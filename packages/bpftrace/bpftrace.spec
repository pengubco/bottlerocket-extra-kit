%global debug_package %{nil}

Name:    %{_cross_os}bpftrace
Version: 0.24.2
Release: 1%{?dist}
Summary: High-level tracing language for Linux eBPF
License: Apache-2.0
URL:     https://github.com/bpftrace/bpftrace

# Pre-built static binary (upstream only provides x86_64)
Source0: https://github.com/bpftrace/bpftrace/releases/download/v%{version}/bpftrace

ExclusiveArch: x86_64

%description
%{summary}.

%prep
# Nothing to unpack — Source0 is the binary itself
cp %{S:0} bpftrace
chmod 0755 bpftrace

%build
%{nil}

%install
install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 bpftrace %{buildroot}%{_cross_bindir}/bpftrace

%files
%{_cross_attribution_file}
%{_cross_bindir}/bpftrace

%changelog
* Tue Mar 10 2026 Bottlerocket Team <bottlerocket@amazon.com> - 0.24.2-1
- Initial package for bpftrace 0.24.2 (pre-built static binary)
