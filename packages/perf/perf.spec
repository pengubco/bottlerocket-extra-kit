%global debug_package %{nil}
%global kversion 6.1.190

Name:    %{_cross_os}perf
Version: %{kversion}
Release: 1%{?dist}
Summary: Linux kernel performance analysis tool
License: GPL-2.0-only
URL:     https://www.kernel.org/

# Same AL2023 kernel SRPM used by bottlerocket-kernel-kit kernel-6.1
Source0: https://cdn.amazonlinux.com/al2023/blobstore/a5bd89eb90dc5c4a71535d05acd83210b0637aee68a9bb3a055e83d92de9cf25/kernel-6.1.190-237.442.amzn2023.src.rpm

Requires: %{_cross_os}perfrun

BuildRequires: bc
BuildRequires: elfutils-devel
BuildRequires: flex
BuildRequires: bison
BuildRequires: make
BuildRequires: gcc
BuildRequires: python3-devel
BuildRequires: %{_cross_os}libelf-devel
BuildRequires: %{_cross_os}libz-devel
BuildRequires: %{_cross_os}libcap-devel

%description
%{summary}.

%prep
# Extract the kernel source tarball from the SRPM
rpm2cpio %{S:0} | cpio -iu {,./}linux-%{kversion}.tar.xz
tar -xof linux-%{kversion}.tar.xz
rm -f linux-%{kversion}.tar.xz

%build
cd linux-%{kversion}

export ARCH="%{_cross_karch}"
export CROSS_COMPILE="%{_cross_target}-"

make -C tools/perf \
    ARCH="%{_cross_karch}" \
    CROSS_COMPILE="%{_cross_target}-" \
    CC="%{_cross_target}-gcc" \
    AR="%{_cross_target}-ar" \
    LD="%{_cross_target}-ld" \
    prefix="%{_cross_prefix}" \
    NO_LIBPYTHON=1 \
    NO_LIBPERL=1 \
    NO_LIBTRACEEVENT=1 \
    NO_LIBUNWIND=1 \
    NO_LIBDW_DWARF_UNWIND=1 \
    NO_SLANG=1 \
    NO_GTK2=1 \
    NO_DEMANGLE=1 \
    NO_JVMTI=1 \
    NO_BPF_SKEL=1 \
    EXTRA_CFLAGS="-Wno-nonnull" \
    LDFLAGS="%{_cross_ldflags}" \
    %{?_smp_mflags}

%install
cd linux-%{kversion}

install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 tools/perf/perf %{buildroot}%{_cross_bindir}/perf

%files
%{_cross_attribution_file}
%{_cross_bindir}/perf

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 6.1.190-1
- Build from kernel 6.1.190, matching bottlerocket-kernel-kit 9.8.0

* Tue Mar 10 2026 Bottlerocket Team <bottlerocket@amazon.com> - 6.1.159-1
- Initial package for perf from kernel 6.1.159
