Name:    %{_cross_os}pcm
Version: 202604
Release: 1%{?dist}
Summary: Intel Performance Counter Monitor
License: BSD-3-Clause
URL:     https://github.com/intel/pcm

Source0: pcm-%{version}.tar.gz

BuildRequires: cmake
BuildRequires: %{_cross_os}glibc-devel

Requires: %{_cross_os}libstdc++

%description
Intel Performance Counter Monitor (Intel PCM) provides tools to monitor
core, memory, PCIe, IIO, NUMA, power and latency metrics of Intel
processors via model-specific registers, uncore PMUs and perf_event.

%prep
%autosetup -n pcm-%{version} -p1

# Do not build:
#  - pcm-sensor-server: an HTTP(S) exporter that opens a listening socket
#    and wants OpenSSL; not appropriate for a host tool package.
#  - pcm-sensor: a KSysGuard sensor backend, useless without KDE.
#  - examples/ and tests/: not shipped.
sed -i -e '/^set(PROJECT_NAMES /s/ pcm-sensor-server)/)/' \
       -e '/list(APPEND PROJECT_NAMES pcm-sensor)/d' src/CMakeLists.txt
sed -i -e '/add_subdirectory(examples)/d' \
       -e '/add_subdirectory(tests)/d' CMakeLists.txt
# Let rpmbuild strip the binaries and extract debuginfo instead of passing
# "-s" to the linker.
sed -i -e 's/ -s")  # --strip-unneeded for packaging/")/' src/CMakeLists.txt

%build
%write_cross_cmake_toolchain_conf
# PCM bakes CMAKE_INSTALL_PREFIX into the binaries to locate its data files
# (e.g. %{_datadir}/pcm/opCode-*.txt for pcm-iio), so configure with the
# runtime prefix and install into the sysroot via DESTDIR instead of using
# the sysroot prefix from the toolchain file.
sed -i -e '/^set(CMAKE_INSTALL_PREFIX /d' %{_cross_cmake_toolchain_conf}

# The git submodules (simdjson, pugixml, perfmon, Intel-PMT) are not in the
# release tarball and are all optional: without them pcm-raw accepts only
# raw event encodings (no perfmon JSON event names) and the Intel PMT XML
# telemetry database is unavailable. The other tools are unaffected.
cmake -S . -B build \
    -DCMAKE_TOOLCHAIN_FILE=%{_cross_cmake_toolchain_conf} \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_EXE_LINKER_FLAGS="%{_cross_ldflags}" \
    -DPCM_NO_ASAN=ON \
    -DNO_SSL=ON \
    -DLINUX_SYSTEMD=OFF
%make_build -C build

%install
DESTDIR=%{buildroot}%{_cross_rootdir} cmake --install build

# pcm-daemon/pcm-client (shared-memory exporter) and the bash
# pcm-bw-histogram helper are not shipped; Bottlerocket has no bash on the
# host. Upstream docs are dropped and the license files are shipped via
# %%license instead of upstream's own copies.
rm -f %{buildroot}%{_cross_sbindir}/pcm-daemon \
      %{buildroot}%{_cross_bindir}/pcm-client \
      %{buildroot}%{_cross_sbindir}/pcm-bw-histogram
rm -rf %{buildroot}%{_cross_docdir} \
       %{buildroot}%{_cross_licensedir}/pcm \
       %{buildroot}%{_cross_datadir}/pcm/perfmon

%files
%license LICENSE third-party-software.txt
%{_cross_attribution_file}
%{_cross_sbindir}/pcm
%{_cross_sbindir}/pcm-accel
%{_cross_sbindir}/pcm-core
%{_cross_sbindir}/pcm-iio
%{_cross_sbindir}/pcm-latency
%{_cross_sbindir}/pcm-memory
%{_cross_sbindir}/pcm-mmio
%{_cross_sbindir}/pcm-msr
%{_cross_sbindir}/pcm-numa
%{_cross_sbindir}/pcm-pcicfg
%{_cross_sbindir}/pcm-pcie
%{_cross_sbindir}/pcm-power
%{_cross_sbindir}/pcm-raw
%{_cross_sbindir}/pcm-tpmi
%{_cross_sbindir}/pcm-tsx
%dir %{_cross_datadir}/pcm
%{_cross_datadir}/pcm/opCode-*.txt
%{_cross_datadir}/pcm/PMURegisterDeclarations
%exclude %{_cross_datadir}/pcm/third-party-software.txt

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 202604-1
- Initial package for Intel PCM 202604
