Name:    %{_cross_os}trace-cmd
Version: 3.4
Release: 1%{?dist}
Summary: Command-line front end for the Linux kernel ftrace tracer
License: GPL-2.0-only AND LGPL-2.1-only
URL:     https://git.kernel.org/pub/scm/utils/trace-cmd/trace-cmd.git/

Source0: https://git.kernel.org/pub/scm/utils/trace-cmd/trace-cmd.git/snapshot/trace-cmd-v%{version}.tar.gz

BuildRequires: meson
BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libtraceevent-devel
BuildRequires: %{_cross_os}libtracefs-devel
BuildRequires: %{_cross_os}libz-devel
BuildRequires: %{_cross_os}libzstd-devel
BuildRequires: %{_cross_os}libaudit-devel
Requires: %{_cross_os}libtraceevent
Requires: %{_cross_os}libtracefs
Requires: %{_cross_os}libz
Requires: %{_cross_os}libzstd
Requires: %{_cross_os}libaudit

%description
%{summary}.

%prep
%autosetup -n trace-cmd-v%{version} -p1

%build
# Bottlerocket has no Python runtime, and docs need asciidoc. The tarball has
# no .git, so pin the version string instead of calling git describe.
# libtracecmd is linked statically into trace-cmd by the meson build.
%cross_meson \
    -Dpython=false \
    -Ddoc=false \
    -Dutest=false \
    -Dversion-tag=%{version}
%cross_meson_build

%install
%cross_meson_install

%files
%license COPYING COPYING.LIB LICENSES/GPL-2.0 LICENSES/LGPL-2.1
%{_cross_attribution_file}
%{_cross_bindir}/trace-cmd
%exclude %{_cross_datadir}/bash-completion

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 3.4-1
- Initial package for trace-cmd 3.4
