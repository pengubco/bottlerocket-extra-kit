Name:    %{_cross_os}htop
Version: 3.5.3
Release: 1%{?dist}
Summary: Interactive process viewer
License: GPL-2.0-or-later
URL:     https://htop.dev/

Source0: https://github.com/htop-dev/htop/releases/download/%{version}/htop-%{version}.tar.xz

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libcap-devel
BuildRequires: %{_cross_os}libncurses-devel

Requires: %{_cross_os}libcap
Requires: %{_cross_os}libncurses

%description
%{summary}.

%prep
%setup -q -n htop-%{version}

%build
# The core kit's ncurses is built wide (libncursesw), so Unicode stays on.
# libcap lets htop drop capabilities it does not need when run as root.
# Everything else that would pull in a library Bottlerocket's core kit either
# lacks (lm_sensors, libunwind) or that adds little for a host debugging tool
# (hwloc, libnl for delay accounting) is turned off explicitly so configure
# never auto-detects it from the SDK.
%cross_configure \
    --enable-unicode \
    --enable-affinity \
    --enable-capabilities \
    --disable-hwloc \
    --disable-delayacct \
    --disable-sensors \
    --disable-backtrace \
    --disable-demangling \
    --disable-pcp \
    --disable-static

%make_build

%install
%make_install

# Drop the desktop entry, icons, and man page to keep the package lean.
rm -rf %{buildroot}%{_cross_datadir}/applications
rm -rf %{buildroot}%{_cross_datadir}/icons
rm -rf %{buildroot}%{_cross_datadir}/pixmaps
rm -rf %{buildroot}%{_cross_mandir}

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/htop

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 3.5.3-1
- Initial package for htop 3.5.3
