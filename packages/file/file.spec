Name:    %{_cross_os}file
Version: 5.46
Release: 1%{?dist}
Summary: Utility to determine file type
License: BSD-2-Clause
URL:     https://www.darwinsys.com/file/

Source0: https://astron.com/pub/file/file-%{version}.tar.gz

BuildRequires: %{_cross_os}glibc-devel

%description
%{summary}.

# The cross-compiled file binary embeds the sysroot libdir as RPATH, which is
# valid on the target but triggers check-rpaths. Allow invalid RPATHs (0x0002).
%define _build_id_links none
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib/rpm/check-rpaths!!g')

%prep
%setup -q -n file-%{version}

%build
%cross_configure \
    --disable-libseccomp \
    --disable-zlib

# Prevent libtool from hardcoding the sysroot libdir as RPATH in binaries
sed -i 's|^hardcode_into_libs=yes|hardcode_into_libs=no|' libtool

# FILE_COMPILE: use host file binary to compile magic.mgc during cross-build
%make_build FILE_COMPILE=/usr/bin/file

%install
%make_install

rm -rf %{buildroot}%{_cross_mandir}
rm -rf %{buildroot}%{_cross_datadir}/locale
# Remove devel files not needed at runtime
rm -f %{buildroot}%{_cross_includedir}/magic.h
rm -f %{buildroot}%{_cross_libdir}/libmagic.so
rm -rf %{buildroot}%{_cross_libdir}/pkgconfig

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/file
%{_cross_libdir}/libmagic.so.*
%{_cross_datadir}/misc/magic.mgc
%dir %{_cross_datadir}/misc

%changelog
* Sat Mar 07 2026 Bottlerocket Team <bottlerocket@amazon.com> - 5.46-1
- Initial package for file 5.46
