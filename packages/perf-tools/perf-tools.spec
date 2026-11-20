# Upstream has no releases; package a pinned commit snapshot.
%global commit cb42511b963a8dd2d8fcca400174c8d5d33a1f37
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global commitdate 20200114

# Install the scripts under libexec, and expose them in the bindir with an
# "ft-" prefix, so they never collide with same-named tools from bcc or
# libbpf-tools (execsnoop, opensnoop, ...).
%global ptdir %{_cross_libexecdir}/perf-tools

# Tools shipped. net/tcpretrans is left out because it is written in Perl,
# which Bottlerocket does not ship. The rest are bash + gawk (plus perf for
# bitesize, perf-stat-hist and syscount, and objdump for uprobe).
%global tools bitesize cachestat execsnoop funccount funcgraph funcslower functrace iolatency iosnoop killsnoop kprobe opensnoop perf-stat-hist reset-ftrace syscount tpoint uprobe

Name:    %{_cross_os}perf-tools
Version: 0^%{commitdate}git%{shortcommit}
Release: 1%{?dist}
Summary: Ftrace and perf_events based performance analysis tools
License: GPL-2.0-only
URL:     https://github.com/brendangregg/perf-tools

Source0: https://github.com/brendangregg/perf-tools/archive/%{commit}/perf-tools-%{commit}.tar.gz

# Prefer tracefs at /sys/kernel/tracing over the debugfs path, and replace the
# only sed use (indenting dmesg output on errors) with awk.
Patch0001: 0001-prefer-tracefs-and-avoid-sed.patch

Requires: %{_cross_os}bash
Requires: %{_cross_os}gawk

%description
%{summary}.

%prep
%autosetup -n perf-tools-%{commit} -p1

%build

%install
install -d %{buildroot}%{ptdir}
install -d %{buildroot}%{_cross_bindir}
for t in %{tools}; do
  # bin/ holds relative symlinks into the category directories.
  install -p -m 0755 "$(readlink -f "bin/${t}")" %{buildroot}%{ptdir}/${t}
  ln -s ../libexec/perf-tools/${t} %{buildroot}%{_cross_bindir}/ft-${t}
done

%files
%license LICENSE
%{_cross_attribution_file}
%dir %{ptdir}
%{ptdir}/*
%{_cross_bindir}/ft-*

%changelog
* Fri Nov 20 2026 Bottlerocket Team <bottlerocket@amazon.com> - 0^20200114gitcb42511-1
- Initial package for perf-tools snapshot cb42511
