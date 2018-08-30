%define uek2epoch 2
%define uek4epoch 4
%define uek5epoch 5

%global flavor vos

Name: rdma-core
Epoch: %{uek5epoch} 
Version: 17.1
Release: 1.0.4%{?dist}%{?flavor}
Summary: RDMA core userspace libraries and daemons (Oracle VOS)

# Almost everything is licensed under the OFA dual GPLv2, 2 Clause BSD license
#  providers/ipathverbs/ Dual licensed using a BSD license with an extra patent clause
#  providers/rxe/ Incorporates code from ipathverbs and contains the patent clause
#  providers/hfi1verbs Uses the 3 Clause BSD license
License: GPLv2 or BSD
Url: https://github.com/linux-rdma/rdma-core
Source: rdma-core-%{version}.tgz

BuildRequires: binutils
BuildRequires: cmake >= 2.8.11
BuildRequires: gcc
BuildRequires: libudev-devel
BuildRequires: pkgconfig
BuildRequires: pkgconfig(libnl-3.0)
BuildRequires: pkgconfig(libnl-route-3.0)
BuildRequires: valgrind-devel
BuildRequires: systemd
BuildRequires: systemd-devel
BuildRequires: python

Requires: dracut, kmod, systemd

# Set minimum kernel version for Oracle UEK5
Requires: kernel-uek >= 4.14.14-11

# Oracle previously shipped oracle/ as a stand-alone
# package called 'rdma', which we're supplanting here.
Provides: rdma = %{uek5epoch}:%{version}-%{release}
#Obsoletes: rdma < %{uek5epoch}:%{version}-%{release}
Conflicts: infiniband-diags <= 1.6.7

# Since we recommend developers use Ninja, so should packagers, for consistency.
# Oracle Linux 7 does not ship Ninja so the build system must be configured to
# enable the EPEL repo.
%define CMAKE_FLAGS %{nil}
BuildRequires: ninja-build
%define CMAKE_FLAGS -GNinja
%define make_jobs ninja-build -v %{?_smp_mflags}
%define cmake_install DESTDIR=%{buildroot} ninja-build install

%description
RDMA core userspace infrastructure and documentation, including initialization
scripts, kernel driver-specific modprobe override configs, IPoIB network
scripts, dracut rules, and the rdma-ndd utility.

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%package devel
Summary: RDMA core development libraries and headers
Requires: %{name}%{?_isa} = %{uek5epoch}:%{version}-%{release}
Requires: libibverbs = %{uek5epoch}:%{version}-%{release}
Provides: libibverbs-devel = %{uek5epoch}:%{version}-%{release}
#Obsoletes: libibverbs-devel < %{uek5epoch}:%{version}-%{release}
Requires: libibumad = %{uek5epoch}:%{version}-%{release}
Provides: libibumad-devel = %{uek5epoch}:%{version}-%{release}
#Obsoletes: libibumad-devel < %{uek5epoch}:%{version}-%{release}
Requires: librdmacm = %{uek5epoch}:%{version}-%{release}
Provides: librdmacm-devel = %{uek5epoch}:%{version}-%{release}
#Obsoletes: librdmacm-devel < %{uek5epoch}:%{version}-%{release}
Requires: ibacm = %{uek5epoch}:%{version}-%{release}
Provides: ibacm-devel = %{uek5epoch}:%{version}-%{release}
#Obsoletes: ibacm-devel < %{uek5epoch}:%{version}-%{release}

%description devel
RDMA core development libraries and headers.

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%package -n libibverbs
Summary: A library and drivers for direct userspace use of RDMA (InfiniBand/iWARP/RoCE) hardware
Requires(post): /sbin/ldconfig
Requires(postun): /sbin/ldconfig
Requires: %{name}%{?_isa} = %{uek5epoch}:%{version}-%{release}
Provides: libcxgb3 = %{uek5epoch}:%{version}-%{release}
Obsoletes: libcxgb3 < %{uek5epoch}:%{version}-%{release}
Provides: libcxgb4 = %{uek5epoch}:%{version}-%{release}
Obsoletes: libcxgb4 < %{uek5epoch}:%{version}-%{release}
Provides: libhfi1 = %{uek5epoch}:%{version}-%{release}
Obsoletes: libhfi1 < %{uek5epoch}:%{version}-%{release}
Provides: libi40iw = %{uek5epoch}:%{version}-%{release}
Obsoletes: libi40iw < %{uek5epoch}:%{version}-%{release}
Provides: libipathverbs = %{uek5epoch}:%{version}-%{release}
Obsoletes: libipathverbs < %{uek5epoch}:%{version}-%{release}
Provides: libmlx4 = %{uek5epoch}:%{version}-%{release}
#Obsoletes: libmlx4 < %{uek5epoch}:%{version}-%{release}
Provides: libmlx5 = %{uek5epoch}:%{version}-%{release}
#Obsoletes: libmlx5 < %{uek5epoch}:%{version}-%{release}
Provides: libmthca = %{uek5epoch}:%{version}-%{release}
Obsoletes: libmthca < %{uek5epoch}:%{version}-%{release}
Provides: libnes = %{uek5epoch}:%{version}-%{release}
Obsoletes: libnes < %{uek5epoch}:%{version}-%{release}
Provides: libocrdma = %{uek5epoch}:%{version}-%{release}
Obsoletes: libocrdma < %{uek5epoch}:%{version}-%{release}
Provides: librxe = %{uek5epoch}:%{version}-%{release}
Obsoletes: librxe < %{uek5epoch}:%{version}-%{release}

%description -n libibverbs
libibverbs is a library that allows userspace processes to use RDMA
"verbs" as described in the InfiniBand Architecture Specification and
the RDMA Protocol Verbs Specification.  This includes direct hardware
access from userspace to InfiniBand/iWARP adapters (kernel bypass) for
fast path operations.

Device-specific plug-in ibverbs userspace drivers are included:

- libcxgb3: Chelsio T3 iWARP HCA
- libcxgb4: Chelsio T4 iWARP HCA
- libhfi1: Intel Omni-Path HFI
- libhns: HiSilicon Hip06 SoC
- libi40iw: Intel Ethernet Connection X722 RDMA
- libipathverbs: QLogic InfiniPath HCA
- libmlx4: Mellanox ConnectX-3 InfiniBand HCA
- libmlx5: Mellanox Connect-IB/X-4+ InfiniBand HCA
- libmthca: Mellanox InfiniBand HCA
- libnes: NetEffect RNIC
- libocrdma: Emulex OneConnect RDMA/RoCE Device
- libqedr: QLogic QL4xxx RoCE HCA
- librxe: A software implementation of the RoCE protocol
- libvmw_pvrdma: VMware paravirtual RDMA device

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%package -n libibverbs-utils
Summary: Examples for the libibverbs library
Requires: libibverbs%{?_isa} = %{uek5epoch}:%{version}-%{release}

%description -n libibverbs-utils
Useful libibverbs example programs such as ibv_devinfo, which
displays information about RDMA devices.

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%package -n ibacm
Summary: InfiniBand Communication Manager Assistant
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
Requires: %{name}%{?_isa} = %{uek5epoch}:%{version}-%{release}

%description -n ibacm
The ibacm daemon helps reduce the load of managing path record lookups on
large InfiniBand fabrics by providing a user space implementation of what
is functionally similar to an ARP cache.  The use of ibacm, when properly
configured, can reduce the SA packet load of a large IB cluster from O(n^2)
to O(n).  The ibacm daemon is started and normally runs in the background,
user applications need not know about this daemon as long as their app
uses librdmacm to handle connection bring up/tear down.  The librdmacm
library knows how to talk directly to the ibacm daemon to retrieve data.

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%package -n iwpmd
Summary: iWarp Port Mapper userspace daemon
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
Requires: %{name}%{?_isa} = %{uek5epoch}:%{version}-%{release}

%description -n iwpmd
iwpmd provides a userspace service for iWarp drivers to claim
tcp ports through the standard socket interface.

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%package -n libibumad
Summary: OpenFabrics Alliance InfiniBand umad (userspace management datagram) library
Requires: %{name}%{?_isa} = %{uek5epoch}:%{version}-%{release}

%description -n libibumad
libibumad provides the userspace management datagram (umad) library
functions, which sit on top of the umad modules in the kernel. These
are used by the IB diagnostic and management tools, including OpenSM.

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%package -n librdmacm
Summary: Userspace RDMA Connection Manager
Requires: %{name}%{?_isa} = %{uek5epoch}:%{version}-%{release}

%description -n librdmacm
librdmacm provides a userspace RDMA Communication Management API.

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%package -n librdmacm-utils
Summary: Examples for the librdmacm library
Requires: librdmacm%{?_isa} = %{uek5epoch}:%{version}-%{release}

%description -n librdmacm-utils
Example test programs for the librdmacm library.

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%package -n srp_daemon
Summary: Tools for using the InfiniBand SRP protocol devices
Obsoletes: srptools <= 1.0.3
Provides: srptools = %{uek5epoch}:%{version}-%{release}
Obsoletes: openib-srptools <= 0.0.6
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
Requires: %{name}%{?_isa} = %{uek5epoch}:%{version}-%{release}

%description -n srp_daemon
In conjunction with the kernel ib_srp driver, srp_daemon allows you to
discover and use SCSI devices via the SCSI RDMA Protocol over InfiniBand.

For use on Oracle Linux systems running the Oracle Database Virtual OS
(VOS) layer.

%prep
%setup

%build

# New RPM defines _rundir, usually as /run
%if 0%{?_rundir:1}
%else
%define _rundir /var/run
%endif

%{!?EXTRA_CMAKE_FLAGS: %define EXTRA_CMAKE_FLAGS %{nil}}

# Pass all of the rpm paths directly to GNUInstallDirs and our other defines.
%cmake %{CMAKE_FLAGS} \
         -DCMAKE_BUILD_TYPE=Release \
         -DCMAKE_INSTALL_BINDIR:PATH=%{_bindir} \
         -DCMAKE_INSTALL_SBINDIR:PATH=%{_sbindir} \
         -DCMAKE_INSTALL_LIBDIR:PATH=%{_libdir} \
         -DCMAKE_INSTALL_LIBEXECDIR:PATH=%{_libexecdir} \
         -DCMAKE_INSTALL_LOCALSTATEDIR:PATH=%{_localstatedir} \
         -DCMAKE_INSTALL_SHAREDSTATEDIR:PATH=%{_sharedstatedir} \
         -DCMAKE_INSTALL_INCLUDEDIR:PATH=%{_includedir} \
         -DCMAKE_INSTALL_INFODIR:PATH=%{_infodir} \
         -DCMAKE_INSTALL_MANDIR:PATH=%{_mandir} \
         -DCMAKE_INSTALL_SYSCONFDIR:PATH=%{_sysconfdir} \
         -DCMAKE_INSTALL_SYSTEMD_SERVICEDIR:PATH=%{_unitdir} \
         -DCMAKE_INSTALL_INITDDIR:PATH=%{_initrddir} \
         -DCMAKE_INSTALL_RUNDIR:PATH=%{_rundir} \
         -DCMAKE_INSTALL_DOCDIR:PATH=%{_docdir}/%{name}-%{version} \
         -DCMAKE_INSTALL_UDEV_RULESDIR:PATH=%{_udevrulesdir} \
         %{EXTRA_CMAKE_FLAGS}
%make_jobs

%install
%cmake_install

mkdir -p %{buildroot}/%{_sysconfdir}/rdma

# Red Hat specific glue
%global dracutlibdir %{_prefix}/lib/dracut
%global sysmodprobedir %{_prefix}/lib/modprobe.d
mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d
mkdir -p %{buildroot}%{_libexecdir}
mkdir -p %{buildroot}%{_udevrulesdir}
mkdir -p %{buildroot}%{dracutlibdir}/modules.d/05rdma
mkdir -p %{buildroot}%{sysmodprobedir}
install -D -m0644 oracle/rdma.conf %{buildroot}/%{_sysconfdir}/rdma/rdma.conf
install -D -m0644 oracle/rdma.sriov-vfs %{buildroot}/%{_sysconfdir}/rdma/sriov-vfs
install -D -m0644 oracle/rdma.mlx4.conf %{buildroot}/%{_sysconfdir}/rdma/mlx4.conf
install -D -m0644 oracle/rdma.service %{buildroot}%{_unitdir}/rdma.service
install -D -m0755 oracle/rdma.modules-setup.sh %{buildroot}%{dracutlibdir}/modules.d/05rdma/module-setup.sh
install -D -m0644 oracle/rdma.udev-rules %{buildroot}%{_udevrulesdir}/98-rdma.rules
install -D -m0644 oracle/rdma.mlx4.sys.modprobe %{buildroot}%{sysmodprobedir}/libmlx4.conf
install -D -m0755 oracle/rdma.kernel-init %{buildroot}%{_libexecdir}/rdma-init-kernel
install -D -m0755 oracle/rdma.sriov-init %{buildroot}%{_libexecdir}/rdma-set-sriov-vf
install -D -m0755 oracle/rdma.mlx4-setup.sh %{buildroot}%{_libexecdir}/mlx4-setup.sh

# ibacm
bin/ib_acme -D . -O
install -D -m0644 ibacm_opts.cfg %{buildroot}%{_sysconfdir}/rdma/

# Delete the package's init.d scripts
rm -rf %{buildroot}/%{_initrddir}/
rm -rf %{buildroot}/%{_sbindir}/srp_daemon.sh

%post -n libibverbs -p /sbin/ldconfig
%postun -n libibverbs -p /sbin/ldconfig

%post -n libibumad -p /sbin/ldconfig
%postun -n libibumad -p /sbin/ldconfig

%post -n librdmacm -p /sbin/ldconfig
%postun -n librdmacm -p /sbin/ldconfig

%post -n ibacm
%systemd_post ibacm.service
%preun -n ibacm
%systemd_preun ibacm.service
%postun -n ibacm
%systemd_postun_with_restart ibacm.service

%post -n srp_daemon
%systemd_post srp_daemon.service
%preun -n srp_daemon
%systemd_preun srp_daemon.service
%postun -n srp_daemon
%systemd_postun_with_restart srp_daemon.service

%post -n iwpmd
%systemd_post iwpmd.service
%preun -n iwpmd
%systemd_preun iwpmd.service
%postun -n iwpmd
%systemd_postun_with_restart iwpmd.service

%files
%dir %{_sysconfdir}/rdma
%dir %{_docdir}/%{name}-%{version}
%doc %{_docdir}/%{name}-%{version}/README.md
%doc %{_docdir}/%{name}-%{version}/rxe.md
%doc %{_docdir}/%{name}-%{version}/udev.md
%doc %{_docdir}/%{name}-%{version}/tag_matching.md
%config(noreplace) %{_sysconfdir}/rdma/mlx4.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/infiniband.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/iwarp.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/opa.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/rdma.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/roce.conf
%config(noreplace) %{_sysconfdir}/rdma/rdma.conf
%config(noreplace) %{_sysconfdir}/rdma/sriov-vfs
%config(noreplace) %{_sysconfdir}/udev/rules.d/*
%config(noreplace) %{_sysconfdir}/modprobe.d/mlx4.conf
%config(noreplace) %{_sysconfdir}/modprobe.d/truescale.conf
%{_unitdir}/rdma-hw.target
%{_unitdir}/rdma-load-modules@.service
%{_unitdir}/rdma.service
%dir %{dracutlibdir}/modules.d/05rdma
%{dracutlibdir}/modules.d/05rdma/module-setup.sh
%{_udevrulesdir}/60-rdma-ndd.rules
%{_udevrulesdir}/75-rdma-description.rules
%{_udevrulesdir}/90-rdma-hw-modules.rules
%{_udevrulesdir}/90-rdma-ulp-modules.rules
%{_udevrulesdir}/90-rdma-umad.rules
%{_udevrulesdir}/98-rdma.rules
%{sysmodprobedir}/libmlx4.conf
%{_libexecdir}/rdma-init-kernel
%{_libexecdir}/rdma-set-sriov-vf
%{_libexecdir}/mlx4-setup.sh
%{_libexecdir}/truescale-serdes.cmds
%{_bindir}/rxe_cfg
%{_sbindir}/rdma-ndd
%{_unitdir}/rdma-ndd.service
%{_mandir}/man7/rxe*
%{_mandir}/man8/rdma-ndd.*
%{_mandir}/man8/rxe*
%license COPYING.*

%files devel
%doc %{_docdir}/%{name}-%{version}/MAINTAINERS
%dir %{_includedir}/infiniband
%dir %{_includedir}/rdma
%{_includedir}/infiniband/*
%{_includedir}/rdma/*
%{_libdir}/lib*.so
%{_mandir}/man3/ibv_*
%{_mandir}/man3/rdma*
%{_mandir}/man3/umad*
%{_mandir}/man3/*_to_ibv_rate.*
%{_mandir}/man7/rdma_cm.*
%{_mandir}/man3/mlx5dv*
%{_mandir}/man3/mlx4dv*
%{_mandir}/man7/mlx5dv*
%{_mandir}/man7/mlx4dv*

%files -n libibverbs
%dir %{_sysconfdir}/libibverbs.d
%dir %{_libdir}/libibverbs
%{_libdir}/libibverbs*.so.*
%{_libdir}/libibverbs/*.so
%{_libdir}/libmlx5.so.*
%{_libdir}/libmlx4.so.*
%config(noreplace) %{_sysconfdir}/libibverbs.d/*.driver
%doc %{_docdir}/%{name}-%{version}/libibverbs.md

%files -n libibverbs-utils
%{_bindir}/ibv_*
%{_mandir}/man1/ibv_*

%files -n ibacm
%config(noreplace) %{_sysconfdir}/rdma/ibacm_opts.cfg
%{_bindir}/ib_acme
%{_sbindir}/ibacm
%{_mandir}/man1/ibacm.*
%{_mandir}/man1/ib_acme.*
%{_mandir}/man7/ibacm.*
%{_mandir}/man7/ibacm_prov.*
%{_unitdir}/ibacm.service
%{_unitdir}/ibacm.socket
%dir %{_libdir}/ibacm
%{_libdir}/ibacm/*
%doc %{_docdir}/%{name}-%{version}/ibacm.md

%files -n iwpmd
%{_sbindir}/iwpmd
%{_unitdir}/iwpmd.service
%config(noreplace) %{_sysconfdir}/rdma/modules/iwpmd.conf
%config(noreplace) %{_sysconfdir}/iwpmd.conf
%{_udevrulesdir}/90-iwpmd.rules
%{_mandir}/man8/iwpmd.*
%{_mandir}/man5/iwpmd.*

%files -n libibumad
%{_libdir}/libibumad*.so.*

%files -n librdmacm
%{_libdir}/librdmacm*.so.*
%dir %{_libdir}/rsocket
%{_libdir}/rsocket/*.so*
%doc %{_docdir}/%{name}-%{version}/librdmacm.md
%{_mandir}/man7/rsocket.*

%files -n librdmacm-utils
%{_bindir}/cmtime
%{_bindir}/mckey
%{_bindir}/rcopy
%{_bindir}/rdma_client
%{_bindir}/rdma_server
%{_bindir}/rdma_xclient
%{_bindir}/rdma_xserver
%{_bindir}/riostream
%{_bindir}/rping
%{_bindir}/rstream
%{_bindir}/ucmatose
%{_bindir}/udaddy
%{_bindir}/udpong
%{_mandir}/man1/cmtime.*
%{_mandir}/man1/mckey.*
%{_mandir}/man1/rcopy.*
%{_mandir}/man1/rdma_client.*
%{_mandir}/man1/rdma_server.*
%{_mandir}/man1/rdma_xclient.*
%{_mandir}/man1/rdma_xserver.*
%{_mandir}/man1/riostream.*
%{_mandir}/man1/rping.*
%{_mandir}/man1/rstream.*
%{_mandir}/man1/ucmatose.*
%{_mandir}/man1/udaddy.*
%{_mandir}/man1/udpong.*

%files -n srp_daemon
%config(noreplace) %{_sysconfdir}/srp_daemon.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/srp_daemon.conf
%{_libexecdir}/srp_daemon/start_on_all_ports
%{_unitdir}/srp_daemon.service
%{_unitdir}/srp_daemon_port@.service
%{_sbindir}/ibsrpdm
%{_sbindir}/srp_daemon
%{_sbindir}/run_srp_daemon
%{_udevrulesdir}/60-srp_daemon.rules
%{_mandir}/man1/ibsrpdm.1*
%{_mandir}/man1/srp_daemon.1*
%{_mandir}/man5/srp_daemon.service.5*
%{_mandir}/man5/srp_daemon_port@.service.5*
%doc %{_docdir}/%{name}-%{version}/ibsrpdm.md

%changelog
* Tue Oct 02 2018 Aron Silverton <aron.silverton@oracle.com> - 5:17.1
- libibverbs: Add additional "#ifndef WITHOUT_ORACLE_EXTENSIONS" markers (Gerd Rausch) [Orabug: 28144657]
- libibverbs: Add upstream & old Oracle-ABI compatibility (Gerd Rausch) [Orabug: 28144657] 

* Mon Aug 27 2018 Aron Silverton <aron.silverton@oracle.com> - 5:17.1-1.0.4
- spec: Use Ninja (ninja-build) for building (Aron Silverton) [Orabug: 28305731]
- oracle: Reconfigure buildrpm for GIT_PROD_START build rule (Aron Silverton) [Orabug: 28557808]
- ibacm: Ignore "acme_plus_kernel_only" when using systemd (Gerd Rausch) [Orabug: 28079081]
- spec: Add "vos" to RPM release number (Aron Silverton) [Orabug 28550856]

* Fri Jun 29 2018 Aron Silverton <aron.silverton@oracle.com> - 5:17.1-1.0.3
- spec: Fix ldconfig warnings when uninstalling (Aron Silverton) [Orabug: 28146600]
- libibverbs(libmlx5): Dereference LEGACY_XRC srq objects (Gerd Rausch) [Orabug: 28064897]

* Mon May 21 2018 Aron Silverton <aron.silverton@oracle.com> - 5:17.1-1.0.2
- init: Load RDS when starting rdma service (Aron Silverton) [Orabug: 27003153]
- libibverbs: Add Shared PD (Gerd Rausch) [Orabug: 28036886, 26440016]
- libibverbs: Add XRC Compatibility Layer (Ajaykumar Hotchandani) [Orabug: 28037496]
- libibverbs: Add Userlevel FMR (Ajaykumar Hotchandani) [Orabug: 26547655, 27594079, 26547698]
- libibverbs(libmlx4): Disable Blueflame conditionally for MLX4 (Qing Huang) [Orabug: 28042759]
- libibverbs(libmlx5): Disable MLX5_QP_FLAG_SCATTER_CQE for Shared-PD (Gerd Rausch) [Orabug: 27949058]
- libibverbs: Detect uek_abi_version and UEK4 compatibility in libibverbs (Gerd Rausch) [Orabug: 28035740]
- init: Load Resilient RDMA IP module when staring rdma service (Sudhakar Dindukurti) [Orabug: 27740657]
- ibacm: (backport) Fix "empty port provider causes segfault" (Aron Silverton) [Orabug: 27859350]
- ibacm: (backport) Add "server_mode" and "acme_plus_kernel_only" options (Aron Silverton) [Orabug: 28058392]
- spec: Add Epoch to package versioning and adjust Obsoletes (Aron Silverton) [Orabug: 27774601]

* Wed Mar 28 2018 Aron Silverton <aron.silverton@oracle.com> - 17.1
- Add Epoch to package versioning and adjust Obsoletes (Aron Silverton) [Orabug: 27774601]

* Wed Mar 14 2018 Aron Silverton <aron.silverton@oracle.com> - 17.1-1.0.1
- Initial release for Oracle (Aron Silverton) [Orabug: 26829960]
