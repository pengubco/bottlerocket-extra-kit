%global debug_package %{nil}
# The AppImage is an ELF runtime with a squashfs image appended. Stripping
# (brp-strip in __os_install_post) drops everything after the ELF sections,
# leaving a 1 MB stub that cannot run, so skip all post-install processing.
%global __os_install_post %{nil}

Name:    %{_cross_os}bpftrace
Version: 0.27.1
Release: 1%{?dist}
Summary: High-level tracing language for Linux eBPF
License: Apache-2.0
URL:     https://github.com/bpftrace/bpftrace

# Pre-built static binaries; upstream publishes one per architecture.
Source0: https://github.com/bpftrace/bpftrace/releases/download/v%{version}/bpftrace-x86_64
Source1: https://github.com/bpftrace/bpftrace/releases/download/v%{version}/bpftrace-aarch64
Source2: bpftrace-wrapper

Requires: %{_cross_os}bash

%description
%{summary}.

%prep
# Nothing to unpack: the sources are the binaries themselves.
cp %{_sourcedir}/bpftrace-%{_cross_arch} bpftrace
chmod 0755 bpftrace

%build
%{nil}

%install
install -d %{buildroot}%{_cross_libexecdir}/bpftrace %{buildroot}%{_cross_bindir}
install -p -m 0755 bpftrace %{buildroot}%{_cross_libexecdir}/bpftrace/bpftrace.AppImage
install -p -m 0755 %{S:2} %{buildroot}%{_cross_bindir}/bpftrace

%files
%{_cross_attribution_file}
%{_cross_bindir}/bpftrace
%dir %{_cross_libexecdir}/bpftrace
%{_cross_libexecdir}/bpftrace/bpftrace.AppImage

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 0.27.1-1
- Update to 0.27.1, which also publishes an aarch64 build
- Run the AppImage through a wrapper that extracts it into /var/cache/bpftrace,
  since Bottlerocket has no FUSE and mounts /tmp noexec

* Tue Mar 10 2026 Bottlerocket Team <bottlerocket@amazon.com> - 0.24.2-1
- Initial package for bpftrace 0.24.2 (pre-built static binary)
