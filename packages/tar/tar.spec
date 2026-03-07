Name:    %{_cross_os}tar
Version: 1.35
Release: 1%{?dist}
Summary: GNU tar archiving utility
License: GPL-3.0-or-later
URL:     https://www.gnu.org/software/tar/

Source0: https://ftp.gnu.org/gnu/tar/tar-%{version}.tar.xz

%description
%{summary}.

%prep
%setup -q -n tar-%{version}

%build
%cross_configure \
    --without-posix-acls \
    --without-selinux

%make_build

%install
%make_install

rm -rf %{buildroot}%{_cross_infodir}
rm -rf %{buildroot}%{_cross_mandir}
rm -rf %{buildroot}%{_cross_datadir}/locale

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/tar
%{_cross_libexecdir}/rmt

%changelog
* Fri Mar 06 2026 Bottlerocket Team <bottlerocket@amazon.com> - 1.35-1
- Initial package for GNU tar 1.35
