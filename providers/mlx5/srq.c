/*
 * Copyright (c) 2012 Mellanox Technologies, Inc.  All rights reserved.
 *
 * This software is available to you under a choice of one of two
 * licenses.  You may choose to be licensed under the terms of the GNU
 * General Public License (GPL) Version 2, available from the file
 * COPYING in the main directory of this source tree, or the
 * OpenIB.org BSD license below:
 *
 *     Redistribution and use in source and binary forms, with or
 *     without modification, are permitted provided that the following
 *     conditions are met:
 *
 *      - Redistributions of source code must retain the above
 *        copyright notice, this list of conditions and the following
 *        disclaimer.
 *
 *      - Redistributions in binary form must reproduce the above
 *        copyright notice, this list of conditions and the following
 *        disclaimer in the documentation and/or other materials
 *        provided with the distribution.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

#include <config.h>

#include <stdlib.h>
#include <pthread.h>
#include <string.h>
#include <errno.h>

#include "mlx5.h"
#include "wqe.h"

static void *get_wqe(struct mlx5_srq *srq, int n)
{
	return srq->buf.buf + (n << srq->wqe_shift);
}

int mlx5_copy_to_recv_srq(struct mlx5_srq *srq, int idx, void *buf, int size)
{
	struct mlx5_wqe_srq_next_seg *next;
	struct mlx5_wqe_data_seg *scat;
	int copy;
	int i;
	int max = 1 << (srq->wqe_shift - 4);

	next = get_wqe(srq, idx);
	scat = (struct mlx5_wqe_data_seg *) (next + 1);

	for (i = 0; i < max; ++i) {
		copy = min_t(long, size, be32toh(scat->byte_count));
		memcpy((void *)(unsigned long)be64toh(scat->addr), buf, copy);
		size -= copy;
		if (size <= 0)
			return IBV_WC_SUCCESS;

		buf += copy;
		++scat;
	}
	return IBV_WC_LOC_LEN_ERR;
}

void mlx5_free_srq_wqe(struct mlx5_srq *srq, int ind)
{
	struct mlx5_wqe_srq_next_seg *next;

	mlx5_spin_lock(&srq->lock);

	next = get_wqe(srq, srq->tail);
	next->next_wqe_index = htobe16(ind);
	srq->tail = ind;

	mlx5_spin_unlock(&srq->lock);
}

int mlx5_post_srq_recv(struct ibv_srq *ibsrq,
		       struct ibv_recv_wr *wr,
		       struct ibv_recv_wr **bad_wr)
{
#ifndef WITHOUT_ORACLE_EXTENSIONS
	struct mlx5_srq *srq;
#else
	struct mlx5_srq *srq = to_msrq(ibsrq);
#endif /* !WITHOUT_ORACLE_EXTENSIONS */
	struct mlx5_wqe_srq_next_seg *next;
	struct mlx5_wqe_data_seg *scat;
	int err = 0;
	int nreq;
	int i;

#ifndef WITHOUT_ORACLE_EXTENSIONS
	if (ibsrq->handle == LEGACY_XRC_SRQ_HANDLE)
		ibsrq = (struct ibv_srq *)(((struct ibv_srq_legacy *) ibsrq)->ibv_srq);
	srq = to_msrq(ibsrq);
#endif /* !WITHOUT_ORACLE_EXTENSIONS */

	mlx5_spin_lock(&srq->lock);

	for (nreq = 0; wr; ++nreq, wr = wr->next) {
		if (wr->num_sge > srq->max_gs) {
			err = EINVAL;
			*bad_wr = wr;
			break;
		}

		if (srq->head == srq->tail) {
			/* SRQ is full*/
			err = ENOMEM;
			*bad_wr = wr;
			break;
		}

		srq->wrid[srq->head] = wr->wr_id;

		next      = get_wqe(srq, srq->head);
		srq->head = be16toh(next->next_wqe_index);
		scat      = (struct mlx5_wqe_data_seg *) (next + 1);

		for (i = 0; i < wr->num_sge; ++i) {
			scat[i].byte_count = htobe32(wr->sg_list[i].length);
			scat[i].lkey       = htobe32(wr->sg_list[i].lkey);
			scat[i].addr       = htobe64(wr->sg_list[i].addr);
		}

		if (i < srq->max_gs) {
			scat[i].byte_count = 0;
			scat[i].lkey       = htobe32(MLX5_INVALID_LKEY);
			scat[i].addr       = 0;
		}
	}

	if (nreq) {
		srq->counter += nreq;

		/*
		 * Make sure that descriptors are written before
		 * we write doorbell record.
		 */
		udma_to_device_barrier();

		*srq->db = htobe32(srq->counter);
	}

	mlx5_spin_unlock(&srq->lock);

	return err;
}

/* Build a linked list on an array of SRQ WQEs.
 * Since WQEs are always added to the tail and taken from the head
 * it doesn't matter where the last WQE points to.
 */
static void set_srq_buf_ll(struct mlx5_srq *srq, int start, int end)
{
	struct mlx5_wqe_srq_next_seg *next;
	int i;

	for (i = start; i < end; ++i) {
		next = get_wqe(srq, i);
		next->next_wqe_index = htobe16(i + 1);
	}
}

int mlx5_alloc_srq_buf(struct ibv_context *context, struct mlx5_srq *srq,
		       uint32_t max_wr)
{
	int size;
	int buf_size;
	struct mlx5_context	   *ctx;
	uint32_t orig_max_wr = max_wr;
	bool have_wq = true;

	ctx = to_mctx(context);

	if (srq->max_gs < 0) {
		errno = EINVAL;
		return -1;
	}

	/* At first, try to allocate more WQEs than requested so the extra will
	 * be used for the wait queue.
	 */
	max_wr = orig_max_wr * 2 + 1;

	if (max_wr > ctx->max_srq_recv_wr) {
		/* Device limits are smaller than required
		 * to provide a wait queue, continue without.
		 */
		max_wr = orig_max_wr + 1;
		have_wq = false;
	}

	size = sizeof(struct mlx5_wqe_srq_next_seg) +
		srq->max_gs * sizeof(struct mlx5_wqe_data_seg);
	size = max(32, size);

	size = mlx5_round_up_power_of_two(size);

	if (size > ctx->max_recv_wr) {
		errno = EINVAL;
		return -1;
	}
	srq->max_gs = (size - sizeof(struct mlx5_wqe_srq_next_seg)) /
		sizeof(struct mlx5_wqe_data_seg);

	srq->wqe_shift = mlx5_ilog2(size);

	srq->max = align_queue_size(max_wr);
	buf_size = srq->max * size;

	if (mlx5_alloc_buf(&srq->buf, buf_size,
			   to_mdev(context->device)->page_size))
		return -1;

	memset(srq->buf.buf, 0, buf_size);
	srq->head = 0;
	srq->tail = align_queue_size(orig_max_wr + 1) - 1;
	if (have_wq)  {
		srq->waitq_head = srq->tail + 1;
		srq->waitq_tail = srq->max - 1;
	} else {
		srq->waitq_head = -1;
		srq->waitq_tail = -1;
	}

	srq->wrid = malloc(srq->max * sizeof(*srq->wrid));
	if (!srq->wrid) {
		mlx5_free_buf(&srq->buf);
		return -1;
	}

	/*
	 * Now initialize the SRQ buffer so that all of the WQEs are
	 * linked into the list of free WQEs.
	 */

	set_srq_buf_ll(srq, srq->head, srq->tail);
	if (have_wq)
		set_srq_buf_ll(srq, srq->waitq_head, srq->waitq_tail);

	return 0;
}

struct mlx5_srq *mlx5_find_srq(struct mlx5_context *ctx, uint32_t srqn)
{
	int tind = srqn >> MLX5_SRQ_TABLE_SHIFT;

	if (ctx->srq_table[tind].refcnt)
		return ctx->srq_table[tind].table[srqn & MLX5_SRQ_TABLE_MASK];
	else
		return NULL;
}

int mlx5_store_srq(struct mlx5_context *ctx, uint32_t srqn,
		   struct mlx5_srq *srq)
{
	int tind = srqn >> MLX5_SRQ_TABLE_SHIFT;

	if (!ctx->srq_table[tind].refcnt) {
		ctx->srq_table[tind].table = calloc(MLX5_SRQ_TABLE_MASK + 1,
						   sizeof(struct mlx5_srq *));
		if (!ctx->srq_table[tind].table)
			return -1;
	}

	++ctx->srq_table[tind].refcnt;
	ctx->srq_table[tind].table[srqn & MLX5_SRQ_TABLE_MASK] = srq;

	return 0;
}

void mlx5_clear_srq(struct mlx5_context *ctx, uint32_t srqn)
{
	int tind = srqn >> MLX5_SRQ_TABLE_SHIFT;

	if (!--ctx->srq_table[tind].refcnt)
		free(ctx->srq_table[tind].table);
	else
		ctx->srq_table[tind].table[srqn & MLX5_SRQ_TABLE_MASK] = NULL;
}
