Name:    %{_cross_os}procps-ng
Version: 4.0.5
Release: 2%{?dist}
Summary: top, watch and slabtop from procps-ng
License: GPL-2.0-or-later AND LGPL-2.0-or-later
URL:     https://gitlab.com/procps-ng/procps

Source0: https://sourceforge.net/projects/procps-ng/files/Production/procps-ng-%{version}.tar.xz/download

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libncurses-devel
Requires: %{_cross_os}libncurses

%description
%{summary}. The core kit's procps package already ships ps, free, pgrep,
vmstat, sysctl and libproc2, and util-linux ships kill; this package adds
only the ncurses tools the core kit leaves out. libproc2 is linked
statically so nothing here overlaps with the core kit's files.

%prep
%setup -q -n procps-ng-%{version}

%build
# Suppress RPATH check failures caused by cross-compilation sysroot paths
%global __brp_check_rpaths %{nil}

%cross_configure \
    --disable-nls \
    --disable-shared \
    --enable-static \
    --with-ncurses \
    --disable-w \
    --disable-kill \
    --disable-pidwait \
    ac_cv_func_malloc_0_nonnull=yes \
    ac_cv_func_realloc_0_nonnull=yes

%make_build src/top/top src/watch src/slabtop

%install
install -d %{buildroot}%{_cross_bindir}
for t in src/top/top src/watch src/slabtop; do
  install -p -m 0755 "$t" %{buildroot}%{_cross_bindir}/
done

%files
%license COPYING COPYING.LIB
%{_cross_attribution_file}
%{_cross_bindir}/top
%{_cross_bindir}/watch
%{_cross_bindir}/slabtop

%changelog
* Sat Nov 21 2026 Bottlerocket Team <bottlerocket@amazon.com> - 4.0.5-2
- Ship only top, watch and slabtop, built with ncurses and a static libproc2;
  the other tools duplicated (and conflicted with) the core kit's procps

* Sat Mar 07 2026 Bottlerocket Team <bottlerocket@amazon.com> - 4.0.5-1
- Initial package for procps-ng 4.0.5
