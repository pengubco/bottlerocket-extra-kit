Name:    %{_cross_os}stress-ng
Version: 0.22.02
Release: 1%{?dist}
Summary: Stress test a computer system in various selectable ways
License: GPL-2.0-or-later
URL:     https://github.com/ColinIanKing/stress-ng

Source0: stress-ng-%{version}.tar.gz

# glibc >= 2.42 no longer provides struct termio
Patch0001: 0001-stress-pty-drop-deprecated-TCGETA-ioctls.patch

BuildRequires: %{_cross_os}glibc-devel

%description
stress-ng stress tests a computer system in various selectable ways. It
exercises CPU, cache, memory, I/O, filesystem, scheduler and kernel
interfaces through more than 300 stressors.

%prep
%autosetup -n stress-ng-%{version} -p1

%build
# stress-ng has no autoconf; its Makefile.config probes the toolchain by
# compiling and linking small test programs. Pass the cross toolchain so the
# probes run against the Bottlerocket sysroot rather than the SDK host.
#
# Every optional external library is disabled by emptying its LIB_* variable,
# which makes Makefile.config skip the probe. Only glibc (libc, libm,
# libpthread, librt, libdl) is linked, so the binary has no runtime
# dependencies beyond glibc. The stressors that need the dropped libraries
# (e.g. zlib, acl, aio, sctp, kmod, crypt, Judy, jpeg, gmp/mpfr, libnl, EGL)
# report themselves as "not implemented" at runtime.
%make_build \
    CC="%{_cross_target}-gcc" \
    CXX="%{_cross_target}-g++" \
    OBJDUMP="%{_cross_target}-objdump" \
    READELF="%{_cross_target}-readelf" \
    CFLAGS="%{_cross_cflags}" \
    LDFLAGS="%{_cross_ldflags}" \
    LIB_ACL= LIB_AIO= LIB_APPARMOR= LIB_ATOMIC= LIB_BSD= LIB_CRYPT= \
    LIB_EGL= LIB_GBM= LIB_GLES2= LIB_GMP= LIB_IPSEC_MB= LIB_JPEG= \
    LIB_JUDY= LIB_KMOD= LIB_MD= LIB_MPFR= LIB_SCTP= LIB_XXHASH= LIB_Z= \
    LIB_LZMA= LIB_NL= LIB_GENL= \
    VERBOSE=1

%install
install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 stress-ng %{buildroot}%{_cross_bindir}/stress-ng

%files
%license COPYING
%{_cross_attribution_file}
%{_cross_bindir}/stress-ng

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 0.22.02-1
- Initial package for stress-ng 0.22.02
