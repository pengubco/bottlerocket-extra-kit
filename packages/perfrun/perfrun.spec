Name:    %{_cross_os}perfrun
Version: 0.1.0
Release: 1%{?dist}
Summary: Convenience wrapper scripts for Linux perf profiling
License: Apache-2.0
URL:     https://www.kernel.org/

%description
%{summary}.

%build
cat > perfrun <<'EOF'
#!/bin/sh
# perfrun - convenience wrapper for common perf profiling tasks
set -e

DURATION=${PERFRUN_DURATION:-30}
OUTPUT=${PERFRUN_OUTPUT:-/tmp/perf.data}

usage() {
    echo "Usage: perfrun <command> [options]"
    echo ""
    echo "Commands:"
    echo "  record [pid]     Record CPU profile (default: system-wide, ${DURATION}s)"
    echo "  flamegraph [pid] Record and generate flamegraph data"
    echo "  stat [pid]       Collect performance counter statistics"
    echo "  top              Live performance counter display"
    echo ""
    echo "Environment:"
    echo "  PERFRUN_DURATION  Recording duration in seconds (default: 30)"
    echo "  PERFRUN_OUTPUT    Output file path (default: /tmp/perf.data)"
    exit 1
}

[ $# -lt 1 ] && usage

CMD=$1
shift

case "$CMD" in
    record)
        if [ -n "$1" ]; then
            exec perf record -g -p "$1" -o "$OUTPUT" -- sleep "$DURATION"
        else
            exec perf record -g -a -o "$OUTPUT" -- sleep "$DURATION"
        fi
        ;;
    flamegraph)
        if [ -n "$1" ]; then
            perf record -g -F 99 -p "$1" -o "$OUTPUT" -- sleep "$DURATION"
        else
            perf record -g -F 99 -a -o "$OUTPUT" -- sleep "$DURATION"
        fi
        perf script -i "$OUTPUT"
        ;;
    stat)
        if [ -n "$1" ]; then
            exec perf stat -p "$1" -- sleep "$DURATION"
        else
            exec perf stat -a -- sleep "$DURATION"
        fi
        ;;
    top)
        exec perf top -g "$@"
        ;;
    *)
        usage
        ;;
esac
EOF

%install
install -d %{buildroot}%{_cross_bindir}
install -p -m 0755 perfrun %{buildroot}%{_cross_bindir}/perfrun

%files
%{_cross_attribution_file}
%{_cross_bindir}/perfrun

%changelog
* Tue Mar 10 2026 Bottlerocket Team <bottlerocket@amazon.com> - 0.1.0-1
- Initial package for perfrun perf wrapper script
