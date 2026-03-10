Name:    %{_cross_os}procps-ng
Version: 4.0.5
Release: 1%{?dist}
Summary: Utilities for monitoring processes (ps, top, free, vmstat, etc.)
License: GPL-2.0-or-later AND LGPL-2.0-or-later
URL:     https://gitlab.com/procps-ng/procps

Source0: https://sourceforge.net/projects/procps-ng/files/Production/procps-ng-%{version}.tar.xz/download

BuildRequires: %{_cross_os}glibc-devel

%description
%{summary}.

%prep
%setup -q -n procps-ng-%{version}

%build
# Suppress RPATH check failures caused by cross-compilation sysroot paths
%global __brp_check_rpaths %{nil}

%cross_configure \
    --disable-nls \
    --disable-modern-top \
    --without-ncurses \
    --disable-w \
    ac_cv_func_malloc_0_nonnull=yes \
    ac_cv_func_realloc_0_nonnull=yes

%make_build

%install
%make_install

rm -rf %{buildroot}%{_cross_mandir}
rm -rf %{buildroot}%{_cross_datadir}/locale
rm -rf %{buildroot}%{_cross_docdir}
find %{buildroot}%{_cross_libdir} -name '*.a' -delete
find %{buildroot}%{_cross_libdir} -name '*.la' -delete

%files
%license COPYING COPYING.LIB
%{_cross_attribution_file}
%{_cross_bindir}/free
%{_cross_bindir}/kill
%{_cross_bindir}/pgrep
%{_cross_bindir}/pidof
%{_cross_bindir}/pidwait
%{_cross_bindir}/pkill
%{_cross_bindir}/pmap
%{_cross_bindir}/ps
%{_cross_bindir}/pwdx
%{_cross_bindir}/tload
%{_cross_bindir}/uptime
%{_cross_bindir}/vmstat
%{_cross_sbindir}/sysctl
%{_cross_libdir}/libproc2.so
%{_cross_libdir}/libproc2.so.*
%{_cross_libdir}/pkgconfig/libproc2.pc
%{_cross_includedir}/libproc2/

%changelog
* Sat Mar 07 2026 Bottlerocket Team <bottlerocket@amazon.com> - 4.0.5-1
- Initial package for procps-ng 4.0.5
