%define uek2epoch 2
%define uek4epoch 4
%define uek5epoch 5

%global flavor ora

%ifnarch s390 %{arm}
%define dma_coherent 1
%endif

%define         git_hash %{nil}
Name:           rdma-core
Epoch:          %{uek5epoch}
Version:        19.2
Release:        1.0.2%{?dist}%{?flavor}
Summary:        RDMA core userspace libraries and daemons (Oracle Extensions)
License:        GPL-2.0 or BSD-2-Clause

# Almost everything is licensed under the OFA dual GPLv2, 2 Clause BSD license
#  providers/ipathverbs/ Dual licensed using a BSD license with an extra patent clause
#  providers/rxe/ Incorporates code from ipathverbs and contains the patent clause
#  providers/hfi1verbs Uses the 3 Clause BSD license
Url:            https://github.com/linux-rdma/rdma-core
Source:         rdma-core-%{version}%{git_hash}.tar.gz
BuildRequires:  binutils
BuildRequires:  cmake >= 2.8.11
BuildRequires:  gcc
BuildRequires:  pandoc
BuildRequires:  pkgconfig
BuildRequires:  pkgconfig(libnl-3.0)
BuildRequires:  pkgconfig(libnl-route-3.0)
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  pkgconfig(udev)
BuildRequires:  python
BuildRequires:  sed
%ifnarch s390 S390x
BuildRequires:  valgrind-devel
%endif

Requires:       dracut
Requires:       initscripts
Requires:       kmod
Requires:       pciutils
Requires:       systemd
Requires:       udev

# Set minimum kernel version for Oracle UEK5
Requires:       kernel-uek >= 4.14.35-1844

# Oracle previously shipped oracle/ as a stand-alone
# package called 'rdma', which we're supplanting here.
Provides:       rdma = %{epoch}:%{version}-%{release}
Obsoletes:      rdma < %{epoch}:%{version}-%{release}

# the rdma-ndd utility moved from infiniband-diags to rdma-core
Conflicts:      infiniband-diags <= 1.6.7
Provides:       rdma-ndd = %{epoch}:%{version}-%{release}
Obsoletes:      rdma-ndd < %{epoch}:%{version}-%{release}

# 32-bit arm is missing required arch-specific memory barriers
ExcludeArch: %{arm}

# Since we recommend developers use Ninja, so should packagers, for consistency.
#  Oracle Linux 7 does not ship Ninja so the build system must be configured to
#  enable the EPEL repo.
BuildRequires:  ninja-build
%define CMAKE_FLAGS -GNinja
%define make_jobs ninja-build -v %{?_smp_mflags}
%define cmake_install DESTDIR=%{buildroot} ninja-build install

%description
RDMA core userspace infrastructure and documentation, including initialization
scripts, kernel driver-specific modprobe override configs, IPoIB network scripts,
dracut rules, and the rdma-ndd utility.

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%package        devel
Summary:        RDMA core development libraries and headers (Oracle Extensions)
Requires:       %{name}%{?_isa} = %{epoch}:%{version}-%{release}

Requires:       libibverbs = %{epoch}:%{version}-%{release}
Provides:       libibverbs-devel = %{epoch}:%{version}-%{release}
Obsoletes:      libibverbs-devel < %{epoch}:%{version}-%{release}
Provides:       libibverbs-devel-static = %{epoch}:%{version}-%{release}
Obsoletes:      libibverbs-devel-static < %{epoch}:%{version}-%{release}

Requires:       libibumad = %{epoch}:%{version}-%{release}
Provides:       libibumad-devel = %{epoch}:%{version}-%{release}
Obsoletes:      libibumad-devel < %{epoch}:%{version}-%{release}
Provides:       libibumad-static = %{epoch}:%{version}-%{release}
Obsoletes:      libibumad-static < %{epoch}:%{version}-%{release}

Requires:       librdmacm = %{epoch}:%{version}-%{release}
Provides:       librdmacm-devel = %{epoch}:%{version}-%{release}
Obsoletes:      librdmacm-devel < %{epoch}:%{version}-%{release}
Provides:       librdmacm-static = %{epoch}:%{version}-%{release}
Obsoletes:      librdmacm-static < %{epoch}:%{version}-%{release}

Requires:       ibacm = %{epoch}:%{version}-%{release}
Provides:       ibacm-devel = %{epoch}:%{version}-%{release}
Obsoletes:      ibacm-devel < %{epoch}:%{version}-%{release}

Provides:       libcxgb3-static = %{epoch}:%{version}-%{release}
Obsoletes:      libcxgb3-static < %{epoch}:%{version}-%{release}

Provides:       libcxgb4-static = %{epoch}:%{version}-%{release}
Obsoletes:      libcxgb4-static < %{epoch}:%{version}-%{release}

Provides:       libhfi1-static = %{epoch}:%{version}-%{release}
Obsoletes:      libhfi1-static < %{epoch}:%{version}-%{release}

Provides:       libipathverbs-static = %{epoch}:%{version}-%{release}
Obsoletes:      libipathverbs-static < %{epoch}:%{version}-%{release}
%if 0%{?dma_coherent}
Provides:       libmlx4-static = %{epoch}:%{version}-%{release}
Obsoletes:      libmlx4-static < %{epoch}:%{version}-%{release}

Provides:       libmlx5-static = %{epoch}:%{version}-%{release}
Obsoletes:      libmlx5-static < %{epoch}:%{version}-%{release}
%endif
Provides:       libnes-static = %{epoch}:%{version}-%{release}
Obsoletes:      libnes-static < %{epoch}:%{version}-%{release}

Provides:       libocrdma-static = %{epoch}:%{version}-%{release}
Obsoletes:      libocrdma-static < %{epoch}:%{version}-%{release}

Provides:       libi40iw-devel-static = %{epoch}:%{version}-%{release}
Obsoletes:      libi40iw-devel-static < %{epoch}:%{version}-%{release}

Provides:       libmthca-static = %{epoch}:%{version}-%{release}
Obsoletes:      libmthca-static < %{epoch}:%{version}-%{release}

%description devel
RDMA core development libraries and headers.

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%package -n     libibverbs
Summary:        A library and drivers for direct userspace use of RDMA (InfiniBand/iWARP/RoCE) hardware (Oracle Extensions)
Requires:       %{name}%{?_isa} = %{epoch}:%{version}-%{release}

Provides:       libcxgb3 = %{epoch}:%{version}-%{release}
Obsoletes:      libcxgb3 < %{epoch}:%{version}-%{release}

Provides:       libcxgb4 = %{epoch}:%{version}-%{release}
Obsoletes:      libcxgb4 < %{epoch}:%{version}-%{release}

Provides:       libhfi1 = %{epoch}:%{version}-%{release}
Obsoletes:      libhfi1 < %{epoch}:%{version}-%{release}

Provides:       libi40iw = %{epoch}:%{version}-%{release}
Obsoletes:      libi40iw < %{epoch}:%{version}-%{release}

Provides:       libipathverbs = %{epoch}:%{version}-%{release}
Obsoletes:      libipathverbs < %{epoch}:%{version}-%{release}
%if 0%{?dma_coherent}
Provides:       libmlx4 = %{epoch}:%{version}-%{release}
Obsoletes:      libmlx4 < %{epoch}:%{version}-%{release}
%ifnarch s390x
Provides:       libmlx5 = %{epoch}:%{version}-%{release}
Obsoletes:      libmlx5 < %{epoch}:%{version}-%{release}
%endif
%endif
Provides:       libmthca = %{epoch}:%{version}-%{release}
Obsoletes:      libmthca < %{epoch}:%{version}-%{release}

Provides:       libnes = %{epoch}:%{version}-%{release}
Obsoletes:      libnes < %{epoch}:%{version}-%{release}

Provides:       libocrdma = %{epoch}:%{version}-%{release}
Obsoletes:      libocrdma < %{epoch}:%{version}-%{release}

Provides:       librxe = %{epoch}:%{version}-%{release}
Obsoletes:      librxe < %{epoch}:%{version}-%{release}

Provides:       libusnic_verbs = %{epoch}:%{version}-%{release}
Obsoletes:      libusnic_verbs < %{epoch}:%{version}-%{release}

%description -n libibverbs
libibverbs is a library that allows userspace processes to use RDMA
"verbs" as described in the InfiniBand Architecture Specification and
the RDMA Protocol Verbs Specification.  This includes direct hardware
access from userspace to InfiniBand/iWARP adapters (kernel bypass) for
fast path operations.

Device-specific plug-in ibverbs userspace drivers are included:

- libbxnt_re: Broadcom NetXtreme-E RoCE HCA
- libcxgb3: Chelsio T3 iWARP HCA
- libcxgb4: Chelsio T4 iWARP HCA
- libhfi1: Intel Omni-Path HFI
- libhns: HiSilicon Hip06 SoC
- libi40iw: Intel Ethernet Connection X722 RDMA
- libipathverbs: QLogic InfiniPath HCA
- libmlx4: Mellanox ConnectX-3 InfiniBand HCA (except arm, s390)
- libmlx5: Mellanox Connect-IB/X-4+ InfiniBand HCA (except arm, s390, s390x)
- libmthca: Mellanox InfiniBand HCA
- libnes: NetEffect RNIC
- libocrdma: Emulex OneConnect RDMA/RoCE Device
- libqedr: QLogic QL4xxx RoCE HCA
- librxe: A software implementation of the RoCE protocol
- libvmw_pvrdma: VMware paravirtual RDMA device

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%package -n     libibverbs-utils
Summary:        Examples for the libibverbs library (Oracle Extensions)
Requires:       libibverbs%{?_isa} = %{epoch}:%{version}-%{release}

%description -n libibverbs-utils
Useful libibverbs example programs such as ibv_devinfo, which
displays information about RDMA devices.

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%package -n     ibacm
Summary:        InfiniBand Communication Manager Assistant (Oracle Extensions)
Requires:       %{name}%{?_isa} = %{epoch}:%{version}-%{release}
Requires:       libibumad%{?_isa} = %{epoch}:%{version}-%{release}
Requires:       libibverbs%{?_isa} = %{epoch}:%{version}-%{release}
%{?systemd_requires}

%description -n ibacm
The ibacm daemon helps reduce the load of managing path record lookups on
large InfiniBand fabrics by providing a user space implementation of what
is functionally similar to an ARP cache.  The use of ibacm, when properly
configured, can reduce the SA packet load of a large IB cluster from O(n^2)
to O(n).  The ibacm daemon is started and normally runs in the background,
user applications need not know about this daemon as long as their app
uses librdmacm to handle connection bring up/tear down.  The librdmacm
library knows how to talk directly to the ibacm daemon to retrieve data.

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%package -n     iwpmd
Summary:        iWarp Port Mapper userspace daemon (Oracle Extensions)
Requires:       %{name}%{?_isa} = %{epoch}:%{version}-%{release}
%{?systemd_requires}

%description -n iwpmd
iwpmd provides a userspace service for iWarp drivers to claim
tcp ports through the standard socket interface.

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%package -n     libibumad
Summary:        OpenFabrics Alliance InfiniBand umad (userspace management datagram) library (Oracle Extensions)
Requires:       %{name}%{?_isa} = %{epoch}:%{version}-%{release}

%description -n libibumad
libibumad provides the userspace management datagram (umad) library
functions, which sit on top of the umad modules in the kernel. These
are used by the IB diagnostic and management tools, including OpenSM.

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%package -n     librdmacm
Summary:        Userspace RDMA Connection Manager (Oracle Extensions)
Requires:       %{name}%{?_isa} = %{epoch}:%{version}-%{release}
Requires:       libibverbs%{?_isa} = %{epoch}:%{version}-%{release}

%description -n librdmacm
librdmacm provides a userspace RDMA Communication Management API.

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%package -n     librdmacm-utils
Summary:        Examples for the librdmacm library (Oracle Extensions)
Requires:       librdmacm%{?_isa} = %{epoch}:%{version}-%{release}
Requires:       libibverbs%{?_isa} = %{epoch}:%{version}-%{release}

%description -n librdmacm-utils
Example test programs for the librdmacm library.

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%package -n     srp_daemon
Summary:        Tools for using the InfiniBand SRP protocol devices (Oracle Extensions)
Requires:       %{name}%{?_isa} = %{epoch}:%{version}-%{release}
Requires:       libibumad%{?_isa} = %{epoch}:%{version}-%{release}
Requires:       libibverbs%{?_isa} = %{epoch}:%{version}-%{release}
%{?systemd_requires}

Provides:       srptools = %{epoch}:%{version}-%{release}
Obsoletes:      srptools <= 1.0.3
Obsoletes:      openib-srptools <= 0.0.6

%description -n srp_daemon
In conjunction with the kernel ib_srp driver, srp_daemon allows you to
discover and use SCSI devices via the SCSI RDMA Protocol over InfiniBand.

For use on Oracle Linux systems running the Oracle Database Virtual OS layer.

%prep
%setup -q -n  %{name}-%{version}%{git_hash}

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

# Make rpmlint happy. On OL, _lib is lib64 so _libdir resolves to /usr/lib64 and
# there is no macro for /usr/lib which is where dracut and modrprobe.d live.
%global oldlib lib
%global dracutlibdir %{_prefix}/%{oldlib}/dracut
%global sysmodprobedir %{_prefix}/%{oldlib}/modprobe.d

mkdir -p %{buildroot}/%{_sysconfdir}/sysconfig/network-scripts
mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d
mkdir -p %{buildroot}%{_libexecdir}
mkdir -p %{buildroot}%{_udevrulesdir}
mkdir -p %{buildroot}%{dracutlibdir}/modules.d/05rdma
mkdir -p %{buildroot}%{sysmodprobedir}
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_sysconfdir}/sysctl.d

# IPoIB - We need to configure IPoIB interfaces
install -D -m0755 oracle/rdma.ifdown-ib %{buildroot}/%{_sysconfdir}/sysconfig/network-scripts/ifdown-ib
install -D -m0755 oracle/rdma.ifup-ib %{buildroot}/%{_sysconfdir}/sysconfig/network-scripts/ifup-ib

# SRIOV - Suse has an SRIOV service, check if we need/want it
install -D -m0644 oracle/rdma.sriov-vfs %{buildroot}/%{_sysconfdir}/rdma/sriov-vfs
install -D -m0755 oracle/rdma.sriov-init %{buildroot}%{_libexecdir}/rdma-set-sriov-vf
install -D -m0644 oracle/rdma.sriov-rules %{buildroot}%{_udevrulesdir}/98-rdma-sriov.rules
install -D -m0644 oracle/rdma.sriov-service %{buildroot}%{_unitdir}/rdma-sriov.service

# Port type setup for mlx4 dual-port cards
%if 0%{?dma_coherent}
install -D -m0644 oracle/rdma.mlx4.conf %{buildroot}/%{_sysconfdir}/rdma/mlx4.conf
install -D -m0644 oracle/rdma.mlx4.sys.modprobe %{buildroot}%{sysmodprobedir}/libmlx4.conf
install -D -m0755 oracle/rdma.mlx4-setup.sh %{buildroot}%{_libexecdir}/mlx4-setup.sh
%endif
# Dracut file for IB support during boot
install -D -m0755 oracle/rdma.modules-setup.sh %{buildroot}%{dracutlibdir}/modules.d/05rdma/module-setup.sh

#
# Oracle Virtual OS (VOS) configuration
#

# Load RDS: Remove upstream /etc/rdma/modules/rdma.conf and replace with our own
rm -f %{buildroot}%{_sysconfdir}/rdma/modules/rdma.conf
install -D -m0644 oracle/modules.rdma-conf %{buildroot}%{_sysconfdir}/rdma/modules/rdma.conf

# Kernel tuning for RDS: udev rules to load net.rds sysctl settings when RDS modules are plugged
install -D -m0644 oracle/sysctl.rds-rules %{buildroot}%{_sysconfdir}/udev/rules.d/99-rds-sysctl-parameters.rules
install -D -m0644 oracle/sysctl.rds-conf %{buildroot}%{_sysconfdir}/sysctl.d/90-rds.conf

# END Oracle Virtual OS (VOS) configuration

# ibacm
bin/ib_acme -D . -O
# multi-lib conflict resolution hacks (bug 1429362)
sed -i -e 's|%{_libdir}|/usr/lib|' %{buildroot}%{_mandir}/man7/ibacm_prov.7
sed -i -e 's|%{_libdir}|/usr/lib|' ibacm_opts.cfg
install -D -m0644 ibacm_opts.cfg %{buildroot}%{_sysconfdir}/rdma/

# Delete the package's init.d scripts
rm -rf %{buildroot}/%{_initrddir}/
rm -f %{buildroot}/%{_sbindir}/srp_daemon.sh

%post -n libibverbs -p /sbin/ldconfig
%postun -n libibverbs -p /sbin/ldconfig

%post -n libibumad -p /sbin/ldconfig
%postun -n libibumad -p /sbin/ldconfig

%post -n librdmacm -p /sbin/ldconfig
%postun -n librdmacm -p /sbin/ldconfig

%post
# we ship udev rules, so trigger an update.
/sbin/udevadm trigger --subsystem-match=infiniband --action=change || true
/sbin/udevadm trigger --subsystem-match=infiniband_mad --action=change || true

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
%defattr(-,root,root)
%dir %{_sysconfdir}/rdma
%dir %{_sysconfdir}/rdma/modules
%dir %{_docdir}/%{name}-%{version}
%dir %{_sysconfdir}/udev
%dir %{_sysconfdir}/udev/rules.d
%dir %{_sysconfdir}/modprobe.d
%dir %{_sysconfdir}/sysctl.d
%doc %{_docdir}/%{name}-%{version}/README.md
%doc %{_docdir}/%{name}-%{version}/udev.md
%if 0%{?dma_coherent}
%config(noreplace) %{_sysconfdir}/rdma/mlx4.conf
%config(noreplace) %{_sysconfdir}/modprobe.d/mlx4.conf
%{sysmodprobedir}/libmlx4.conf
%{_libexecdir}/mlx4-setup.sh
%endif
%config(noreplace) %{_sysconfdir}/rdma/modules/infiniband.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/iwarp.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/opa.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/rdma.conf
%config(noreplace) %{_sysconfdir}/rdma/modules/roce.conf
%config(noreplace) %{_sysconfdir}/rdma/sriov-vfs
%config(noreplace) %{_sysconfdir}/udev/rules.d/*
%config(noreplace) %{_sysconfdir}/modprobe.d/truescale.conf
%config(noreplace) %{_sysconfdir}/sysctl.d/90-rds.conf
%{_unitdir}/rdma-hw.target
%{_unitdir}/rdma-load-modules@.service
%{_unitdir}/rdma-sriov.service
%dir %{dracutlibdir}/modules.d/05rdma
%{dracutlibdir}/modules.d/05rdma/module-setup.sh
# Consider replacing below with {_udevrulesdir}/*
%{_udevrulesdir}/60-rdma-ndd.rules
%{_udevrulesdir}/75-rdma-description.rules
%{_udevrulesdir}/90-rdma-hw-modules.rules
%{_udevrulesdir}/90-rdma-ulp-modules.rules
%{_udevrulesdir}/90-rdma-umad.rules
%{_udevrulesdir}/98-rdma-sriov.rules
# Consider replacing above with {_udevrulesdir}/*
%{_sysconfdir}/sysconfig/network-scripts/*
%{_sysconfdir}/udev/rules.d/99-rds-sysctl-parameters.rules
%{_libexecdir}/rdma-set-sriov-vf
%{_libexecdir}/truescale-serdes.cmds
%{_sbindir}/rdma-ndd
%{_unitdir}/rdma-ndd.service
%{_mandir}/man8/rdma-ndd.*
%license COPYING.*

%files devel
%defattr(-,root,root)
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
%if 0%{?dma_coherent}
%{_mandir}/man3/mlx5dv*
%{_mandir}/man3/mlx4dv*
%{_mandir}/man7/mlx5dv*
%{_mandir}/man7/mlx4dv*
%endif

%files -n libibverbs
%defattr(-,root,root)
%dir %{_sysconfdir}/libibverbs.d
%dir %{_libdir}/libibverbs
%{_libdir}/libibverbs*.so.*
%{_libdir}/libibverbs/*.so
%if 0%{?dma_coherent}
%{_libdir}/libmlx5.so.*
%{_libdir}/libmlx4.so.*
%endif
%config(noreplace) %{_sysconfdir}/libibverbs.d/*.driver
%doc %{_docdir}/%{name}-%{version}/libibverbs.md
%doc %{_docdir}/%{name}-%{version}/rxe.md
%doc %{_docdir}/%{name}-%{version}/udev.md
%doc %{_docdir}/%{name}-%{version}/tag_matching.md
%{_bindir}/rxe_cfg
%{_mandir}/man7/rxe*
%{_mandir}/man8/rxe*

%files -n libibverbs-utils
%defattr(-,root,root)
%{_bindir}/ibv_*
%{_mandir}/man1/ibv_*

%files -n ibacm
%defattr(-,root,root)
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
%defattr(-,root,root)
%dir %{_sysconfdir}/rdma
%dir %{_sysconfdir}/rdma/modules
%{_sbindir}/iwpmd
%{_unitdir}/iwpmd.service
%config(noreplace) %{_sysconfdir}/rdma/modules/iwpmd.conf
%config(noreplace) %{_sysconfdir}/iwpmd.conf
%{_udevrulesdir}/90-iwpmd.rules
%{_mandir}/man8/iwpmd.*
%{_mandir}/man5/iwpmd.*

%files -n libibumad
%defattr(-,root,root)
%{_libdir}/libibumad*.so.*

%files -n librdmacm
%defattr(-,root,root)
%{_libdir}/librdmacm*.so.*
%dir %{_libdir}/rsocket
%{_libdir}/rsocket/*.so*
%doc %{_docdir}/%{name}-%{version}/librdmacm.md
%{_mandir}/man7/rsocket.*

%files -n librdmacm-utils
%defattr(-,root,root)
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
%defattr(-,root,root)
%dir %{_libexecdir}/srp_daemon
%dir %{_sysconfdir}/rdma
%dir %{_sysconfdir}/rdma/modules
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
* Wed Feb 27 2019 Aron Silverton <aron.silverton@oracle.com> - 5:19.2
- Add IPoIB interface configuration scripts (Aron Silverton) [Orabug: 29307270]

* Wed Feb 20 2019 Aron Silverton <aron.silverton@oracle.com> - 5:19.2-1.0.2
- libibverbs(verbs,libmlx4,libmlx5): Add Shared PD (Mark Haywood) [Orabug: 21525110, 28036829]
- libibverbs(verbs,libmlx4,libmlx5), librdmacm: Add Compatibility Layer (Mark Haywood) [Orabug: 21616281, 28037506]
- libibverbs(verbs,libmlx4,libmlx5): Add Userlevel FMR (Mark Haywood) [Orabug: 21525110, 26547698]
- libibverbs(libmlx4): Conditionally disable blueflame (Mark Haywood) [Orabug: 25894415]
- libibverbs: Detect uek_abi_version and UEK4 compatibility in libibverbs (Gerd Rausch) [Orabug: 28035740]
- libibverbs: Add upstream & old Oracle-ABI compatibility (Gerd Rausch) [Orabug: 28144657]
- ibacm: remove endpoint IP address from provider when address deleted (Mark Haywood) [Orabug: 28845883]
- ibacm: Check return value when deleting a cache entry (Håkon Bugge) [Orabug: 29037101]
- ibacm: Flush cache in provider when local address is removed (Håkon Bugge) [Orabug: 29037124]
- ibacm: Remove trailing blanks (Håkon Bugge) [Orabug: 29037144]
- ibacm: Fix proper return value from ib_acme (Håkon Bugge) [Orabug: 29037153]
- ibacm: Handle rereg event coming before link active event (Håkon Bugge) [Orabug: 29037189]
- ibacm: Use helper functions and existing defines to avoid literal use (Håkon Bugge) [Orabug: 29026611]
- ibacm: Unable to assign EP name for limited pkey (Håkon Bugge) [Orabug: 29037216]
- ibacm: Fix improper refcnt (Håkon Bugge) [Orabug: 29037237]
- ibacm: Fix incorrect length used in address comparisons (Håkon Bugge) [Orabug: 29037253]
- ibacm: Copy correct number of address bytes before calling provider (Håkon Bugge) [Orabug: 29037270]

* Thu Jan 31 2019 Aron Silverton <aron.silverton@oracle.com> - 5:19.2-1.0.1
- oracle: Package for Oracle (Aron Silverton) [Orabug: 29356186]
- oracle/spec: Load RDS kernel modules using hot-plug (Aron Silverton) [Orabug: 28667038]
- oracle/spec: Load sysctl settings for RDS (Aron Silverton) [Orabug: 28667038]
- oracle: Disable loading ib_iser (Aron Silverton) [Orabug: 28188517]
- oracle: Disable loading NFS over RDMA (Aron Silverton) [Orabug: 28667412]
- oracle: Load RDMAIP kernel module using hot-plug (Aron Silverton) [Orabug: 28782057]
- oracle/spec: Set minimum required kernel (Aron Silverton) [Orabug: 29391672]
- oracle: Add buildrpm and link spec file (Aron Silverton) [Orabug: 26829960]
- oracle/spec: Set initial release number for Oracle (Aron Silverton) [Orabug: 29356186]
