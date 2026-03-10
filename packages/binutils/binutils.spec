Name:    %{_cross_os}binutils
Version: 2.44
Release: 1%{?dist}
Summary: GNU binary utilities (strings, nm, objdump, readelf, etc.)
License: GPL-3.0-or-later AND LGPL-2.0-or-later
URL:     https://www.gnu.org/software/binutils/

Source0: https://ftp.gnu.org/gnu/binutils/binutils-%{version}.tar.xz

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libz-devel

%description
%{summary}.

%prep
%setup -q -n binutils-%{version}

%build
# Suppress the RPATH check that fails for cross-compiled sysroot paths
%global __brp_check_rpaths %{nil}

%cross_configure \
    --disable-gold \
    --disable-ld \
    --disable-gdb \
    --disable-gdbserver \
    --disable-sim \
    --disable-nls \
    --disable-gprofng \
    --without-debuginfod \
    --without-zstd \
    --enable-shared \
    ac_cv_func_getrlimit=yes \
    ac_cv_func_setrlimit=yes

%make_build

%install
%make_install

rm -rf %{buildroot}%{_cross_mandir}
rm -rf %{buildroot}%{_cross_infodir}
rm -rf %{buildroot}%{_cross_datadir}/locale
# Remove static libs and libtool archives not needed at runtime
find %{buildroot}%{_cross_libdir} -name '*.a' -delete
find %{buildroot}%{_cross_libdir} -name '*.la' -delete

%files
%license COPYING COPYING.LIB
%{_cross_attribution_file}
%{_cross_bindir}/*
%{_cross_libdir}/*.so*
%dir %{_cross_prefix}/x86_64-bottlerocket-linux-gnu/bin/
%{_cross_prefix}/x86_64-bottlerocket-linux-gnu/bin/*
%{_cross_includedir}/
%{_cross_datadir}/

%changelog
* Sat Mar 07 2026 Bottlerocket Team <bottlerocket@amazon.com> - 2.44-1
- Initial package for GNU binutils 2.44
