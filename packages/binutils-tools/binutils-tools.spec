Name:    %{_cross_os}binutils-tools
Version: 2.44
Release: 2%{?dist}
Summary: GNU binary utilities missing from the core kit (objdump, readelf, nm, strings, ...)
License: GPL-3.0-or-later AND LGPL-2.0-or-later
URL:     https://www.gnu.org/software/binutils/

Source0: https://ftp.gnu.org/gnu/binutils/binutils-%{version}.tar.xz

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libz-devel

%description
%{summary}.

The core kit's binutils package ships only ld and strip. This package adds
the other binutils programs and the shared libraries they use, and leaves
ld and strip to the core kit so both packages can be installed together.

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
%{_cross_bindir}/addr2line
%{_cross_bindir}/ar
%{_cross_bindir}/as
%{_cross_bindir}/c++filt
%{_cross_bindir}/elfedit
%{_cross_bindir}/gprof
%{_cross_bindir}/nm
%{_cross_bindir}/objcopy
%{_cross_bindir}/objdump
%{_cross_bindir}/ranlib
%{_cross_bindir}/readelf
%{_cross_bindir}/size
%{_cross_bindir}/strings
%{_cross_libdir}/libbfd-%{version}.so
%{_cross_libdir}/libopcodes-%{version}.so
%{_cross_libdir}/libctf.so.*
%{_cross_libdir}/libctf-nobfd.so.*
%{_cross_libdir}/libsframe.so.*
# strip comes from the core kit's binutils. The per-target bin directory,
# headers and unversioned .so links are only useful for building software.
%exclude %{_cross_bindir}/strip
%exclude %{_cross_prefix}/%{_cross_target}
%exclude %{_cross_includedir}
%exclude %{_cross_libdir}/libbfd.so
%exclude %{_cross_libdir}/libopcodes.so
%exclude %{_cross_libdir}/libctf.so
%exclude %{_cross_libdir}/libctf-nobfd.so
%exclude %{_cross_libdir}/libsframe.so

%changelog
* Sun Nov 22 2026 Bottlerocket Team <bottlerocket@amazon.com> - 2.44-2
- Rename to binutils-tools and drop strip, which the core kit's binutils ships,
  so both packages can be installed together

* Sat Mar 07 2026 Bottlerocket Team <bottlerocket@amazon.com> - 2.44-1
- Initial package for GNU binutils 2.44
