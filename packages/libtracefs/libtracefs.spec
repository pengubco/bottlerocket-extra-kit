%global sover 1

Name:    %{_cross_os}libtracefs
Version: 1.8.4
Release: 1%{?dist}
Summary: Library for accessing the Linux kernel tracefs file system
License: LGPL-2.1-only AND GPL-2.0-only
URL:     https://git.kernel.org/pub/scm/libs/libtrace/libtracefs.git/

Source0: https://git.kernel.org/pub/scm/libs/libtrace/libtracefs.git/snapshot/libtracefs-%{version}.tar.gz

BuildRequires: meson
BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libtraceevent-devel
Requires: %{_cross_os}libtraceevent

%description
%{summary}.

%package devel
Summary: Files for development using the libtracefs library
Requires: %{name}
Requires: %{_cross_os}libtraceevent-devel

%description devel
%{summary}.

%prep
%autosetup -n libtracefs-%{version} -p1

%build
# Skip documentation (needs asciidoc), the sample programs (sqlhist), and the
# CUnit test suite; only the library is wanted.
%cross_meson \
    -Ddoc=false \
    -Dsamples=false \
    -Dutest=false
%cross_meson_build

%install
%cross_meson_install

%files
%license LICENSES/LGPL-2.1 LICENSES/GPL-2.0
%{_cross_attribution_file}
%{_cross_libdir}/libtracefs.so.%{sover}*
%exclude %{_cross_datadir}/bash-completion

%files devel
%{_cross_libdir}/libtracefs.so
%{_cross_includedir}/libtracefs
%{_cross_pkgconfigdir}/libtracefs.pc

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 1.8.4-1
- Initial package for libtracefs 1.8.4
