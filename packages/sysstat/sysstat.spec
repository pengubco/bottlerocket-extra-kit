Summary: Collection of performance monitoring tools for Linux
Name: %{_cross_os}sysstat
Version: 12.7.7
Release: 1%{?dist}
License: GPL-2.0-or-later
 
URL: https://github.com/sysstat/sysstat
Source0: https://github.com/sysstat/sysstat/archive/v%{version}.tar.gz
 
BuildRequires: gcc
BuildRequires: gettext
BuildRequires: git
BuildRequires: make
BuildRequires: systemd-rpm-macros
 
Requires: %{_cross_os}findutils
 
%description
%{summary}.
 
%prep
%autosetup -n sysstat-%{version} -p1

%build
%cross_configure \
    --enable-install-cron \
    --enable-copy-only \
    --disable-file-attr \
    --disable-stripping \
    --with-systemdsystemunitdir='%{_cross_unitdir}' \
    --with-systemdsleepdir='%{_cross_unitdir}-sleep' \
    sadc_options='-S DISK' \
    history=28 \
    compressafter=31
%make_build

%install
%make_install
%find_lang sysstat 
 
%files -f sysstat.lang
%{_cross_sysconfdir}/sysconfig/sysstat
%{_cross_sysconfdir}/sysconfig/sysstat.ioconf
%license COPYING
%doc CHANGES CREDITS FAQ.md README.md
%{_cross_bindir}/cifsiostat
%{_cross_bindir}/iostat
%{_cross_bindir}/mpstat
%{_cross_bindir}/pidstat
%{_cross_bindir}/sadf
%{_cross_bindir}/sar
%{_cross_bindir}/tapestat
%{_cross_libdir}/sa
%{_cross_localstatedir}/log/sa
%{_cross_unitdir}/sysstat*
%{_cross_unitdir}-sleep/sysstat.sleep
%exclude %{_cross_docdir}/*
%exclude %{_cross_mandir}/*
%{_cross_attribution_file}