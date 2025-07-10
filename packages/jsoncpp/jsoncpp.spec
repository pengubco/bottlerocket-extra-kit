	
%global jsondir json
%global sover 26

Name: %{_cross_os}jsoncpp
Summary: JSON library implemented in C++
Version: 1.9.6
Release: 1%{?dist}
License: MIT
 
URL: https://github.com/open-source-parsers/jsoncpp
Source0: https://github.com/open-source-parsers/jsoncpp/archive/refs/tags/%{version}.tar.gz

BuildRequires:	meson

%description
%{summary}

%package devel
Summary: Files for development using the jsoncpp library
Requires: %{name}

%description devel
%{summary}.

%prep
%autosetup -n jsoncpp-%{version} -p1
 
%build
%cross_meson 
%cross_meson_build

%install
%cross_meson_install

%files
%license AUTHORS LICENSE
%{_cross_attribution_file}
%{_cross_libdir}/libjsoncpp.so.%{sover}*

%files devel
%{_cross_libdir}/libjsoncpp.so
%{_cross_includedir}/%{jsondir}
%{_cross_libdir}/cmake/*
%{_cross_pkgconfigdir}/jsoncpp.pc
