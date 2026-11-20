Name:    %{_cross_os}gawk
Version: 5.4.2
Release: 1%{?dist}
Summary: GNU awk pattern scanning and processing language
License: GPL-3.0-or-later
URL:     https://www.gnu.org/software/gawk/

Source0: https://ftp.gnu.org/gnu/gawk/gawk-%{version}.tar.xz

BuildRequires: %{_cross_os}glibc-devel

%description
%{summary}.

%prep
%setup -q -n gawk-%{version}

%build
# Keep gawk self-contained: no MPFR/GMP arbitrary precision (-M), no readline
# for the --debug prompt, no persistent memory allocator, and no dynamic
# extensions, so the only runtime dependency is glibc.
%cross_configure \
    --disable-mpfr \
    --disable-pma \
    --disable-extensions \
    --disable-nls \
    --without-readline

%make_build

%install
%make_install

# Drop the versioned hardlink, the gawkbug reporting script (needs a mailer),
# the profile.d snippets, the bundled awk library scripts, locale data, man
# pages, and info docs to keep the package lean.
rm -f %{buildroot}%{_cross_bindir}/gawk-%{version}
rm -f %{buildroot}%{_cross_bindir}/gawkbug
rm -rf %{buildroot}%{_cross_sysconfdir}
rm -rf %{buildroot}%{_cross_libexecdir}/awk
rm -rf %{buildroot}%{_cross_datadir}/awk
rm -rf %{buildroot}%{_cross_libdir}/gawk
rm -rf %{buildroot}%{_cross_includedir}
rm -rf %{buildroot}%{_cross_datadir}/locale
rm -rf %{buildroot}%{_cross_mandir}
rm -rf %{buildroot}%{_cross_infodir}

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/gawk
%{_cross_bindir}/awk

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 5.4.2-1
- Initial package for gawk 5.4.2
