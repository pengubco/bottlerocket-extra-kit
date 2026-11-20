%global sover 1

Name:    %{_cross_os}libtraceevent
Version: 1.9.1
Release: 1%{?dist}
Summary: Library to parse raw trace event formats
License: LGPL-2.1-only AND GPL-2.0-only
URL:     https://git.kernel.org/pub/scm/libs/libtrace/libtraceevent.git/

Source0: https://git.kernel.org/pub/scm/libs/libtrace/libtraceevent.git/snapshot/libtraceevent-%{version}.tar.gz

BuildRequires: meson
BuildRequires: %{_cross_os}glibc-devel

%description
%{summary}.

%package devel
Summary: Files for development using the libtraceevent library
Requires: %{name}

%description devel
%{summary}.

%prep
%autosetup -n libtraceevent-%{version} -p1

%build
# Documentation needs asciidoc/xmlto, which are not in the SDK and would only
# produce man pages that Bottlerocket does not ship anyway.
%cross_meson \
    -Ddoc=false
%cross_meson_build

%install
%cross_meson_install

%files
%license LICENSES/LGPL-2.1 LICENSES/GPL-2.0
%{_cross_attribution_file}
%{_cross_libdir}/libtraceevent.so.%{sover}*
%dir %{_cross_libdir}/traceevent
%{_cross_libdir}/traceevent/plugins

%files devel
%{_cross_libdir}/libtraceevent.so
%{_cross_includedir}/traceevent
%{_cross_pkgconfigdir}/libtraceevent.pc

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 1.9.1-1
- Initial package for libtraceevent 1.9.1
