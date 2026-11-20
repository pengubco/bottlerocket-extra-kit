%global debug_package %{nil}
%global kversion 6.1.159

Name:    %{_cross_os}bpftool
Version: %{kversion}
Release: 1%{?dist}
Summary: Inspect and manipulate eBPF programs and maps
License: GPL-2.0-only OR BSD-2-Clause
URL:     https://www.kernel.org/

# Same AL2023 kernel SRPM used by the perf package
Source0: https://cdn.amazonlinux.com/al2023/blobstore/dce51e264ae9f9dc1841aaba22ea3ccd34ebc646acd5518b0604134097062c6c/kernel-6.1.159-181.297.amzn2023.src.rpm

Requires: %{_cross_os}libcap
Requires: %{_cross_os}libelf
Requires: %{_cross_os}libz

BuildRequires: make
BuildRequires: gcc
BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libelf-devel
BuildRequires: %{_cross_os}libz-devel
BuildRequires: %{_cross_os}libcap-devel

%description
%{summary}.

%prep
rpm2cpio %{S:0} | cpio -iu {,./}linux-%{kversion}.tar.xz
tar -xof linux-%{kversion}.tar.xz
rm -f linux-%{kversion}.tar.xz

%build
cd linux-%{kversion}

# - bpftool statically links the libbpf bundled in the kernel tree, so it
#   always matches the kernel's BPF UAPI headers.
# - VMLINUX_BTF/VMLINUX_H are forced empty so the BPF skeletons (used by
#   "prog profile" and the PID columns of "prog/map show") are not built.
#   Building them needs clang plus a vmlinux BTF; the BTF would otherwise be
#   picked up from the build host's /sys/kernel/btf/vmlinux, which is not
#   reproducible.
# - libbfd is forced off: it is only used for JIT disassembly ("prog dump
#   jited") and binutils' libbfd is not in the Bottlerocket sysroot.
# - Flags go through EXTRA_CFLAGS/EXTRA_LDFLAGS because assigning CFLAGS on
#   the command line would drop the Makefile's own include paths.
# - libbpf builds with -Werror; glibc's C23 const-preserving strchr()/strstr()
#   trip -Wdiscarded-qualifiers in this libbpf version, so keep that a warning.
make -C tools/bpf/bpftool \
    ARCH="%{_cross_karch}" \
    CROSS_COMPILE="%{_cross_target}-" \
    CC="%{_cross_target}-gcc" \
    AR="%{_cross_target}-ar" \
    LD="%{_cross_target}-ld" \
    HOSTCC=gcc HOSTLD=ld HOSTAR=ar \
    VMLINUX_BTF= VMLINUX_H= \
    feature-libbfd=0 feature-libbfd-liberty=0 feature-libbfd-liberty-z=0 \
    EXTRA_CFLAGS="%{_cross_cflags} -Wno-error=discarded-qualifiers" \
    EXTRA_LDFLAGS="%{_cross_ldflags}" \
    V=1 \
    %{?_smp_mflags}

%install
cd linux-%{kversion}

install -d %{buildroot}%{_cross_sbindir}
install -p -m 0755 tools/bpf/bpftool/bpftool %{buildroot}%{_cross_sbindir}/bpftool

%files
%license linux-%{kversion}/LICENSES/preferred/GPL-2.0 linux-%{kversion}/LICENSES/preferred/BSD-2-Clause
%{_cross_attribution_file}
%{_cross_sbindir}/bpftool

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 6.1.159-1
- Initial package for bpftool from kernel 6.1.159
