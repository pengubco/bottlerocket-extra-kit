Name: %{_cross_os}libpcap
Version: 1.11.0
Release: 1%{?dist}
Summary: A system-independent interface for user-level packet capture
License: BSD-3-Clause
URL: https://www.tcpdump.org/

Source0: https://www.tcpdump.org/release/libpcap-%{version}.tar.xz

BuildRequires: %{_cross_os}glibc-devel
BuildRequires: bison
BuildRequires: flex

%description
%{summary}.

%package devel
Summary: Files for development using the libpcap library
Requires: %{name}

%description devel
%{summary}.

%prep
%autosetup -n libpcap-%{version} -p1

%build
# Keep the library minimal: only plain Linux socket capture (plus the
# netfilter/NFLOG pseudo-devices, which need no extra libraries). The
# optional D-Bus, Bluetooth, RDMA, USB, netmap and remote-capture backends
# would each pull in more libraries or are not useful on a container host.
# libnl is only used for creating wireless monitor-mode interfaces.
%cross_configure \
    --enable-shared \
    --disable-dbus \
    --disable-bluetooth \
    --disable-rdma \
    --disable-usb \
    --disable-netmap \
    --disable-remote \
    --without-libnl \
    --without-dag \
    --without-snf \
    --with-pcap=linux

%make_build

%install
%make_install

# Shared library only; drop the static archive and man pages.
rm -f %{buildroot}%{_cross_libdir}/libpcap.a
rm -rf %{buildroot}%{_cross_mandir}

# configure adds "-Wl,-rpath,${libdir}" to the link flags whenever the prefix
# is not /usr, which is always the case for the cross sysroot prefix. Strip
# it so consumers don't embed a sysroot RUNPATH.
sed -i 's|-Wl,-rpath,${libdir} *||' \
    %{buildroot}%{_cross_pkgconfigdir}/libpcap.pc \
    %{buildroot}%{_cross_bindir}/pcap-config

%files
%license LICENSE
%{_cross_attribution_file}
%{_cross_libdir}/libpcap.so.1
%{_cross_libdir}/libpcap.so.%{version}

%files devel
%{_cross_bindir}/pcap-config
%{_cross_libdir}/libpcap.so
%{_cross_includedir}/pcap.h
%{_cross_includedir}/pcap-bpf.h
%{_cross_includedir}/pcap-namedb.h
%dir %{_cross_includedir}/pcap
%{_cross_includedir}/pcap/*.h
%{_cross_pkgconfigdir}/libpcap.pc
