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
version = "1.0.4"
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

The extra-kit always builds against the latest core-kit, kernel-kit, and SDK at the time of release. The release version is just the extra-kit's own semver (e.g. `1.0.4`). To find which core-kit, kernel-kit, and SDK a given release was built with, check the `Twoliter.toml` at that release tag.

If you need to build with a different core-kit and SDK version, please check out the repository and update the `Twoliter.toml`.

## Build and publish this kit 

Generate `Twoliter.toml` using the latest core-kit, kernel-kit, and SDK versions from GitHub (default):
```
make generate-twoliter-toml RELEASE_VERSION=1.0.4
```

Pin to the same versions used in an existing `Twoliter.toml`:
```
make generate-twoliter-toml RELEASE_VERSION=1.0.4 TWOLITER_SOURCE=/path/to/Twoliter.toml
```

Or specify versions explicitly:
```
make generate-twoliter-toml RELEASE_VERSION=1.0.4 CORE_KIT_VERSION=13.0.0 KERNEL_KIT_VERSION=5.0.0 SDK_VERSION=0.70.0
```

You can mix and match — any version not specified will be fetched from GitHub. For example, pin only the SDK:
```
make generate-twoliter-toml RELEASE_VERSION=1.0.4 SDK_VERSION=0.70.0
```

To build a single package without rebuilding the entire kit:
```
make build-package PACKAGE=awscli2
```

Then build and publish:
```
make build-and-publish VENDOR=xxx
```

## Automated daily builds

`scripts/daily-build.sh` checks for upstream kernel-kit, core-kit, or SDK updates and rebuilds the kit when any version changes. If nothing changed, it logs and exits. Use it from cron:

```cron
0 6 * * * /path/to/bottlerocket-extra-kit/scripts/daily-build.sh
```

Environment variables:
- `VENDOR` — ECR vendor alias for publishing (default: `peng`). Set empty to skip publish.
- `RELEASE_VERSION` — Override the extra-kit release version (default: read from Makefile).
- `LOG_FILE` — Log output path (default: `/tmp/extra-kit-daily-build.log`).
- `DRY_RUN` — Set to `true` to show what would change without acting.

## Tools That Work Best on the Host

Some tools in this kit work correctly only when run natively on the Bottlerocket host, not from inside a container. There are two main reasons for this.

**Process-aware tools** — tools like `pldd` attach to running processes via `/proc/<pid>/maps` or ptrace. They need to see the host's process namespace and require `SYS_PTRACE` capability. Running them from a sidecar container against host processes is unreliable and often blocked by the container's security profile.

**Dynamic linker tools** — `ldd` works by invoking the ELF interpreter embedded in the target binary (`LD_TRACE_LOADED_OBJECTS=1`). When run from a container against a binary on a mounted host volume, it uses the container's dynamic linker and library paths, not the host's — so the dependency output will be wrong. Running `ldd` natively on the host ensures it resolves libraries against the correct sysroot. If you only need to inspect `NEEDED` entries statically (without executing the binary), `readelf -d` or `objdump -p` from `binutils` work correctly from any context.

**Performance and tracing tools** — eBPF, hardware performance counters, and kernel tracing require elevated capabilities (`CAP_BPF`, `CAP_PERFMON`, `CAP_SYS_ADMIN`) and access to kernel internals that are typically restricted inside containers. Running on the host gives full visibility across all processes and kernel subsystems.

The following packages are designed for or work best at the host level:

- **glibc-utils** (`ldd`, `pldd`) — `ldd` resolves shared library dependencies by executing the target binary's ELF interpreter; must run natively for correct results. `pldd` lists shared libraries loaded into a running process via `/proc`; requires host process namespace access.
- **perf** — Linux kernel performance counters. Requires `CAP_PERFMON` (or `CAP_SYS_ADMIN` on older kernels) and access to perf events, which are often restricted in containers.
- **perfrun** — Convenience wrapper around `perf` for common workflows (record, flamegraph, stat, top). Depends on `perf`.
- **bpftrace** — High-level eBPF tracing language. Requires `CAP_BPF` + `CAP_PERFMON` and access to kernel BTF/debug info.
- **sysstat** (`sar`, `iostat`, `mpstat`, etc.) — System-wide I/O, CPU, and memory statistics. Most useful at the host level for whole-node visibility.

## Packages
- [awscli2](https://aws.amazon.com/cli/) v2.27.0 - AWS CLI version 2
- [binutils](https://www.gnu.org/software/binutils/) v2.44 - Binary utilities: `as`, `ld`, `objdump`, `nm`, `strip`, `readelf`, and more
- [bpftrace](https://github.com/bpftrace/bpftrace) v0.24.2 - High-level tracing language for Linux eBPF. Pre-built static binary (x86_64 only).
- [curl](https://curl.se) v8.12.1
- [diffutils](https://www.gnu.org/software/diffutils/) v3.12 - GNU diff utilities: `diff`, `diff3`, `cmp`, `sdiff`
- [file](https://www.darwinsys.com/file/) v5.46 - Determine file type (`file` command)
- [glibc-utils](https://www.gnu.org/software/libc/) v2.42 - GNU C Library utilities: `ldd` (list dynamic dependencies) and `pldd` (list shared libraries of a running process).
- [golang](https://go.dev) v1.26.1 - The Go programming language toolchain. Note: `/tmp` is mounted `noexec` on Bottlerocket; set `GOCACHE`, `GOTMPDIR`, and `GOPATH` to a writable path such as `/local` before running `go build` or `go run`.
- [gzip](https://www.gnu.org/software/gzip/) v1.14 - GNU compression utility: `gzip`, `gunzip`, `zcat`, `zgrep`. The core kit ships only `unpigz`, which cannot compress, so this fills the gap.
- [jsoncpp](https://github.com/open-source-parsers/jsoncpp) v1.9.6
- [logrotate](https://github.com/logrotate/logrotate) v3.22.0 - Rotates and maintains log files. Ships a default `/etc/logrotate.conf` plus a `logrotate.timer` that runs daily; drop additional rules into `/etc/logrotate.d`. Pulls in `gzip` so `compress` works out of the box.
- [nerdctl](https://github.com/containerd/nerdctl) v2.1.6 - Docker-compatible CLI for containerd
- [oomd](https://github.com/facebookincubator/oomd) v0.5.0
- [openssh](https://www.openssh.com/) v10.0p1 - OpenSSH daemon (`sshd`) and client utilities (`ssh`, `scp`, `sftp`, `ssh-keygen`)
- [perf](https://perf.wiki.kernel.org/) v6.1.159 - Linux kernel performance analysis tool.
- [perfrun](https://www.kernel.org/) v0.1.0 - Convenience wrapper for common `perf` workflows: `record`, `flamegraph`, `stat`, `top`. Installed automatically with `perf`.
- [permissive-selinux] - Set SELinux mode to permissive. Useful for debugging/developing while bypassing SELinux denials (e.g., running shell scripts)
- [procps-ng](https://gitlab.com/procps-ng/procps) - Process monitoring utilities: `ps`, `top`, `free`, `vmstat`, `pgrep`, `pkill`, and more
- [sysstat](https://github.com/sysstat/sysstat) v12.7.7 - Commands: sar, sadf, iostat, mpstat, pidstat, tapestat, cifsiostat.
- [tar](https://www.gnu.org/software/tar/) v1.35 - GNU tar archiving utility
- [vim](https://github.com/vim/vim) v9.1.0
- [which](https://savannah.gnu.org/projects/which/) v2.23 - Show full path of shell commands
- [libcap-utils](https://sites.google.com/site/fullycapable/) v2.77 - POSIX capabilities utilities: `getcap`, `setcap`, `capsh`, `getpcaps`
