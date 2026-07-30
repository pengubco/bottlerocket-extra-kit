Name:    %{_cross_os}gzip
Version: 1.14
Release: 1%{?dist}
Summary: GNU zip compression utility
License: GPL-3.0-or-later
URL:     https://www.gnu.org/software/gzip/

Source0: https://ftp.gnu.org/gnu/gzip/gzip-%{version}.tar.xz

BuildRequires: %{_cross_os}glibc-devel

# gunzip, zcat, and zgrep are /bin/sh scripts, and zgrep shells out to grep
Requires: %{_cross_os}bash
Requires: %{_cross_os}grep

%description
%{summary}.

%prep
%setup -q -n gzip-%{version}

%build
# GREP is baked into the zgrep script at build time, so pin it instead of
# letting configure record whatever the SDK container happens to detect. This
# has to be the on-target path, not %%{_cross_bindir}, which is the
# sysroot-prefixed build-time path.
%cross_configure \
    GREP=/usr/bin/grep

%make_build

%install
%make_install

# Remove locale files, man pages, and docs to keep the package lean
rm -rf %{buildroot}%{_cross_datadir}/locale
rm -rf %{buildroot}%{_cross_mandir}
rm -rf %{buildroot}%{_cross_infodir}

# Drop the helper scripts whose dependencies Bottlerocket does not ship:
# gzexe needs a writable /usr, zcmp/zdiff need cmp/diff, zegrep/zfgrep need
# egrep/fgrep (excluded from the grep package), and zless/zmore need a pager.
rm -f %{buildroot}%{_cross_bindir}/gzexe
rm -f %{buildroot}%{_cross_bindir}/zcmp
rm -f %{buildroot}%{_cross_bindir}/zdiff
rm -f %{buildroot}%{_cross_bindir}/zegrep
rm -f %{buildroot}%{_cross_bindir}/zfgrep
rm -f %{buildroot}%{_cross_bindir}/zforce
rm -f %{buildroot}%{_cross_bindir}/zless
rm -f %{buildroot}%{_cross_bindir}/zmore
rm -f %{buildroot}%{_cross_bindir}/znew

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/gzip
%{_cross_bindir}/gunzip
%{_cross_bindir}/uncompress
%{_cross_bindir}/zcat
%{_cross_bindir}/zgrep

%changelog
* Thu Jul 30 2026 Bottlerocket Team <bottlerocket@amazon.com> - 1.14-1
- Initial package for gzip 1.14
