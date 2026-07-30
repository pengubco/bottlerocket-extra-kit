Name:    %{_cross_os}logrotate
Version: 3.22.0
Release: 1%{?dist}
Summary: Rotates and maintains system log files
License: GPL-2.0-only
URL:     https://github.com/logrotate/logrotate

Source0: https://github.com/logrotate/logrotate/releases/download/%{version}/logrotate-%{version}.tar.xz
Source1: logrotate.conf
Source2: logrotate.service
Source3: logrotate.timer
Source4: logrotate-tmpfiles.conf

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libacl-devel
BuildRequires: %{_cross_os}libpopt-devel
BuildRequires: %{_cross_os}libselinux-devel

Requires: %{_cross_os}gzip
Requires: %{_cross_os}libacl
Requires: %{_cross_os}libpopt
Requires: %{_cross_os}libselinux

%description
%{summary}.

%prep
%setup -q -n logrotate-%{version}

%build
# The compress and state file paths are baked into the binary, so they have to
# be on-target paths rather than the sysroot-prefixed %%{_cross_*} build paths.
# Upstream defaults to /bin/gzip, which resolves via the /bin -> /usr/bin
# symlink, but pin it explicitly to match the gzip package.
%cross_configure \
    --with-acl \
    --with-selinux \
    --with-compress-command=/usr/bin/gzip \
    --with-uncompress-command=/usr/bin/gunzip \
    --with-state-file-path=/var/lib/logrotate/logrotate.status

%make_build

%install
%make_install

# /etc is a tmpfs on Bottlerocket, so ship the default config in the factory
# directory and let systemd-tmpfiles copy it into place on boot.
install -d %{buildroot}%{_cross_factorydir}%{_cross_sysconfdir}
install -p -m 0644 %{S:1} %{buildroot}%{_cross_factorydir}%{_cross_sysconfdir}/logrotate.conf

install -d %{buildroot}%{_cross_unitdir}
install -p -m 0644 %{S:2} %{buildroot}%{_cross_unitdir}/logrotate.service
install -p -m 0644 %{S:3} %{buildroot}%{_cross_unitdir}/logrotate.timer

install -d %{buildroot}%{_cross_tmpfilesdir}
install -p -m 0644 %{S:4} %{buildroot}%{_cross_tmpfilesdir}/logrotate.conf

# Remove man pages to keep the package lean
rm -rf %{buildroot}%{_cross_mandir}

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_sbindir}/logrotate
%{_cross_factorydir}%{_cross_sysconfdir}/logrotate.conf
%{_cross_unitdir}/logrotate.service
%{_cross_unitdir}/logrotate.timer
%{_cross_tmpfilesdir}/logrotate.conf

%changelog
* Thu Jul 30 2026 Bottlerocket Team <bottlerocket@amazon.com> - 3.22.0-1
- Initial package for logrotate 3.22.0
