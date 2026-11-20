%global debug_package %{nil}
%global kversion 6.1.159
%global pciver 3.15.0

Name:    %{_cross_os}cpupower
Version: %{kversion}
Release: 1%{?dist}
Summary: Examine and tune CPU frequency and idle-state settings
License: GPL-2.0-only AND GPL-2.0-or-later
URL:     https://www.kernel.org/

# Same AL2023 kernel SRPM used by the perf package
Source0: https://cdn.amazonlinux.com/al2023/blobstore/dce51e264ae9f9dc1841aaba22ea3ccd34ebc646acd5518b0604134097062c6c/kernel-6.1.159-181.297.amzn2023.src.rpm
# Built as a private static library: cpupower always links -lpci, and the
# core kit's pciutils package ships only lspci, not libpci.
Source1: https://mirrors.edge.kernel.org/pub/software/utils/pciutils/pciutils-%{pciver}.tar.xz

BuildRequires: make
BuildRequires: %{_cross_os}glibc-devel

%description
%{summary}.

%prep
rpm2cpio %{S:0} | cpio -iu {,./}linux-%{kversion}.tar.xz
tar -xof linux-%{kversion}.tar.xz
rm -f linux-%{kversion}.tar.xz
tar -xof %{S:1}

%build
# Static, minimal libpci: no zlib, DNS, kmod or udev hwdb lookups. cpupower
# only reads PCI config space (AMD boost / family 14h idle monitor), so the
# optional name-resolution backends are not needed.
pcistage="${PWD}/pci-stage"
make -C pciutils-%{pciver} \
    CROSS_COMPILE="%{_cross_target}-" \
    HOST="%{_cross_arch}-linux" \
    PREFIX=/usr \
    OPT="%{_cross_cflags}" \
    ZLIB=no DNS=no SHARED=no LIBKMOD=no HWDB=no \
    DESTDIR="${pcistage}" \
    %{?_smp_mflags} \
    install-lib

# - STATIC=true links libcpupower into the binary, so no shared library has
#   to be shipped alongside it.
# - NLS and the cpufreq-bench tool are disabled; Bottlerocket ships no
#   translations and the bench tool is a development aid.
# - DEBUG=false enables optimization; the Makefile otherwise builds -O1 -g.
# - The Makefile appends its own flags with "override CFLAGS +=", so the
#   cross CFLAGS can be passed on the command line.
make -C linux-%{kversion}/tools/power/cpupower \
    CROSS="%{_cross_target}-" \
    STATIC=true \
    NLS=false \
    CPUFREQ_BENCH=false \
    DEBUG=false \
    V=true \
    CFLAGS="%{_cross_cflags} -I${pcistage}/usr/include" \
    LDFLAGS="%{_cross_ldflags} -L${pcistage}/usr/lib" \
    %{?_smp_mflags}

%install
install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 linux-%{kversion}/tools/power/cpupower/cpupower %{buildroot}%{_cross_bindir}/cpupower

%files
%license linux-%{kversion}/LICENSES/preferred/GPL-2.0 pciutils-%{pciver}/COPYING
%{_cross_attribution_file}
%{_cross_bindir}/cpupower

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 6.1.159-1
- Initial package for cpupower from kernel 6.1.159
