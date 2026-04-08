Name:    %{_cross_os}strace
Version: 6.18
Release: 1%{?dist}
Summary: Diagnostic, debugging and instructional userspace utility for Linux
License: LGPL-2.1-or-later
URL:     https://strace.io

Source0: https://strace.io/files/%{version}/strace-%{version}.tar.xz

BuildRequires: %{_cross_os}glibc-devel

%description
%{summary}.

%prep
%setup -q -n strace-%{version}

%build
%cross_configure \
    --disable-mpers

%make_build

%install
%make_install

rm -rf %{buildroot}%{_cross_mandir}
rm -rf %{buildroot}%{_cross_datadir}

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/strace
%{_cross_bindir}/strace-log-merge

%changelog
* Tue Apr 07 2026 Bottlerocket Team <bottlerocket@amazon.com> - 6.18-1
- Initial package for strace 6.18
