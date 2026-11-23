#!/bin/bash
# smoke-test.sh — run on a Bottlerocket host built with this kit to check that
# each tool starts. It only runs harmless version/help/list commands.
#
# Run it as root in the host namespaces, e.g. from the admin container:
#   sudo sheltie
#   bash smoke-test.sh            # or: bash smoke-test.sh tcpdump fio
#
# A tool whose binary is missing is reported as SKIP (the variant may not
# include that package); a tool that is present but fails is reported as FAIL.
# Exit status is 1 if anything failed.
set -uo pipefail

# name|binary|command to run
CHECKS=(
  "awscli2|aws|aws --version"
  "binutils-tools|readelf|readelf --version"
  "blktrace|blkparse|blkparse --version"
  "bpftool|bpftool|bpftool version"
  "bpftrace|bpftrace|bpftrace --version"
  "cpupower|cpupower|cpupower --version"
  "curl|curl|curl --version"
  "diffutils|diff|diff --version"
  "file|file|file --version"
  "fio|fio|fio --version"
  "gawk|gawk|gawk --version"
  "glibc-utils|ldd|ldd --version"
  "golang|go|go version"
  "gzip|gzip|gzip --version"
  "htop|htop|htop --version"
  "iotop-c|iotop|iotop --version"
  "iperf3|iperf3|iperf3 --version"
  "libbpf-tools|bpf-runqlat|bpf-runqlat --help"
  "libcap-utils|capsh|capsh --print"
  "logrotate|logrotate|logrotate --version"
  "lsof|lsof|lsof -v"
  "nerdctl|nerdctl|nerdctl --version"
  "numactl|numactl|numactl --hardware"
  "openssh|ssh|ssh -V"
  "pcm|pcm|pcm --version"
  "perf|perf|perf --version"
  "perfrun|perfrun|perfrun --help"
  "perf-tools|ft-execsnoop|ft-execsnoop -h"
  "procps-ng|top|top -bn1"
  "procps-ng|watch|watch -v"
  "procps-ng|slabtop|slabtop -o"
  "stress-ng|stress-ng|stress-ng --version"
  "strace|strace|strace -V"
  "sysstat|iostat|iostat -V"
  "tar|tar|tar --version"
  "tcpdump|tcpdump|tcpdump --version"
  "trace-cmd|trace-cmd|trace-cmd list -t"
  "tree|tree|tree --version"
  "turbostat|turbostat|turbostat --version"
  "vim|vim|vim --version"
  "which|which|which --version"
)

pass=0 fail=0 skip=0
for check in "${CHECKS[@]}"; do
  IFS='|' read -r name bin cmd <<<"${check}"
  if [[ $# -gt 0 && ! " $* " == *" ${name} "* ]]; then
    continue
  fi
  if ! command -v "${bin}" >/dev/null 2>&1; then
    printf 'SKIP  %-14s (%s not installed)\n' "${name}" "${bin}"
    skip=$((skip + 1))
    continue
  fi
  # Several tools print usage and exit non-zero for -h/--help; accept any exit
  # status below 126 as long as the program actually ran and printed output.
  out="$(timeout 120 bash -c "${cmd}" 2>&1)"
  rc=$?
  if [[ ${rc} -lt 126 && -n "${out}" ]]; then
    printf 'PASS  %-14s %s\n' "${name}" "$(head -1 <<<"${out}" | cut -c1-70)"
    pass=$((pass + 1))
  else
    printf 'FAIL  %-14s rc=%s %s\n' "${name}" "${rc}" "$(head -3 <<<"${out}" | tr '\n' ' ' | cut -c1-120)"
    fail=$((fail + 1))
  fi
done

echo "passed=${pass} failed=${fail} skipped=${skip}"
[[ ${fail} -eq 0 ]]
