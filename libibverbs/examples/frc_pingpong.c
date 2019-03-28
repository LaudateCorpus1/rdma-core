/*
 * Copyright (c) 2005 Topspin Communications.  All rights reserved.
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

#define _GNU_SOURCE
#include <config.h>

#ifndef WITHOUT_ORACLE_EXTENSIONS

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netdb.h>
#include <malloc.h>
#include <getopt.h>
#include <arpa/inet.h>
#include <time.h>
#include <errno.h>

#include "pingpong.h"

enum {
	PINGPONG_RECV_WRID = 1,
	PINGPONG_SEND_WRID = 2,
};

static int page_size;
static int roffset = 0;
static int soffset = 0;
static long mr_calls_failed = 0;

#define MAX_QUEUELEN 500

struct pingpong_context {
	struct ibv_context	*context;
	struct ibv_comp_channel *channel;
	struct ibv_pd		*pd;
	struct ibv_mr		*rmr[MAX_QUEUELEN];
	struct ibv_mr		*smr[MAX_QUEUELEN];
	struct ibv_cq		*cq;
	struct ibv_qp		*qp;
	void			*rbuf;
	void			*sbuf;
	int			 size;
	int			 rx_depth;
	int			 rpending;
	int			 spending;
	struct ibv_port_attr     portinfo;
};

struct pingpong_dest {
	int lid;
	int qpn;
	int psn;
	union ibv_gid gid;
};

static int pp_connect_ctx(struct pingpong_context *ctx, int port, int my_psn,
			  enum ibv_mtu mtu, int sl,
			  struct pingpong_dest *dest, int sgid_idx)
{
	struct ibv_qp_attr attr = {
		.qp_state		= IBV_QPS_RTR,
		.path_mtu		= mtu,
		.dest_qp_num		= dest->qpn,
		.rq_psn			= dest->psn,
		.max_dest_rd_atomic	= 1,
		.min_rnr_timer		= 12,
		.ah_attr		= {
			.is_global	= 0,
			.dlid		= dest->lid,
			.sl		= sl,
			.src_path_bits	= 0,
			.port_num	= port
		}
	};

	if (dest->gid.global.interface_id) {
		attr.ah_attr.is_global = 1;
		attr.ah_attr.grh.hop_limit = 1;
		attr.ah_attr.grh.dgid = dest->gid;
		attr.ah_attr.grh.sgid_index = sgid_idx;
	}
	if (ibv_modify_qp(ctx->qp, &attr,
			  IBV_QP_STATE              |
			  IBV_QP_AV                 |
			  IBV_QP_PATH_MTU           |
			  IBV_QP_DEST_QPN           |
			  IBV_QP_RQ_PSN             |
			  IBV_QP_MAX_DEST_RD_ATOMIC |
			  IBV_QP_MIN_RNR_TIMER)) {
		fprintf(stderr, "Failed to modify QP to RTR\n");
		return 1;
	}

	attr.qp_state	    = IBV_QPS_RTS;
	attr.timeout	    = 14;
	attr.retry_cnt	    = 7;
	attr.rnr_retry	    = 7;
	attr.sq_psn	    = my_psn;
	attr.max_rd_atomic  = 1;
	if (ibv_modify_qp(ctx->qp, &attr,
			  IBV_QP_STATE              |
			  IBV_QP_TIMEOUT            |
			  IBV_QP_RETRY_CNT          |
			  IBV_QP_RNR_RETRY          |
			  IBV_QP_SQ_PSN             |
			  IBV_QP_MAX_QP_RD_ATOMIC)) {
		fprintf(stderr, "Failed to modify QP to RTS\n");
		return 1;
	}

	return 0;
}

static struct pingpong_dest *pp_client_exch_dest(const char *servername, int port,
						 const struct pingpong_dest *my_dest)
{
	struct addrinfo *res, *t;
	struct addrinfo hints = {
		.ai_family   = AF_UNSPEC,
		.ai_socktype = SOCK_STREAM
	};
	char *service;
	char msg[sizeof "0000:000000:000000:00000000000000000000000000000000"];
	int n;
	int sockfd = -1;
	struct pingpong_dest *rem_dest = NULL;
	char gid[33];

	if (asprintf(&service, "%d", port) < 0)
		return NULL;

	n = getaddrinfo(servername, service, &hints, &res);

	if (n < 0) {
		fprintf(stderr, "%s for %s:%d\n", gai_strerror(n), servername, port);
		free(service);
		return NULL;
	}

	for (t = res; t; t = t->ai_next) {
		sockfd = socket(t->ai_family, t->ai_socktype, t->ai_protocol);
		if (sockfd >= 0) {
			if (!connect(sockfd, t->ai_addr, t->ai_addrlen))
				break;
			close(sockfd);
			sockfd = -1;
		}
	}

	freeaddrinfo(res);
	free(service);

	if (sockfd < 0) {
		fprintf(stderr, "Couldn't connect to %s:%d\n", servername, port);
		return NULL;
	}

	gid_to_wire_gid(&my_dest->gid, gid);
	sprintf(msg, "%04x:%06x:%06x:%s", my_dest->lid, my_dest->qpn, my_dest->psn, gid);
	if (write(sockfd, msg, sizeof msg) != sizeof msg) {
		fprintf(stderr, "Couldn't send local address\n");
		goto out;
	}

	if (read(sockfd, msg, sizeof msg) != sizeof msg ||
	    write(sockfd, "done", sizeof "done") != sizeof "done") {
		perror("client read/write");
		fprintf(stderr, "Couldn't read/write remote address\n");
		goto out;
	}

	rem_dest = malloc(sizeof *rem_dest);
	if (!rem_dest)
		goto out;

	sscanf(msg, "%x:%x:%x:%s", &rem_dest->lid, &rem_dest->qpn, &rem_dest->psn, gid);
	wire_gid_to_gid(gid, &rem_dest->gid);

out:
	close(sockfd);
	return rem_dest;
}

static struct pingpong_dest *pp_server_exch_dest(struct pingpong_context *ctx,
						 int ib_port, enum ibv_mtu mtu,
						 int port, int sl,
						 const struct pingpong_dest *my_dest,
						 int sgid_idx)
{
	struct addrinfo *res, *t;
	struct addrinfo hints = {
		.ai_flags    = AI_PASSIVE,
		.ai_family   = AF_UNSPEC,
		.ai_socktype = SOCK_STREAM
	};
	char *service;
	char msg[sizeof "0000:000000:000000:00000000000000000000000000000000"];
	int n;
	int sockfd = -1, connfd;
	struct pingpong_dest *rem_dest = NULL;
	char gid[33];

	if (asprintf(&service, "%d", port) < 0)
		return NULL;

	n = getaddrinfo(NULL, service, &hints, &res);

	if (n < 0) {
		fprintf(stderr, "%s for port %d\n", gai_strerror(n), port);
		free(service);
		return NULL;
	}

	for (t = res; t; t = t->ai_next) {
		sockfd = socket(t->ai_family, t->ai_socktype, t->ai_protocol);
		if (sockfd >= 0) {
			n = 1;

			setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &n, sizeof n);

			if (!bind(sockfd, t->ai_addr, t->ai_addrlen))
				break;
			close(sockfd);
			sockfd = -1;
		}
	}

	freeaddrinfo(res);
	free(service);

	if (sockfd < 0) {
		fprintf(stderr, "Couldn't listen to port %d\n", port);
		return NULL;
	}

	listen(sockfd, 1);
	connfd = accept(sockfd, NULL, 0);
	close(sockfd);
	if (connfd < 0) {
		fprintf(stderr, "accept() failed\n");
		return NULL;
	}

	n = read(connfd, msg, sizeof msg);
	if (n != sizeof msg) {
		perror("server read");
		fprintf(stderr, "%d/%d: Couldn't read remote address\n", n, (int) sizeof msg);
		goto out;
	}

	rem_dest = malloc(sizeof *rem_dest);
	if (!rem_dest)
		goto out;

	sscanf(msg, "%x:%x:%x:%s", &rem_dest->lid, &rem_dest->qpn, &rem_dest->psn, gid);
	wire_gid_to_gid(gid, &rem_dest->gid);

	if (pp_connect_ctx(ctx, ib_port, my_dest->psn, mtu, sl, rem_dest, sgid_idx)) {
		fprintf(stderr, "Couldn't connect to remote QP\n");
		free(rem_dest);
		rem_dest = NULL;
		goto out;
	}


	gid_to_wire_gid(&my_dest->gid, gid);
	sprintf(msg, "%04x:%06x:%06x:%s", my_dest->lid, my_dest->qpn, my_dest->psn, gid);
	if (write(connfd, msg, sizeof msg) != sizeof msg ||
	    read(connfd, msg, sizeof msg) != sizeof "done") {
		fprintf(stderr, "Couldn't send/recv local address\n");
		free(rem_dest);
		rem_dest = NULL;
		goto out;
	}

out:
	close(connfd);
	return rem_dest;
}

static struct pingpong_context *pp_init_ctx(struct ibv_device *ib_dev, int size,
					    int rx_depth, int port,
					    int use_event, int is_server)
{
	struct pingpong_context *ctx;

	ctx = calloc(1, sizeof *ctx);
	if (!ctx)
		return NULL;

	ctx->size     = size;
	ctx->rx_depth = rx_depth;

	ctx->rbuf = memalign(page_size, size * MAX_QUEUELEN);
	ctx->sbuf = memalign(page_size, size * MAX_QUEUELEN);
	if (!ctx->rbuf || !ctx->sbuf) {
		fprintf(stderr, "Couldn't allocate work buf.\n");
		goto clean_ctx;
	}

	memset(ctx->sbuf, 0x7b + is_server, size * 2);
	memset(ctx->sbuf + size*2, 0xcc + is_server, size * 2);
	((char*)ctx->sbuf)[ctx->size * 4 + 1] = (char)0xab;

	ctx->context = ibv_open_device(ib_dev);
	if (!ctx->context) {
		fprintf(stderr, "Couldn't get context for %s\n",
			ibv_get_device_name(ib_dev));
		goto clean_ctx;
	}

	if (use_event) {
		ctx->channel = ibv_create_comp_channel(ctx->context);
		if (!ctx->channel) {
			fprintf(stderr, "Couldn't create completion channel\n");
			goto clean_device;
		}
	}

	ctx->pd = ibv_alloc_pd(ctx->context);
	if (!ctx->pd) {
		fprintf(stderr, "Couldn't allocate PD\n");
		goto clean_comp_channel;
	}

s_retry:
	ctx->smr[0] = ibv_reg_mr_relaxed(ctx->pd, ctx->sbuf, size,
						IBV_ACCESS_LOCAL_WRITE);
	if (!ctx->smr[0]) {
		mr_calls_failed++;
		if (errno == EAGAIN) {
			usleep(1);
			goto s_retry;
		}
		fprintf(stderr, "Couldn't register MR\n");
		goto clean_pd;
	}
	printf("fmr:lkey = %x, rkey = %x for start=%p, len = %d, access = %x\n",
		ctx->smr[0]->lkey, ctx->smr[0]->rkey, ctx->sbuf, size,
		IBV_ACCESS_LOCAL_WRITE);

retry:
	ctx->rmr[0] = ibv_reg_mr_relaxed(ctx->pd, ctx->rbuf, size,
					 IBV_ACCESS_LOCAL_WRITE);
	if (!ctx->rmr[0]) {
		mr_calls_failed++;
		if (errno == EAGAIN) {
			usleep(1);
			goto retry;
		}
		fprintf(stderr, "Couldn't register MR\n");
		goto clean_mrs;
	}
	printf("fmr:lkey = %x, rkey = %x for start=%p, len = %d, access = %x\n",
		ctx->rmr[0]->lkey, ctx->rmr[0]->rkey, ctx->rbuf, size,
		IBV_ACCESS_LOCAL_WRITE);

	ctx->cq = ibv_create_cq(ctx->context, rx_depth * 2 + 1, NULL,
				ctx->channel, 0);
	if (!ctx->cq) {
		fprintf(stderr, "Couldn't create CQ\n");
		goto clean_mrs;
	}

	{
		struct ibv_qp_init_attr attr = {
			.send_cq = ctx->cq,
			.recv_cq = ctx->cq,
			.cap     = {
				.max_send_wr  = rx_depth,
				.max_recv_wr  = rx_depth,
				.max_send_sge = 1,
				.max_recv_sge = 1
			},
			.qp_type = IBV_QPT_RC
		};

		ctx->qp = ibv_create_qp(ctx->pd, &attr);
		if (!ctx->qp)  {
			fprintf(stderr, "Couldn't create QP\n");
			goto clean_cq;
		}
	}

	{
		struct ibv_qp_attr attr = {
			.qp_state        = IBV_QPS_INIT,
			.pkey_index      = 0,
			.port_num        = port,
			.qp_access_flags = 0
		};

		if (ibv_modify_qp(ctx->qp, &attr,
				  IBV_QP_STATE              |
				  IBV_QP_PKEY_INDEX         |
				  IBV_QP_PORT               |
				  IBV_QP_ACCESS_FLAGS)) {
			fprintf(stderr, "Failed to modify QP to INIT\n");
			goto clean_qp;
		}
	}

	return ctx;

clean_qp:
	ibv_destroy_qp(ctx->qp);

clean_cq:
	ibv_destroy_cq(ctx->cq);

clean_mrs:
	if (ctx->rmr[0])
		ibv_dereg_mr_relaxed(ctx->rmr[0]);
	if (ctx->smr[0])
		ibv_dereg_mr_relaxed(ctx->smr[0]);

clean_pd:
	ibv_dealloc_pd(ctx->pd);

clean_comp_channel:
	if (ctx->channel)
		ibv_destroy_comp_channel(ctx->channel);

clean_device:
	ibv_close_device(ctx->context);

clean_ctx:
	free(ctx->rbuf);
	free(ctx->sbuf);
	free(ctx);

	return NULL;
}

static int pp_close_ctx(struct pingpong_context *ctx)
{
	int i = 0;
	if (ibv_destroy_qp(ctx->qp)) {
		fprintf(stderr, "Couldn't destroy QP\n");
		return 1;
	}

	if (ibv_destroy_cq(ctx->cq)) {
		fprintf(stderr, "Couldn't destroy CQ\n");
		return 1;
	}

	for (i = 0; i < MAX_QUEUELEN; i++) {
		if (ctx->smr[i] && ibv_dereg_mr_relaxed(ctx->smr[i])) {
			fprintf(stderr, "Couldn't deregister MR\n");
			return 1;
		}
		if (ctx->rmr[i] && ibv_dereg_mr_relaxed(ctx->rmr[i])) {
			fprintf(stderr, "Couldn't deregister MR\n");
			return 1;
		}
	}

	if (ibv_dealloc_pd(ctx->pd)) {
		fprintf(stderr, "Couldn't deallocate PD\n");
		return 1;
	}

	if (ctx->channel) {
		if (ibv_destroy_comp_channel(ctx->channel)) {
			fprintf(stderr, "Couldn't destroy completion channel\n");
			return 1;
		}
	}

	if (ibv_close_device(ctx->context)) {
		fprintf(stderr, "Couldn't release context\n");
		return 1;
	}

	if (*(char*)ctx->rbuf == 0x7b || *(char*)ctx->rbuf == 0x7c) {
		char is_server = *(char*)ctx->rbuf - (char)0x7b;
		char *buf1 = ctx->rbuf;
		char *buf2 = ctx->rbuf + 2 * ctx->size;
		for (i = 0 ; i < ctx->size * 2; i++) {
			if (buf1[i] != (0x7b + is_server)) {
				fprintf(stderr, "Data corruption  at %d - %x\n", i, buf1[i]);
				break;
			}
			if ((char)buf2[i] != (char)(0xcc + is_server)) {
				fprintf(stderr, "Data corruption  at %d - %x\n", 2 * ctx->size + i, buf2[i]);
				break;
			}
		}
	}

	if ((char)((char*)ctx->rbuf)[ctx->size * 4 + 1] != (char)0xab)
		fprintf(stderr, "Data corruption  at %d - %x\n", ctx->size * 4 + 1, (char)((char*)ctx->rbuf)[ctx->size * 4 + 1]);

	free(ctx->rbuf);
	free(ctx->sbuf);
	free(ctx);

	return 0;
}

static int pp_post_recv(struct pingpong_context *ctx, int n)
{

	if (ctx->rmr[roffset] && ibv_dereg_mr_relaxed(ctx->rmr[roffset])) {
		fprintf(stderr, "Couldn't unregister MT\n");
		return -1;
	}
retry:
	ctx->rmr[roffset]= ibv_reg_mr_relaxed(ctx->pd, ctx->rbuf + roffset*ctx->size,
						ctx->size, IBV_ACCESS_LOCAL_WRITE);
	if (!ctx->rmr[roffset]) {
		mr_calls_failed++;
		if (errno == EAGAIN) {
			usleep(1);
			goto retry;
		}
		fprintf(stderr, "Couldn't register MR\n");
		return -1;
	}
	{
		struct ibv_sge list = {
			.addr	= (uintptr_t) ctx->rbuf + roffset * ctx->size,
			.length = ctx->size,
			.lkey	= ctx->rmr[roffset]->lkey
		};
		struct ibv_recv_wr wr = {
			.wr_id	    = PINGPONG_RECV_WRID,
			.sg_list    = &list,
			.num_sge    = 1,
		};
		struct ibv_recv_wr *bad_wr;
		int i;

		roffset++;
		if (roffset >= MAX_QUEUELEN)
			roffset = 0;

		for (i = 0; i < n; ++i)
			if (ibv_post_recv(ctx->qp, &wr, &bad_wr))
				break;

		return i;
	}
}

static int pp_post_send(struct pingpong_context *ctx)
{
	if (ctx->smr[soffset] && ibv_dereg_mr_relaxed(ctx->smr[soffset])) {
		fprintf(stderr, "Couldn't unregister MT\n");
		return -1;
	}
retry:
	ctx->smr[soffset] = ibv_reg_mr_relaxed(ctx->pd, ctx->sbuf + soffset * ctx->size,
						ctx->size, IBV_ACCESS_LOCAL_WRITE);
	if (!ctx->smr[soffset]) {
		mr_calls_failed++;
		if (errno == EAGAIN) {
			usleep(1);
			goto retry;
		}
		fprintf(stderr, "Couldn't register MR\n");
		return -1;
	}

	{
		struct ibv_sge list = {
			.addr	= (uintptr_t) ctx->sbuf + soffset * ctx->size,
			.length = ctx->size,
			.lkey	= ctx->smr[soffset]->lkey
		};
		struct ibv_send_wr wr = {
			.wr_id	    = PINGPONG_SEND_WRID,
			.sg_list    = &list,
			.num_sge    = 1,
			.opcode     = IBV_WR_SEND,
			.send_flags = IBV_SEND_SIGNALED,
		};
		struct ibv_send_wr *bad_wr;

		soffset++;
		if (soffset >= MAX_QUEUELEN)
			soffset = 0;

		return ibv_post_send(ctx->qp, &wr, &bad_wr);
	}
}

static void usage(const char *argv0)
{
	printf("Usage:\n");
	printf("  %s            start a server and wait for connection\n", argv0);
	printf("  %s <host>     connect to server at <host>\n", argv0);
	printf("\n");
	printf("Options:\n");
	printf("  -p, --port=<port>      listen on/connect to port <port> (default 18515)\n");
	printf("  -d, --ib-dev=<dev>     use IB device <dev> (default first device found)\n");
	printf("  -i, --ib-port=<port>   use port <port> of IB device (default 1)\n");
	printf("  -s, --size=<size>      size of message to exchange (default 4096)\n");
	printf("  -m, --mtu=<size>       path MTU (default 1024)\n");
	printf("  -r, --rx-depth=<dep>   number of receives to post at a time (default 500)\n");
	printf("  -n, --iters=<iters>    number of exchanges (default 1000)\n");
	printf("  -l, --sl=<sl>          service level value\n");
	printf("  -e, --events           sleep on CQ events (default poll)\n");
	printf("  -g, --gid-idx=<gid index> local port gid index\n");
}

int main(int argc, char *argv[])
{
	struct ibv_device      **dev_list;
	struct ibv_device	*ib_dev;
	struct pingpong_context *ctx;
	struct pingpong_dest     my_dest;
	struct pingpong_dest    *rem_dest;
	struct timeval           start, end;
	char                    *ib_devname = NULL;
	char                    *servername = NULL;
	int                      port = 18515;
	int                      ib_port = 1;
	int                      size = 4096;
	enum ibv_mtu		 mtu = IBV_MTU_1024;
	int                      rx_depth = 200;
	int                      iters = 1000;
	int                      use_event = 0;
	int                      routs = 0;
	int                      rcnt, scnt;
	int                      num_cq_events = 0;
	int                      sl = 0;
	int			 gidx = -1;
	char			 gid[33];

	srand48(getpid() * time(NULL));

	while (1) {
		int c;

		static struct option long_options[] = {
			{ .name = "port",     .has_arg = 1, .val = 'p' },
			{ .name = "ib-dev",   .has_arg = 1, .val = 'd' },
			{ .name = "ib-port",  .has_arg = 1, .val = 'i' },
			{ .name = "size",     .has_arg = 1, .val = 's' },
			{ .name = "mtu",      .has_arg = 1, .val = 'm' },
			{ .name = "rx-depth", .has_arg = 1, .val = 'r' },
			{ .name = "iters",    .has_arg = 1, .val = 'n' },
			{ .name = "sl",       .has_arg = 1, .val = 'l' },
			{ .name = "events",   .has_arg = 0, .val = 'e' },
			{ .name = "gid-idx",  .has_arg = 1, .val = 'g' },
			{ 0 }
		};

		c = getopt_long(argc, argv, "p:d:i:s:m:r:n:l:eg:", long_options, NULL);
		if (c == -1)
			break;

		switch (c) {
		case 'p':
			port = strtol(optarg, NULL, 0);
			if (port < 0 || port > 65535) {
				usage(argv[0]);
				return 1;
			}
			break;

		case 'd':
			ib_devname = strdupa(optarg);
			break;

		case 'i':
			ib_port = strtol(optarg, NULL, 0);
			if (ib_port < 0) {
				usage(argv[0]);
				return 1;
			}
			break;

		case 's':
			size = strtol(optarg, NULL, 0);
			break;

		case 'm':
			mtu = pp_mtu_to_enum(strtol(optarg, NULL, 0));
			if (mtu < 0) {
				usage(argv[0]);
				return 1;
			}
			break;

		case 'r':
			rx_depth = strtol(optarg, NULL, 0);
			break;

		case 'n':
			iters = strtol(optarg, NULL, 0);
			break;

		case 'l':
			sl = strtol(optarg, NULL, 0);
			break;

		case 'e':
			++use_event;
			break;

		case 'g':
			gidx = strtol(optarg, NULL, 0);
			break;

		default:
			usage(argv[0]);
			return 1;
		}
	}

	if (optind == argc - 1)
		servername = strdupa(argv[optind]);
	else if (optind < argc) {
		usage(argv[0]);
		return 1;
	}

	page_size = sysconf(_SC_PAGESIZE);

	dev_list = ibv_get_device_list(NULL);
	if (!dev_list) {
		perror("Failed to get IB devices list");
		return 1;
	}

	if (!ib_devname) {
		ib_dev = *dev_list;
		if (!ib_dev) {
			fprintf(stderr, "No IB devices found\n");
			return 1;
		}
	} else {
		int i;
		for (i = 0; dev_list[i]; ++i)
			if (!strcmp(ibv_get_device_name(dev_list[i]), ib_devname))
				break;
		ib_dev = dev_list[i];
		if (!ib_dev) {
			fprintf(stderr, "IB device %s not found\n", ib_devname);
			return 1;
		}
	}

	ctx = pp_init_ctx(ib_dev, size, rx_depth, ib_port, use_event, !servername);
	if (!ctx)
		return 1;

	{
		int i = 0;
		for (i = 0; i < ctx->rx_depth; i++) {
			routs += pp_post_recv(ctx, 1);
		}
	}
	if (routs < ctx->rx_depth) {
		fprintf(stderr, "Couldn't post receive (%d)\n", routs);
		return 1;
	}

	if (use_event)
		if (ibv_req_notify_cq(ctx->cq, 0)) {
			fprintf(stderr, "Couldn't request CQ notification\n");
			return 1;
		}


	if (pp_get_port_info(ctx->context, ib_port, &ctx->portinfo)) {
		fprintf(stderr, "Couldn't get port info\n");
		return 1;
	}

	my_dest.lid = ctx->portinfo.lid;
	if (ctx->portinfo.link_layer == IBV_LINK_LAYER_INFINIBAND && !my_dest.lid) {
		fprintf(stderr, "Couldn't get local LID\n");
		return 1;
	}

	if (gidx >= 0) {
		if (ibv_query_gid(ctx->context, ib_port, gidx, &my_dest.gid)) {
			fprintf(stderr, "Could not get local gid for gid index %d\n", gidx);
			return 1;
		}
	} else
		memset(&my_dest.gid, 0, sizeof my_dest.gid);

	my_dest.qpn = ctx->qp->qp_num;
	my_dest.psn = lrand48() & 0xffffff;
	inet_ntop(AF_INET6, &my_dest.gid, gid, sizeof gid);
	printf("  local address:  LID 0x%04x, QPN 0x%06x, PSN 0x%06x, GID %s\n",
	       my_dest.lid, my_dest.qpn, my_dest.psn, gid);


	if (servername)
		rem_dest = pp_client_exch_dest(servername, port, &my_dest);
	else
		rem_dest = pp_server_exch_dest(ctx, ib_port, mtu, port, sl, &my_dest, gidx);

	if (!rem_dest)
		return 1;

	inet_ntop(AF_INET6, &rem_dest->gid, gid, sizeof gid);
	printf("  remote address: LID 0x%04x, QPN 0x%06x, PSN 0x%06x, GID %s\n",
	       rem_dest->lid, rem_dest->qpn, rem_dest->psn, gid);

	if (servername)
		if (pp_connect_ctx(ctx, ib_port, my_dest.psn, mtu, sl, rem_dest, gidx))
			return 1;

	ctx->rpending = ctx->rx_depth;

	if (servername) {
		while (ctx->spending < ctx->rx_depth) {
			ctx->spending++;
			if (pp_post_send(ctx)) {
				fprintf(stderr, "Couldn't post send\n");
				return 1;
			}
		}
	}

	if (gettimeofday(&start, NULL)) {
		perror("gettimeofday");
		return 1;
	}

	rcnt = scnt = 0;
	while (rcnt < iters || scnt < iters) {
		if (use_event) {
			struct ibv_cq *ev_cq;
			void          *ev_ctx;

			if (ibv_get_cq_event(ctx->channel, &ev_cq, &ev_ctx)) {
				fprintf(stderr, "Failed to get cq_event\n");
				return 1;
			}

			++num_cq_events;

			if (ev_cq != ctx->cq) {
				fprintf(stderr, "CQ event for unknown CQ %p\n", ev_cq);
				return 1;
			}

			if (ibv_req_notify_cq(ctx->cq, 0)) {
				fprintf(stderr, "Couldn't request CQ notification\n");
				return 1;
			}
		}

		{
			struct ibv_wc wc[100];
			int ne, i;

			do {
				ne = ibv_poll_cq(ctx->cq, 100, wc);
				if (ne < 0) {
					fprintf(stderr, "poll CQ failed %d\n", ne);
					return 1;
				}

			} while (!use_event && ne < 1);

			for (i = 0; i < ne; ++i) {
				if (wc[i].status != IBV_WC_SUCCESS) {
					fprintf(stderr, "Failed status %s (%d[%d]) for wr_id %d(scnt %d, rcnt %d, i %d)\n",
						ibv_wc_status_str(wc[i].status),
						wc[i].status,wc[i].vendor_err, (int) wc[i].wr_id, scnt, rcnt, i);
					return 1;
				}

				switch ((int) wc[i].wr_id) {
					case PINGPONG_SEND_WRID:
						ctx->spending--;
						++scnt;
						break;

					case PINGPONG_RECV_WRID:
						ctx->rpending--;
						--routs ;
						routs += pp_post_recv(ctx, 1);
						if (routs < ctx->rx_depth) {
							fprintf(stderr,
									"Couldn't post receive (%d)\n",
									routs);
							return 1;
						}
						ctx->rpending++;

						++rcnt;
						break;

					default:
						fprintf(stderr, "Completion for unknown wr_id %d\n",
								(int) wc[i].wr_id);
						return 1;
				}

				if ((ctx->spending + scnt) < iters) {
					int j =0;
					int count = iters - (ctx->spending + scnt);
					count = (count > (ctx->rx_depth - ctx->spending)) ?
						 ctx->rx_depth - ctx->spending  : count;
					for (j = 0; j < count; j++) {
						if (pp_post_send(ctx)) {
							fprintf(stderr, "Couldn't post send %d, count %d\n", i, count);
							return 1;
						}
					}
					ctx->spending  += count;
				}
			}
		}
	}

	if (gettimeofday(&end, NULL)) {
		perror("gettimeofday");
		return 1;
	}

	{
		float usec = (end.tv_sec - start.tv_sec) * 1000000 +
			(end.tv_usec - start.tv_usec);
		long long bytes = (long long) size * iters * 2;

		printf("%lld bytes in %.2f seconds = %.2f Mbit/sec\n",
		       bytes, usec / 1000000., bytes * 8. / usec);
		printf("%d iters in %.2f seconds = %.2f usec/iter\n",
		       iters, usec / 1000000., usec / iters);
	}
	printf(" %ld reg_mrs failed\n", mr_calls_failed);

	ibv_ack_cq_events(ctx->cq, num_cq_events);

	if (pp_close_ctx(ctx))
		return 1;

	ibv_free_device_list(dev_list);
	free(rem_dest);

	return 0;
}

#else /* WITHOUT_ORACLE_EXTENSIONS */

#include <stdio.h>

int main(int argc, char *argv[])
{
	fprintf(stderr, "%s is not supported when compiled without Oracle extensions.\n", argv[0]);
	return 1;
}

#endif /* WITHOUT_ORACLE_EXTENSIONS */
