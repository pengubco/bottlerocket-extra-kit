Name:    %{_cross_os}diffutils
Version: 3.12
Release: 1%{?dist}
Summary: GNU diff utilities (diff, cmp, diff3, sdiff)
License: GPL-3.0-or-later
URL:     https://www.gnu.org/software/diffutils/

Source0: https://ftp.gnu.org/gnu/diffutils/diffutils-%{version}.tar.xz

%description
%{summary}.

%prep
%setup -q -n diffutils-%{version}

%build
%cross_configure \
    --without-libsigsegv-prefix \
    ac_cv_func_strcasecmp=yes \
    ac_cv_func_strncasecmp=yes \
    gl_cv_func_strcasecmp_works=yes \
    gl_cv_func_strncasecmp_works=yes

%make_build

%install
%make_install

# Remove locale files and man pages to keep the package lean
rm -rf %{buildroot}%{_cross_datadir}/locale
rm -rf %{buildroot}%{_cross_mandir}
rm -rf %{buildroot}%{_cross_infodir}

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/diff
%{_cross_bindir}/diff3
%{_cross_bindir}/cmp
%{_cross_bindir}/sdiff

%changelog
* Fri Mar 06 2026 Bottlerocket Team <bottlerocket@amazon.com> - 3.12-1
- Initial package for diffutils 3.12
