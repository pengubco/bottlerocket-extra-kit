Name:    %{_cross_os}which
Version: 2.23
Release: 1%{?dist}
Summary: GNU which - show full path of commands
License: GPL-3.0-or-later
URL:     https://savannah.gnu.org/projects/which/

Source0: https://ftp.gnu.org/gnu/which/which-%{version}.tar.gz

%description
%{summary}.

%prep
%setup -q -n which-%{version}

%build
%cross_configure

%make_build

%install
%make_install

rm -rf %{buildroot}%{_cross_infodir}
rm -rf %{buildroot}%{_cross_mandir}
rm -rf %{buildroot}%{_cross_datadir}/locale

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/which

%changelog
* Fri Mar 06 2026 Bottlerocket Team <bottlerocket@amazon.com> - 2.23-1
- Initial package for GNU which 2.23
