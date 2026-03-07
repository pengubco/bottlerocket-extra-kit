Name:    %{_cross_os}openssh
Version: 10.0p1
Release: 1%{?dist}
Summary: OpenSSH SSH daemon and client utilities
License: BSD-2-Clause AND BSD-3-Clause
URL:     https://www.openssh.com/

Source0: https://cdn.openbsd.org/pub/OpenBSD/OpenSSH/portable/openssh-%{version}.tar.gz
Source1: sshd.service

Patch0001: 0001-xcrypt-guard-crypt-call-with-HAVE_CRYPT.patch

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libcrypto-devel
BuildRequires: %{_cross_os}libssl-devel
BuildRequires: %{_cross_os}libz-devel

%description
%{summary}.

%prep
%setup -q -n openssh-%{version}
%patch -P 1 -p1

%build
%cross_configure \
    --sysconfdir=%{_cross_sysconfdir}/ssh \
    --with-privsep-path=%{_cross_localstatedir}/empty/sshd \
    --with-default-path=%{_cross_bindir} \
    --with-superuser-path=%{_cross_sbindir}:%{_cross_bindir} \
    --with-ssl-engine \
    --disable-strip \
    --without-pam \
    --without-kerberos5

%make_build

%install
%make_install

# Install systemd service unit
install -d %{buildroot}%{_cross_unitdir}
install -p -m 0644 %{S:1} %{buildroot}%{_cross_unitdir}/sshd.service

# Create privilege separation directory
install -d -m 0755 %{buildroot}%{_cross_localstatedir}/empty/sshd

# Remove unused files
rm -rf %{buildroot}%{_cross_mandir}

%files
%license LICENCE
%{_cross_attribution_file}
%{_cross_sbindir}/sshd
%{_cross_bindir}/ssh
%{_cross_bindir}/ssh-keygen
%{_cross_bindir}/ssh-keyscan
%{_cross_bindir}/ssh-add
%{_cross_bindir}/ssh-agent
%{_cross_bindir}/scp
%{_cross_bindir}/sftp
%{_cross_libexecdir}/sftp-server
%{_cross_libexecdir}/ssh-keysign
%{_cross_libexecdir}/ssh-pkcs11-helper
%{_cross_libexecdir}/ssh-sk-helper
%{_cross_libexecdir}/sshd-auth
%{_cross_libexecdir}/sshd-session
%dir %{_cross_sysconfdir}/ssh
%config(noreplace) %{_cross_sysconfdir}/ssh/moduli
%config(noreplace) %{_cross_sysconfdir}/ssh/ssh_config
%config(noreplace) %{_cross_sysconfdir}/ssh/sshd_config
%dir %{_cross_localstatedir}/empty/sshd
%{_cross_unitdir}/sshd.service

%changelog
* Fri Mar 06 2026 Bottlerocket Team <bottlerocket@amazon.com> - 10.0p1-1
- Initial package for OpenSSH 10.0p1
