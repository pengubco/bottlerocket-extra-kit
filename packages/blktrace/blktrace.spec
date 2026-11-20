Name:    %{_cross_os}blktrace
Version: 1.3.0
Release: 1%{?dist}
Summary: Block layer IO tracing utilities
License: GPL-2.0-or-later
URL:     https://git.kernel.org/pub/scm/linux/kernel/git/axboe/blktrace.git

Source0: https://brick.kernel.dk/snaps/blktrace-%{version}.tar.gz

BuildRequires: %{_cross_os}glibc-devel

# btrace is a /bin/sh wrapper around blktrace and blkparse.
Requires: %{_cross_os}bash

%description
%{summary}.

%prep
%autosetup -n blktrace-%{version} -p1

%build
# blktrace ships hand-written Makefiles with no configure script. Only the
# targets we ship are built: btreplay needs libaio and iowatcher needs
# external plotting tools, and neither is useful on Bottlerocket. The
# Makefiles add the _GNU_SOURCE and large-file defines on top of CFLAGS.
%make_build \
    CC="%{_cross_target}-gcc" \
    CFLAGS="%{_cross_cflags}" \
    LDFLAGS="%{_cross_ldflags}" \
    blktrace blkparse blkiomon
%make_build -C btt \
    CC="%{_cross_target}-gcc" \
    CFLAGS="%{_cross_cflags}" \
    LDFLAGS="%{_cross_ldflags}" \
    btt

%install
install -d %{buildroot}%{_cross_bindir}
for prog in blktrace blkparse blkiomon btt/btt btrace; do
  install -p -m 0755 "${prog}" %{buildroot}%{_cross_bindir}/
done

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/blktrace
%{_cross_bindir}/blkparse
%{_cross_bindir}/blkiomon
%{_cross_bindir}/btt
%{_cross_bindir}/btrace

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 1.3.0-1
- Initial package for blktrace 1.3.0
