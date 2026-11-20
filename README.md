# Bottlerocket Extra Kit
`bottlerocket-extra-kit` provides RPM packages not included in the [bottlerocket-kernel-kit](https://github.com/bottlerocket-os/bottlerocket-kernel-kit) or [bottlerocket-core-kit](https://github.com/bottlerocket-os/bottlerocket-core-kit) that you may find useful when building your own [Bottlerocket](https://github.com/bottlerocket-os) variant.

Some tools (noted in the [Tools That Work Best on the Host](#tools-that-work-best-on-the-host) section below) rely on host-level access to processes, kernel internals, or the native dynamic linker and will not work correctly from inside a container.

## Use RPM packages from the released kit
Take the [aws-dev](https://github.com/bottlerocket-os/bottlerocket/tree/develop/variants/aws-dev) variant as an example. 

Step 1. Add vendor and kit to the `{project-root}/Twoliter.toml`.
```toml
[vendor.peng]
registry = "public.ecr.aws/m8c0s8v8"

[[kit]]
name = "bottlerocket-extra-kit"
# Find the versions in Releases
version = "1.0.5"
vendor = "peng" 
```

You can build and publish the kit on your own. Just create an `Infra.toml` from [the template](Infra-template.toml).

Step 2. Add packages you need to the `included-packages` in `variants/aws-dev/Cargo.toml`. See [available packages](#packages).
```plain
awscli2
diffutils
sysstat
vim
curl
nerdctl
permissive-selinux
```

Step 3. Build the Bottlerocket image and AMI as usual.

## bottlerocket-core-kit and bottlerocket-sdk
When building a Bottlerocket image, the bottlerocket-kernel-kit, bottlerocket-core-kit, and bottlerocket-sdk must be the same version across all kits. Otherwise, you may see errors like:
```plain
Error: cannot have multiple versions of the same kit (bottlerocket-core-kit-9.2.1@bottlerocket != bottlerocket-core-kit-9.2.0@bottlerocket)
```

The extra-kit always builds against the latest core-kit, kernel-kit, and SDK at the time of release. The release version is just the extra-kit's own semver (e.g. `1.0.5`). To find which core-kit, kernel-kit, and SDK a given release was built with, check the `Twoliter.toml` at that release tag.

If you need to build with a different core-kit and SDK version, please check out the repository and update the `Twoliter.toml`.

## Build and publish this kit 

Generate `Twoliter.toml` using the latest core-kit, kernel-kit, and SDK versions from GitHub (default):
```
make generate-twoliter-toml RELEASE_VERSION=1.0.5
```

Pin to the same versions used in an existing `Twoliter.toml`:
```
make generate-twoliter-toml RELEASE_VERSION=1.0.5 TWOLITER_SOURCE=/path/to/Twoliter.toml
```

Pin explicit versions:
```
make generate-twoliter-toml RELEASE_VERSION=1.0.5 \
  CORE_KIT_VERSION=15.0.0 KERNEL_KIT_VERSION=7.3.0 SDK_VERSION=0.77.0
```

To build a single package without rebuilding the entire kit:
```
make build-package PACKAGE=awscli2
```

Then build and publish:
```
make build-and-publish VENDOR=xxx
```

This builds the kit for both `x86_64` and `aarch64` (the SDK cross-compiles, so one x86 host is enough) and publishes them as a single multi-arch image. Limit the architectures with `ARCHES`, e.g. `make build-and-publish VENDOR=xxx ARCHES=x86_64`. To build every architecture without publishing, run `make build-all-arches`.

## Cutting a release

`make release-github` cuts a release end to end:
```
make release-github RELEASE_VERSION=1.0.6
make release-github RELEASE_VERSION=1.0.6 RELEASE_ARGS="--latest --draft"
```

It runs `scripts/release.sh`, which:
1. Checks that the tree is clean, `gh` is logged in, `Infra.toml` exists, and the tag `vX.Y.Z` does not exist yet.
2. Bumps `release-version` in `Twoliter.toml` and `RELEASE_VERSION` in the Makefile, refreshes `Twoliter.lock`, and commits.
3. Builds the kit for each architecture in `ARCHES`.
4. Publishes the kit and, if `crane` is installed, checks that the image index has every architecture.
5. Pushes the commit and the annotated tag, then creates the GitHub release. The release notes list the usage snippet, the pinned core-kit, kernel-kit and SDK versions, the packages, and the commits since the previous tag.

The tag is created only after publishing succeeds, so a failed build never leaves behind a tag without an artifact.

Flags (pass them via `RELEASE_ARGS`):
- `--latest` — bump core-kit, kernel-kit and SDK to the latest upstream first. By default the current pins are kept.
- `--draft` — create the GitHub release as a draft.
- `--attach-archives` — upload the per-architecture kit tarballs (~160 MB each) as release assets.
- `--skip-build` — reuse archives already built for the current commit.

## Automated daily builds

`scripts/daily-build.sh` checks for upstream kernel-kit, core-kit, or SDK updates and rebuilds the kit when any version changes. If nothing changed, it logs and exits.

Run it through make:
```
make daily-build
make daily-build DAILY_BUILD_ARGS=--dry-run
```

Or call the script directly:
```
VENDOR=peng REGISTRY=public.ecr.aws/m8c0s8v8 ./scripts/daily-build.sh --force
```

Flags:
- `--force` — rebuild and publish even when Twoliter.toml already has the latest versions.
- `--dry-run` — show what would change without acting.

Environment variables:
- `VENDOR` — ECR vendor alias for publishing (default: `peng`). Set empty to skip publish.
- `REGISTRY` — OCI registry URL (e.g. `public.ecr.aws/m8c0s8v8`). Required for publishing unless `Infra.toml` already exists.
- `PUBLISH_REGIONS` — Comma-separated AWS regions (default: `us-west-2`).
- `RELEASE_VERSION` — Override the extra-kit release version (default: read from Makefile).
- `ARCHES` — Space-separated architectures to build (default: `x86_64 aarch64`). They are published as one multi-arch image.
- `LOG_FILE` — Log output path (default: `/tmp/extra-kit-daily-build.log`).
- `GITHUB_TOKEN` — Token for the GitHub API calls that resolve upstream versions. Unauthenticated requests are capped at 60/hour **per IP**, which a shared NAT address (such as a Cloud Desktop) exhausts easily. If unset, the script falls back to `gh auth token` when the gh CLI is logged in.

Progress and error messages go to stderr; they are also appended to `LOG_FILE`.

If `Infra.toml` does not exist and `VENDOR` is set, the script generates one from `REGISTRY` and `PUBLISH_REGIONS`. You can also create it manually from [Infra-template.toml](Infra-template.toml).

### Running from cron

```cron
0 6 * * * GITHUB_TOKEN=ghp_xxx REGISTRY=public.ecr.aws/m8c0s8v8 /path/to/bottlerocket-extra-kit/scripts/daily-build.sh
```

Set `GITHUB_TOKEN` explicitly for cron rather than relying on the `gh` fallback. cron runs with a minimal environment, so `gh` may not be on `PATH` even when it works in an interactive shell.

### Why publishing requires a clean tree

The kit version is derived from git, in twoliter's `Makefile.toml`:

```toml
BUILDSYS_VERSION_BUILD = { script = ["git describe --always --dirty --exclude '*' --abbrev=8 || echo 00000000"] }
```

That value lands in the archive filename and is also passed to `publish-kit` as `--build-id`. Two consequences:

- **Publishing from a dirty tree** would push an artifact tagged `-dirty`, which corresponds to no commit and cannot be reproduced from the repository. The script refuses to do this, with no override. Building dirty is fine and stays allowed — only the publish step is gated. To build without publishing, set `VENDOR=` (empty). When publishing is requested, the check runs *before* the build, so a dirty tree fails in under a second rather than after several minutes.
- **HEAD must not change between build and publish.** If it does, publish computes a different expected filename and fails with `No kit archive(s) exist at path ...`. This is why the script commits the pin bump *before* building, not after.

## Tools That Work Best on the Host

Some tools in this kit work correctly only when run natively on the Bottlerocket host, not from inside a container. There are two main reasons for this.

**Process-aware tools** — tools like `pldd` attach to running processes via `/proc/<pid>/maps` or ptrace. They need to see the host's process namespace and require `SYS_PTRACE` capability. Running them from a sidecar container against host processes is unreliable and often blocked by the container's security profile.

**Dynamic linker tools** — `ldd` works by invoking the ELF interpreter embedded in the target binary (`LD_TRACE_LOADED_OBJECTS=1`). When run from a container against a binary on a mounted host volume, it uses the container's dynamic linker and library paths, not the host's — so the dependency output will be wrong. Running `ldd` natively on the host ensures it resolves libraries against the correct sysroot. If you only need to inspect `NEEDED` entries statically (without executing the binary), `readelf -d` or `objdump -p` from `binutils` work correctly from any context.

**Performance and tracing tools** — eBPF, hardware performance counters, and kernel tracing require elevated capabilities (`CAP_BPF`, `CAP_PERFMON`, `CAP_SYS_ADMIN`) and access to kernel internals that are typically restricted inside containers. Running on the host gives full visibility across all processes and kernel subsystems.

The following packages are designed for or work best at the host level:

- **glibc-utils** (`ldd`, `pldd`) — `ldd` resolves shared library dependencies by executing the target binary's ELF interpreter; must run natively for correct results. `pldd` lists shared libraries loaded into a running process via `/proc`; requires host process namespace access.
- **perf** — Linux kernel performance counters. Requires `CAP_PERFMON` (or `CAP_SYS_ADMIN` on older kernels) and access to perf events, which are often restricted in containers.
- **perfrun** — Convenience wrapper around `perf` for common workflows (record, flamegraph, stat, top). Depends on `perf`.
- **perf-tools** (`ft-execsnoop`, `ft-iosnoop`, `ft-funccount`, `ft-kprobe`, etc.) — ftrace-based shell tools. Must run as root on the host with tracefs mounted at `/sys/kernel/tracing` (or debugfs at `/sys/kernel/debug/tracing`).
- **bpftrace** — High-level eBPF tracing language. Requires `CAP_BPF` + `CAP_PERFMON` and access to kernel BTF/debug info.
- **libbpf-tools** (`bpf-biolatency`, `bpf-runqlat`, `bpf-execsnoop`, etc.) — Prebuilt eBPF CO-RE tools. Require `CAP_BPF` + `CAP_PERFMON` (or `CAP_SYS_ADMIN`) and kernel BTF at `/sys/kernel/btf/vmlinux`.
- **sysstat** (`sar`, `iostat`, `mpstat`, etc.) — System-wide I/O, CPU, and memory statistics. Most useful at the host level for whole-node visibility.

## Packages
- [awscli2](https://aws.amazon.com/cli/) v2.27.0 - AWS CLI version 2
- [binutils](https://www.gnu.org/software/binutils/) v2.44 - Binary utilities: `as`, `ld`, `objdump`, `nm`, `strip`, `readelf`, and more
- [bpftool](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/bpf/bpftool) v6.1.159 - Inspect and manage eBPF programs, maps, links and BTF (`bpftool` v7.1.0, built from the kernel 6.1.159 tree). Built without BPF skeletons, so `prog profile` and the PID columns of `prog/map show` are unavailable; JIT disassembly (`prog dump jited`) is unavailable too. Needs `CAP_SYS_ADMIN` (or `CAP_BPF` + `CAP_PERFMON`).
- [blktrace](https://git.kernel.org/pub/scm/linux/kernel/git/axboe/blktrace.git) v1.3.0 - Block layer IO tracing: `blktrace`, `blkparse`, `btt`, `blkiomon`, and the `btrace` wrapper. Needs debugfs mounted at `/sys/kernel/debug`.
- [bpftrace](https://github.com/bpftrace/bpftrace) v0.24.2 - High-level tracing language for Linux eBPF. Pre-built static binary (x86_64 only).
- [cpupower](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/power/cpupower) v6.1.159 - Show and set CPU frequency governors/limits and idle states (`cpupower frequency-info`, `frequency-set`, `idle-info`, `idle-set`, `monitor`), built from the kernel 6.1.159 tree. Changing settings needs root and a writable `/sys`; on most cloud VMs there is no cpufreq driver, so only idle-state info is reported.
- [curl](https://curl.se) v8.12.1
- [diffutils](https://www.gnu.org/software/diffutils/) v3.12 - GNU diff utilities: `diff`, `diff3`, `cmp`, `sdiff`
- [file](https://www.darwinsys.com/file/) v5.46 - Determine file type (`file` command)
- [gawk](https://www.gnu.org/software/gawk/) v5.4.2 - GNU awk: `gawk` and `awk`. The core kit ships no awk, so scripts that pipe through awk (such as `perf-tools`) need this.
- [fio](https://github.com/axboe/fio) v3.43 - Flexible I/O tester for storage benchmarking (`fio`). Built with the `libaio`, `io_uring` and synchronous engines; network/cluster engines (rbd, gfapi, rdma, http, nfs) and the python/gnuplot helper scripts are not included. `fio --server` opens a listening socket (port 8765) and should only be started deliberately.
- [glibc-utils](https://www.gnu.org/software/libc/) v2.42 - GNU C Library utilities: `ldd` (list dynamic dependencies) and `pldd` (list shared libraries of a running process).
- [golang](https://go.dev) v1.26.1 - The Go programming language toolchain. Note: `/tmp` is mounted `noexec` on Bottlerocket; set `GOCACHE`, `GOTMPDIR`, and `GOPATH` to a writable path such as `/local` before running `go build` or `go run`.
- [iperf3](https://github.com/esnet/iperf) v3.22.1 - Network throughput measurement tool (`iperf3`). Built without RSA authentication and SCTP. `iperf3 -s` opens a listening port (5201 by default) that accepts tests from any client that can reach it; only run the server deliberately, bind it with `-B <addr>`, use `-1` to exit after one test, and stop it when done.
- [gzip](https://www.gnu.org/software/gzip/) v1.14 - GNU compression utility: `gzip`, `gunzip`, `zcat`, `zgrep`. The core kit ships only `unpigz`, which cannot compress, so this fills the gap.
- [iotop-c](https://github.com/Tomas-M/iotop) v1.33 - Top-like per-process I/O monitor (`iotop`), the C rewrite of iotop. Needs root or `CAP_NET_ADMIN` (taskstats netlink); enable `sysctl kernel.task_delayacct=1` for the SWAPIN/IO% columns.
- [htop](https://github.com/htop-dev/htop) v3.5.3 - Interactive process viewer (`htop`), built against the core kit's wide-character ncurses with Unicode and Linux capabilities support
- [jsoncpp](https://github.com/open-source-parsers/jsoncpp) v1.9.6
- [libbpf-tools](https://github.com/iovisor/bcc/tree/master/libbpf-tools) v0.37.0 - BPF CO-RE tracing tools from bcc (`bpf-biolatency`, `bpf-runqlat`, `bpf-offcputime`, `bpf-profile`, `bpf-execsnoop`, `bpf-opensnoop`, `bpf-tcpconnect`, and more), installed with a `bpf-` prefix. No python or compiler needed; requires kernel BTF.
- [libtraceevent](https://git.kernel.org/pub/scm/libs/libtrace/libtraceevent.git/) v1.9.1 - Library for parsing raw kernel trace event formats, plus its event-format plugins. Used by `trace-cmd`.
- [libtracefs](https://git.kernel.org/pub/scm/libs/libtrace/libtracefs.git/) v1.8.4 - Library for accessing the kernel tracefs file system. Used by `trace-cmd`.
- [libpcap](https://www.tcpdump.org/) v1.11.0 - Packet capture library used by `tcpdump`. Built with only the Linux socket and netfilter backends (no D-Bus, Bluetooth, RDMA, USB, netmap, or remote capture). Includes a `-devel` subpackage.
- [logrotate](https://github.com/logrotate/logrotate) v3.22.0 - Rotates and maintains log files. Ships a default `/etc/logrotate.conf` plus a `logrotate.timer` that runs daily; drop additional rules into `/etc/logrotate.d`. Pulls in `gzip` so `compress` works out of the box.
- [lsof](https://github.com/lsof-org/lsof) v4.99.7 - List open files, sockets and pipes per process (`lsof`), with SELinux context (`-Z`) support
- [nerdctl](https://github.com/containerd/nerdctl) v2.1.6 - Docker-compatible CLI for containerd
- [numactl](https://github.com/numactl/numactl) v2.0.19 - NUMA policy control: `numactl`, `numastat`, `migratepages`, `memhog`, plus the `libnuma` shared library
- [oomd](https://github.com/facebookincubator/oomd) v0.5.0
- [openssh](https://www.openssh.com/) v10.0p1 - OpenSSH daemon (`sshd`) and client utilities (`ssh`, `scp`, `sftp`, `ssh-keygen`)
- [pcm](https://github.com/intel/pcm) v202604 - Intel Performance Counter Monitor: `pcm`, `pcm-memory`, `pcm-pcie`, `pcm-iio`, `pcm-numa`, `pcm-power`, `pcm-latency`, `pcm-core`, `pcm-raw`, and more (x86_64 only, Intel CPUs). Run as root; needs the `msr` kernel module (`/dev/cpu/*/msr`) and `perf_event` access. `pcm-sensor-server` (HTTP exporter) is not included.
- [perf](https://perf.wiki.kernel.org/) v6.1.159 - Linux kernel performance analysis tool.
- [perf-tools](https://github.com/brendangregg/perf-tools) snapshot cb42511 (2020-01-14) - Brendan Gregg's ftrace/perf_events shell tools: `bitesize`, `cachestat`, `execsnoop`, `funccount`, `funcgraph`, `funcslower`, `functrace`, `iolatency`, `iosnoop`, `killsnoop`, `kprobe`, `opensnoop`, `perf-stat-hist`, `reset-ftrace`, `syscount`, `tpoint`, `uprobe`. Upstream has no releases, so this pins a commit. The scripts live in `/usr/libexec/perf-tools` under their upstream names, and each is linked into `/usr/bin` with an `ft-` prefix (for example `ft-execsnoop`) so they never clash with same-named bcc/libbpf-tools commands; add `/usr/libexec/perf-tools` to `PATH` to use the upstream names. `tcpretrans` is omitted because it needs Perl. Pulls in `gawk`; `bitesize`, `perf-stat-hist` and `syscount` also need `perf`, and `uprobe` needs `objdump` from `binutils`.
- [perfrun](https://www.kernel.org/) v0.1.0 - Convenience wrapper for common `perf` workflows: `record`, `flamegraph`, `stat`, `top`. Installed automatically with `perf`.
- [permissive-selinux] - Set SELinux mode to permissive. Useful for debugging/developing while bypassing SELinux denials (e.g., running shell scripts)
- [procps-ng](https://gitlab.com/procps-ng/procps) - Process monitoring utilities: `ps`, `top`, `free`, `vmstat`, `pgrep`, `pkill`, and more
- [stress-ng](https://github.com/ColinIanKing/stress-ng) v0.22.02 - Stress test CPU, cache, memory, I/O, filesystem and kernel interfaces (`stress-ng`). Built against glibc only; stressors that need optional libraries (zlib, libaio, libacl, libsctp, libkmod, ...) report as not implemented.
- [sysstat](https://github.com/sysstat/sysstat) v12.7.7 - Commands: sar, sadf, iostat, mpstat, pidstat, tapestat, cifsiostat.
- [tar](https://www.gnu.org/software/tar/) v1.35 - GNU tar archiving utility
- [trace-cmd](https://git.kernel.org/pub/scm/utils/trace-cmd/trace-cmd.git/) v3.4 - Command-line front end for the kernel ftrace tracer: `trace-cmd record`, `report`, `list`, `stat`, and more. Pulls in `libtraceevent` and `libtracefs`. Run as root with `/sys/kernel/tracing` (tracefs) accessible, e.g. from the admin container via `sheltie`.
- [tcpdump](https://www.tcpdump.org/) v4.99.7 - Command-line packet analyzer (`tcpdump`). Pulls in `libpcap`. Built without a default privilege-drop user (Bottlerocket has no `tcpdump` account), so it keeps running as the invoking user, normally root; pass `-Z <user>` to drop privileges explicitly. Linked against the host `libcrypto`, so ESP decryption (`-E`) works.
- [tree](https://oldmanprogrammer.net/source.php?dir=projects/tree) v2.3.2 - List directory contents as an indented tree (`tree`)
- [turbostat](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/tools/power/x86/turbostat) v6.1.159 - Report per-CPU frequency, C-state residency, temperature and RAPL power on x86 (`turbostat` 2022.10.04, built from the kernel 6.1.159 tree). x86_64 only. Run as root (needs `CAP_SYS_RAWIO` for `/dev/cpu/*/msr`); most counters are unavailable inside VMs that do not expose MSRs.
- [vim](https://github.com/vim/vim) v9.1.0
- [which](https://savannah.gnu.org/projects/which/) v2.23 - Show full path of shell commands
- [libcap-utils](https://sites.google.com/site/fullycapable/) v2.77 - POSIX capabilities utilities: `getcap`, `setcap`, `capsh`, `getpcaps`
