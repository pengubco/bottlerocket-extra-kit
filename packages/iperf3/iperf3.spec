Name:    %{_cross_os}iperf3
Version: 3.22.1
Release: 1%{?dist}
Summary: Network bandwidth measurement tool
License: BSD-3-Clause AND MIT
URL:     https://github.com/esnet/iperf

Source0: https://downloads.es.net/pub/iperf/iperf-%{version}.tar.gz

BuildRequires: %{_cross_os}glibc-devel

%description
%{summary}.

%prep
%autosetup -n iperf-%{version} -p1

%build
# Link libiperf statically into the iperf3 binary so the package ships a single
# executable and no unversioned shared library. RSA authentication (OpenSSL)
# and SCTP (lksctp-tools) are disabled: neither is needed for throughput
# testing and keeping them out avoids extra runtime dependencies.
%cross_configure \
    --disable-shared \
    --enable-static \
    --without-openssl \
    --without-sctp
%make_build

%install
%make_install
# Only the iperf3 binary is shipped; drop the static library, header and man
# pages that "make install" adds.
rm -f %{buildroot}%{_cross_libdir}/libiperf.*
rm -f %{buildroot}%{_cross_includedir}/iperf_api.h
rm -rf %{buildroot}%{_cross_mandir}

%files
%license LICENSE
%{_cross_attribution_file}
%{_cross_bindir}/iperf3

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 3.22.1-1
- Initial package for iperf3 3.22.1
