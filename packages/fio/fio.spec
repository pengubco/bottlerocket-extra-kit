Name:    %{_cross_os}fio
Version: 3.43
Release: 1%{?dist}
Summary: Flexible I/O tester
License: GPL-2.0-only
URL:     https://github.com/axboe/fio

Source0: https://brick.kernel.dk/snaps/fio-%{version}.tar.gz

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libaio-devel
BuildRequires: %{_cross_os}libz-devel

Requires: %{_cross_os}libaio
Requires: %{_cross_os}libz

%description
%{summary}.

%prep
%autosetup -n fio-%{version} -p1

%build
# fio ships its own hand-written configure script rather than autoconf, so
# %%cross_configure does not apply. The compiler and cross flags are passed
# explicitly, and every optional engine whose library is not in the core kit
# is disabled so the result does not depend on what happens to be in the SDK.
# --disable-native keeps -march=native out of the build; --disable-lex avoids
# a flex/bison build dependency (it only gates arithmetic in job files).
./configure \
    --prefix=%{_cross_prefix} \
    --cc=%{_cross_target}-gcc \
    --extra-cflags="%{_cross_cflags}" \
    --extra-ldflags="%{_cross_ldflags}" \
    --disable-native \
    --disable-lex \
    --disable-numa \
    --disable-rdma \
    --disable-rados \
    --disable-rbd \
    --disable-http \
    --disable-gfapi \
    --disable-pmem \
    --disable-libnfs \
    --disable-xnvme \
    --disable-isal \
    --disable-isal64 \
    --disable-libblkio \
    --disable-libzbc \
    --disable-tcmalloc \
    --disable-dfs

# Fail the build rather than silently shipping fio without the libaio engine.
grep -q '^CONFIG_LIBAIO=y' config-host.mak

%make_build V=1 fio

%install
# Install only the fio binary. Upstream "make install" also installs helper
# scripts (fio2gnuplot, fiologparser, genfio, ...) that need python, bash or
# gnuplot, none of which exist on Bottlerocket.
install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 fio %{buildroot}%{_cross_bindir}/fio

%files
%license COPYING MORAL-LICENSE
%{_cross_attribution_file}
%{_cross_bindir}/fio

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 3.43-1
- Initial package for fio 3.43
