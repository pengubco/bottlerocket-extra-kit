%global bccver 0.37.0

Name:    %{_cross_os}libbpf-tools
Version: %{bccver}
Release: 1%{?dist}
Summary: BPF CO-RE tracing and performance tools from bcc
License: (LGPL-2.1-only OR BSD-2-Clause) AND GPL-2.0-only AND GPL-3.0-only
URL:     https://github.com/iovisor/bcc/tree/master/libbpf-tools

Source0: https://github.com/iovisor/bcc/releases/download/v%{bccver}/bcc-src-with-submodule-%{bccver}.tar.gz

# libbpf is linked statically from bcc's vendored copy; libelf and libz are
# the only shared libraries the tools need besides glibc.
Requires: %{_cross_os}libelf
Requires: %{_cross_os}libz

# Host tools: the SDK's clang/llvm-strip (not RPM-managed, so not listed)
# compile the BPF objects, and a host bpftool is built from the bundled
# source to generate the skeleton headers.
BuildRequires: elfutils-devel
BuildRequires: gcc
BuildRequires: make
BuildRequires: zlib-devel
BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libelf-devel
BuildRequires: %{_cross_os}libz-devel

%description
%{summary}. Each tool is a self-contained binary with its BPF program
embedded; they rely on kernel BTF (/sys/kernel/btf/vmlinux) for CO-RE
relocation and need no compiler, headers, python or perl at runtime.
The tools are installed with a "bpf-" prefix, e.g. bpf-biolatency.

%prep
%autosetup -n bcc-src-with-submodule-%{bccver}/bcc -p1

%build
cd libbpf-tools

# Build bpftool for the build host first, with a clean environment, so the
# cross toolchain settings below never leak into it. The release tarball
# does not include bpftool's own nested libbpf submodule, so point it at the
# libbpf copy bcc vendors in src/cc/libbpf (same checkpoint commit).
mkdir -p .output/bpftool
make -C bpftool/src \
    OUTPUT="$(pwd)/.output/bpftool/" \
    BPF_DIR="$(pwd)/../src/cc/libbpf/src" \
    ARCH= CROSS_COMPILE= \
    %{?_smp_mflags} \
    bootstrap

# blazesym (used by a few tools for symbolization on x86) is a Rust crate
# that would need network access to vendor; the tools fall back to their
# built-in ELF symbolizer without it.
%make_build \
    ARCH="%{_cross_karch}" \
    CC="%{_cross_target}-gcc" \
    AR="%{_cross_target}-ar" \
    LD="%{_cross_target}-ld" \
    CLANG=clang \
    LLVM_STRIP=llvm-strip \
    BPFTOOL="$(pwd)/.output/bpftool/bootstrap/bpftool" \
    USE_BLAZESYM=0 \
    APP_PREFIX=bpf- \
    EXTRA_CFLAGS="%{_cross_cflags}" \
    EXTRA_LDFLAGS="%{_cross_ldflags}"

%install
cd libbpf-tools
# Tool names such as "profile", "capable" and "syscount" are too generic to
# put in /usr/bin as-is, so use the "bpf-" prefix Fedora's libbpf-tools uses.
make install \
    ARCH="%{_cross_karch}" \
    CC="%{_cross_target}-gcc" \
    BPFTOOL="$(pwd)/.output/bpftool/bootstrap/bpftool" \
    USE_BLAZESYM=0 \
    APP_PREFIX=bpf- \
    DESTDIR=%{buildroot} \
    bindir=%{_cross_bindir}

%files
%license LICENSE.txt src/cc/libbpf/LICENSE src/cc/libbpf/LICENSE.BSD-2-Clause src/cc/libbpf/LICENSE.LGPL-2.1
%{_cross_attribution_file}
%{_cross_bindir}/bpf-*

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 0.37.0-1
- Initial package for libbpf-tools from bcc 0.37.0
