Name:    %{_cross_os}iotop-c
Version: 1.33
Release: 1%{?dist}
Summary: Simple top-like I/O monitor (implemented in C)
License: GPL-2.0-or-later
URL:     https://github.com/Tomas-M/iotop

Source0: https://github.com/Tomas-M/iotop/releases/download/v%{version}/iotop-%{version}.tar.xz

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libncurses-devel

Requires: %{_cross_os}libncurses

%description
%{summary}.

%prep
%autosetup -n iotop-%{version} -p1

%build
# iotop-c ships a hand-written Makefile with no configure script. It asks
# pkg-config for the ncursesw flags, so pass them explicitly instead to keep
# the host pkg-config out of a cross build; the values match the sysroot's
# ncursesw.pc. LTO is disabled as in the upstream Fedora spec.
%make_build \
    CC="%{_cross_target}-gcc" \
    CFLAGS="%{_cross_cflags}" \
    LDFLAGS="%{_cross_ldflags}" \
    NCCC="-D_DEFAULT_SOURCE -D_XOPEN_SOURCE=600" \
    NCLD="-lncursesw -ltinfo" \
    NO_FLTO=1 \
    V=1

%install
install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 iotop %{buildroot}%{_cross_bindir}/iotop

%files
%license COPYING LICENSE
%{_cross_attribution_file}
%{_cross_bindir}/iotop

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 1.33-1
- Initial package for iotop-c 1.33
