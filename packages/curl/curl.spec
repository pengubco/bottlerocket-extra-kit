# Adapted from 
# 1. https://github.com/vigh-m/debug-kit/tree/develop/packages/curl
# 2. https://src.fedoraproject.org/rpms/curl/blob/rawhide/f/curl.spec

Name: %{_cross_os}curl
Version: 8.12.1
Release: 1%{dist}
Summary: A utility for getting files from remote servers (FTP, HTTP, and others)
License: curl
URL: https://curl.se

Source0: https://curl.se/download/curl-%{version}.tar.gz

%description
%{summary}

%prep
%autosetup -n curl-%{version} -p1

%build
autoreconf -fiv
%set_cross_build_flags
%cross_configure \
    --enable-optimize               \
    --disable-httpsrr               \
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
    --disable-tls-srp               \
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
    --without-brotli                \
    --without-libpsl                \
    --without-ssl                   \
    --without-zlib                  \
    --without-ca-bundle             \
    --without-ca-path               \
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
