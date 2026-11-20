Name:    %{_cross_os}lsof
Version: 4.99.7
Release: 1%{?dist}
Summary: List open files
License: lsof
URL:     https://github.com/lsof-org/lsof

Source0: https://github.com/lsof-org/lsof/releases/download/%{version}/lsof-%{version}.tar.gz

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libselinux-devel
BuildRequires: %{_cross_os}libtirpc-devel

Requires: %{_cross_os}libselinux
Requires: %{_cross_os}libtirpc

%description
%{summary}.

%prep
%autosetup -n lsof-%{version} -p1

%build
# lsof compiles the liblsof sources directly into the binary, so there is no
# need to ship the (unstable-API) shared library. libtirpc, shipped by the core
# kit, lets lsof resolve RPC portmapper names; SELinux adds the -Z context
# column. Require both explicitly so configure fails instead of silently
# dropping them.
%cross_configure \
    --disable-liblsof \
    --with-selinux \
    --with-libtirpc
%make_build

%install
%make_install
rm -rf %{buildroot}%{_cross_mandir}

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/lsof

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 4.99.7-1
- Initial package for lsof 4.99.7
