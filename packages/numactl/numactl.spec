Name:    %{_cross_os}numactl
Version: 2.0.19
Release: 1%{?dist}
Summary: Library and tools for controlling NUMA policy
License: GPL-2.0-only AND LGPL-2.1-only
URL:     https://github.com/numactl/numactl

Source0: https://github.com/numactl/numactl/releases/download/v%{version}/numactl-%{version}.tar.gz

BuildRequires: %{_cross_os}glibc-devel

Requires: %{name}-libs

%description
%{summary}.

%package libs
Summary: NUMA policy library (libnuma)
License: LGPL-2.1-only

%description libs
%{summary}.

%package devel
Summary: Files for development using libnuma
License: LGPL-2.1-only
Requires: %{name}-libs

%description devel
%{summary}.

%prep
%autosetup -n numactl-%{version} -p1

%build
%cross_configure \
    --disable-static
# libtool would otherwise bake the sysroot libdir into the tools as an RPATH.
%force_disable_rpath
%make_build

%install
%make_install

# numademo and migspeed are benchmarks/demos rather than operational tools.
rm -f %{buildroot}%{_cross_bindir}/{numademo,migspeed}
rm -f %{buildroot}%{_cross_libdir}/*.la
rm -rf %{buildroot}%{_cross_mandir}

%files
%license LICENSE.GPL2
%{_cross_attribution_file}
%{_cross_bindir}/numactl
%{_cross_bindir}/numastat
%{_cross_bindir}/migratepages
%{_cross_bindir}/memhog

%files libs
%license LICENSE.LGPL2.1
%{_cross_libdir}/libnuma.so.1*

%files devel
%{_cross_libdir}/libnuma.so
%{_cross_includedir}/numa.h
%{_cross_includedir}/numacompat1.h
%{_cross_includedir}/numaif.h
%{_cross_pkgconfigdir}/numa.pc

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 2.0.19-1
- Initial package for numactl 2.0.19
