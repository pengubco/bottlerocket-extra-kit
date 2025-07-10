Name: %{_cross_os}oomd
Summary: Userspace Out-Of-Memory (OOM) killer
Version: 0.5.0
Release: 1%{?dist}
License: GPL-2.0
 
URL: https://github.com/facebookincubator/oomd
Source0: https://github.com/facebookincubator/oomd/archive/refs/tags/v%{version}.tar.gz

# Resolved a compiler error due to lacking include
Patch0: %{url}/commit/83a6742f08349fbc93f459228dcc3d1f56eac411.patch

BuildRequires: meson
BuildRequires: %{_cross_os}jsoncpp-devel

Requires: %{_cross_os}libstdc++

%description
%{summary}

This package installs only the oomd binary, not the oomd.service. 

%prep
%autosetup -n oomd-%{version} -p1
 
%build
%cross_meson 
%cross_meson_build

%install
%cross_meson_install

%files
%license LICENSE
%doc README.md CONTRIBUTING.md CODE_OF_CONDUCT.md docs/
%{_cross_bindir}/oomd
%{_cross_sysconfdir}/oomd/
%exclude %{_cross_mandir}/*
%exclude %{_cross_unitdir}/oomd.service
%{_cross_attribution_file}