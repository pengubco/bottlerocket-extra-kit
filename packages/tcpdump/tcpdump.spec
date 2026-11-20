Name: %{_cross_os}tcpdump
Version: 4.99.7
Release: 1%{?dist}
Summary: Command-line network packet analyzer
License: BSD-3-Clause
URL: https://www.tcpdump.org/

Source0: https://www.tcpdump.org/release/tcpdump-%{version}.tar.xz

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libcrypto-devel
BuildRequires: %{_cross_os}libpcap-devel

Requires: %{_cross_os}libcrypto
Requires: %{_cross_os}libpcap

%description
%{summary}.

%prep
%autosetup -n tcpdump-%{version} -p1

%build
# Upstream only drops privileges when built with --with-user; distros usually
# pass --with-user=tcpdump, but Bottlerocket has no "tcpdump" account, so
# leave it unset and tcpdump keeps running as the invoking user (root). Users
# can still opt in to dropping privileges with -Z <user>.
#
# libcrypto (already on every Bottlerocket host) enables ESP decryption (-E)
# and TCP-MD5 signature verification. libsmi and libcap-ng are not available.
%cross_configure \
    --disable-local-libpcap \
    --without-user \
    --without-chroot \
    --without-smi \
    --without-cap-ng \
    --with-crypto

%make_build

%install
%make_install

# Upstream also installs a versioned copy of the binary; ship just one.
rm -f %{buildroot}%{_cross_bindir}/tcpdump.%{version}
rm -rf %{buildroot}%{_cross_mandir}

%files
%license LICENSE
%{_cross_attribution_file}
%{_cross_bindir}/tcpdump
