%global debug_package %{nil}
%global kversion 6.1.190

Name:    %{_cross_os}turbostat
Version: %{kversion}
Release: 1%{?dist}
Summary: Report x86 processor frequency, idle and power statistics
License: GPL-2.0-only
URL:     https://www.kernel.org/
ExclusiveArch: x86_64

# Same AL2023 kernel SRPM used by the perf package
Source0: https://cdn.amazonlinux.com/al2023/blobstore/a5bd89eb90dc5c4a71535d05acd83210b0637aee68a9bb3a055e83d92de9cf25/kernel-6.1.190-237.442.amzn2023.src.rpm

Requires: %{_cross_os}libcap

BuildRequires: make
BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libcap-devel

%description
%{summary}.

%prep
rpm2cpio %{S:0} | cpio -iu {,./}linux-%{kversion}.tar.xz
tar -xof linux-%{kversion}.tar.xz
rm -f linux-%{kversion}.tar.xz

%build
cd linux-%{kversion}

# The Makefile appends its own flags with "override CFLAGS +=", so passing
# the cross CFLAGS on the command line keeps its MSR/intel-family includes.
make -C tools/power/x86/turbostat \
    CC="%{_cross_target}-gcc" \
    CFLAGS="%{_cross_cflags}" \
    LDFLAGS="%{_cross_ldflags}" \
    %{?_smp_mflags}

%install
cd linux-%{kversion}

install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 tools/power/x86/turbostat/turbostat %{buildroot}%{_cross_bindir}/turbostat

%files
%license linux-%{kversion}/LICENSES/preferred/GPL-2.0
%{_cross_attribution_file}
%{_cross_bindir}/turbostat

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 6.1.190-1
- Build from kernel 6.1.190, matching bottlerocket-kernel-kit 9.8.0

* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 6.1.159-1
- Initial package for turbostat from kernel 6.1.159
