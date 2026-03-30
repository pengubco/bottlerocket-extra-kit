Name:    %{_cross_os}glibc-utils
Version: 2.42
Release: 1%{?dist}
Summary: Utilities from the GNU C Library (ldd, pldd)
License: LGPL-2.1-or-later AND GPL-2.0-or-later
URL:     http://www.gnu.org/software/glibc/

Source0: https://ftp.gnu.org/gnu/glibc/glibc-%{version}.tar.xz
Source1: https://ftp.gnu.org/gnu/glibc/glibc-%{version}.tar.xz.sig
Source2: gpgkey-35B17DF5752577CA0C541CEB94BFDF4484AD142F.asc

BuildRequires: %{_cross_os}glibc-devel

%description
%{summary}.

%prep
%{gpgverify} --data=%{S:0} --signature=%{S:1} --keyring=%{S:2}
%autosetup -n glibc-%{version} -p1

%build
mkdir build
pushd build
CC="%{_cross_target}-gcc %{?_cross_arch_cflags}" CXX="%{_cross_target}-g++ %{?_cross_arch_cflags}" \
BUILDFLAGS="-O2 -g1 -fstack-clash-protection -fno-omit-frame-pointer" \
CFLAGS="${BUILDFLAGS}" CPPFLAGS="" CXXFLAGS="${BUILDFLAGS}" \
../configure \
  --prefix="%{_cross_prefix}" \
  --sysconfdir="%{_cross_sysconfdir}" \
  --localstatedir="%{_cross_localstatedir}" \
  --target="%{_cross_target}" \
  --host="%{_cross_target}" \
  --build="%{_build}" \
  --with-headers="%{_cross_includedir}" \
  --enable-bind-now \
  --enable-shared \
  --disable-build-nscd \
  --disable-crypt \
  --disable-nscd \
  --disable-profile \
  --disable-systemtap \
  --disable-timezone-tools \
  --without-gd \
  --without-selinux \
  --enable-kernel="5.10.0"
make %{?_smp_mflags} -O -r
popd

%install
# Copy only ldd and pldd directly from the build output tree.
# ldd is a shell script generated in build/elf/; pldd is a compiled binary.
install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 build/elf/ldd %{buildroot}%{_cross_bindir}/ldd
install -p -m 0755 build/elf/pldd %{buildroot}%{_cross_bindir}/pldd

%files
%license COPYING COPYING.LIB LICENSES
%{_cross_attribution_file}
%{_cross_bindir}/ldd
%{_cross_bindir}/pldd

%changelog
* Sun Mar 29 2026 Bottlerocket Team <bottlerocket@amazon.com> - 2.42-1
- Initial package providing ldd and pldd from glibc 2.42
