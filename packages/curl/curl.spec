Name: %{_cross_os}curl
Version: 8.12.1
Release: 1%{dist}
Summary: A utility for getting files from remote servers (FTP, HTTP, and others)
License: curl
URL: https://curl.se

Source0: https://curl.se/download/curl-%{version}.tar.gz


BuildRequires: %{_cross_os}glibc-devel
BuildRequires: %{_cross_os}libblkid-devel
BuildRequires: %{_cross_os}libcrypto-devel
BuildRequires: %{_cross_os}libcrypto-devel
BuildRequires: %{_cross_os}libcrypto-tools
BuildRequires: %{_cross_os}libdevmapper-devel
BuildRequires: %{_cross_os}libjson-c-devel
BuildRequires: %{_cross_os}libpopt-devel
BuildRequires: %{_cross_os}libselinux-devel
BuildRequires: %{_cross_os}libssl-devel
BuildRequires: %{_cross_os}libuuid-devel
BuildRequires: openssl-devel
BuildRequires:%{_cross_os}libcrypto
Requires: %{_cross_os}libblkid
Requires: %{_cross_os}libblkid-devel
Requires: %{_cross_os}libcrypto
Requires: %{_cross_os}libcrypto-devel
Requires: %{_cross_os}libcrypto-tools
Requires: %{_cross_os}libdevmapper
Requires: %{_cross_os}libdevmapper-devel
Requires: %{_cross_os}libjson-c
Requires: %{_cross_os}libjson-c-devel
Requires: %{_cross_os}libselinux
Requires: %{_cross_os}libssl-devel
Requires: %{_cross_os}libuuid
Requires: %{_cross_os}libuuid-devel
Requires:%{_cross_os}libcrypto

%description
%{summary}

%prep
%autosetup -n curl-%{version} -p1

%build
autoreconf -fiv
%set_cross_build_flags
%cross_configure \
    --enable-optimize               \
    --disable-dict                  \
    --disable-gopher                \
    --disable-imap                  \
    --disable-ldap                  \
    --disable-ldaps                 \
    --disable-mqtt                  \
    --disable-ntlm                  \
    --disable-pop3                  \
    --disable-rtsp                  \
    --disable-smb                   \
    --disable-smtp                  \
    --disable-telnet                \
    --disable-tftp                  \
    --disable-websockets            \
    --disable-docs                  \
    --disable-largefile             \
    --disable-ftp                   \
    --disable-imap                  \
    --disable-libcurl-option        \
    --disable-openssl-auto-load-config  \
    --disable-mime                  \
    --disable-netrc                 \
    --enable-unix-sockets           \
    --with-openssl                  \
    --with-ca-bundle=%{_cross_sysconfdir}/pki/tls/certs/ca-bundle.crt \
    --without-brotli                \
    --without-libpsl                \
    --without-zlib                  \
    --without-ca-fallback           \
    --without-zsh-functions-dir     \
    --without-fish-functions-dir    \
    --without-libuv                 \
    --without-msh3                  \
    --without-openssl-quic          \
    --without-nghttp2               \
    --without-zstd                  \
    --without-libssh                \
    --without-libidn2

%force_disable_rpath
%make_build

%install
%make_install

%files
%{_cross_bindir}/curl
%{_cross_bindir}/curl-config
%{_cross_libdir}/libcurl.a
%{_cross_libdir}/libcurl.so
%{_cross_libdir}/libcurl.so.4
%{_cross_libdir}/libcurl.so.4.8.0
%{_cross_libdir}/pkgconfig/*.pc
%{_cross_includedir}/curl
%{_cross_datadir}/aclocal/libcurl.m4
%{_cross_attribution_file}

%changelog
