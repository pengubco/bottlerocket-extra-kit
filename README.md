# Bottlerocket Extra Kit
`bottlerocket-extra-kit` contains RPM packages used for developing and debugging on Bottlerocket that are not included in the [bottlerocket-kernel-kit](https://github.com/bottlerocket-os/bottlerocket-kernel-kit) and [bottlerocket-core-kit](https://github.com/bottlerocket-os/bottlerocket-core-kit). You can consume packages from this kit to build your own [Bottlerocket](https://github.com/bottlerocket-os) variant.

You should NOT use `bottlerocket-extra-kit` in your production Bottlerocket OS. Packages here are only intended to make developing and debugging on Bottlerocket easier.

## Use RPM packages from the released kit
Take the [aws-dev](https://github.com/bottlerocket-os/bottlerocket/tree/develop/variants/aws-dev) variant as an example. 

Step 1. Add vendor and kit to the `{project-root}/Twoliter.toml`.
```toml
[vendor.peng]
registry = "public.ecr.aws/m8c0s8v8"

[[kit]]
name = "bottlerocket-extra-kit"
# Find the versions in Releases
version = "1.0.1-kernalkit-4.7.1-corekit-12.2.0-sdk-0.66.0"
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

The extra-kit will release with the latest core-kit and SDK at the time of release. The release name follows this pattern:
`v0.0.3-kernelkit-4.3.0-corekit-10.3.0-sdk-0.64.0`, which reads:
- bottlerocket-extra-kit version 0.0.3
- bottlerocket-kernel-kit version 4.3.0
- bottlerocket-core-kit version 10.3.0
- bottlerocket-sdk version 0.64.0

If you need to build with a different core-kit and SDK version, please check out the repository and update the `Twoliter.toml`.

## Build and publish this kit 

Generate `Twoliter.toml` using the latest core-kit, kernel-kit, and SDK versions from GitHub (default):
```
make generate-twoliter-toml RELEASE_VERSION=1.0.3
```

Pin to the same versions used in an existing `Twoliter.toml`:
```
make generate-twoliter-toml RELEASE_VERSION=1.0.3 TWOLITER_SOURCE=/path/to/Twoliter.toml
```

Or specify versions explicitly:
```
make generate-twoliter-toml RELEASE_VERSION=1.0.3 CORE_KIT_VERSION=13.0.0 KERNEL_KIT_VERSION=5.0.0 SDK_VERSION=0.70.0
```

You can mix and match — any version not specified will be fetched from GitHub. For example, pin only the SDK:
```
make generate-twoliter-toml RELEASE_VERSION=1.0.3 SDK_VERSION=0.70.0
```

To build a single package without rebuilding the entire kit:
```
make build-package PACKAGE=awscli2
```

Then build and publish:
```
make update && make fetch && make build
make publish VENDOR=xxx
```

or 
```
make build-and-publish VENDOR=xxx
```

## Performance Analysis Tools

Some performance analysis tools — particularly those that use eBPF, hardware performance counters, or kernel tracing — work best when run directly on the host rather than inside a container. Containers share the host kernel but may have restricted access to `/proc`, `/sys`, perf events, and BPF syscalls depending on their security profile. Running these tools on the Bottlerocket host (e.g., via the admin container or an SSH session) gives them full visibility into all processes, kernel internals, and hardware counters across the entire node.

The following packages in this kit are designed for host-level performance analysis:

- **perf** — Linux kernel performance counters. Profiling from inside a container requires `CAP_PERFMON` (or `CAP_SYS_ADMIN` on older kernels) and access to perf events, which are often restricted. Running on the host avoids these limitations and gives system-wide visibility.
- **perfrun** — Convenience wrapper around `perf` for common workflows (record, flamegraph, stat, top). Depends on `perf`.
- **bpftrace** — High-level eBPF tracing language. eBPF programs require `CAP_BPF` + `CAP_PERFMON` and access to kernel BTF/debug info. Host execution is strongly preferred for full tracing capability.
- **sysstat** (`sar`, `iostat`, `mpstat`, etc.) — System-wide I/O, CPU, and memory statistics. Most useful at the host level for whole-node visibility.

## Packages
- [awscli2](https://aws.amazon.com/cli/) v2.27.0 - AWS CLI version 2
- [binutils](https://www.gnu.org/software/binutils/) v2.44 - Binary utilities: `as`, `ld`, `objdump`, `nm`, `strip`, `readelf`, and more
- [bpftrace](https://github.com/bpftrace/bpftrace) v0.24.2 - High-level tracing language for Linux eBPF. Pre-built static binary (x86_64 only). See [Performance Analysis Tools](#performance-analysis-tools).
- [curl](https://curl.se) v8.12.1
- [diffutils](https://www.gnu.org/software/diffutils/) v3.12 - GNU diff utilities: `diff`, `diff3`, `cmp`, `sdiff`
- [file](https://www.darwinsys.com/file/) v5.46 - Determine file type (`file` command)
- [golang](https://go.dev) v1.26.1 - The Go programming language toolchain. Note: `/tmp` is mounted `noexec` on Bottlerocket; set `GOCACHE`, `GOTMPDIR`, and `GOPATH` to a writable path such as `/local` before running `go build` or `go run`.
- [jsoncpp](https://github.com/open-source-parsers/jsoncpp) v1.9.6
- [nerdctl](https://github.com/containerd/nerdctl) v2.1.6 - Docker-compatible CLI for containerd
- [oomd](https://github.com/facebookincubator/oomd) v0.5.0
- [openssh](https://www.openssh.com/) v10.0p1 - OpenSSH daemon (`sshd`) and client utilities (`ssh`, `scp`, `sftp`, `ssh-keygen`)
- [perf](https://perf.wiki.kernel.org/) v6.1.159 - Linux kernel performance analysis tool. See [Performance Analysis Tools](#performance-analysis-tools).
- [perfrun](https://www.kernel.org/) v0.1.0 - Convenience wrapper for common `perf` workflows: `record`, `flamegraph`, `stat`, `top`. Installed automatically with `perf`. See [Performance Analysis Tools](#performance-analysis-tools).
- [permissive-selinux] - Set SELinux mode to permissive. Useful for debugging/developing while bypassing SELinux denials (e.g., running shell scripts)
- [procps-ng](https://gitlab.com/procps-ng/procps) - Process monitoring utilities: `ps`, `top`, `free`, `vmstat`, `pgrep`, `pkill`, and more
- [sysstat](https://github.com/sysstat/sysstat) v12.7.7 - Commands: sar, sadf, iostat, mpstat, pidstat, tapestat, cifsiostat. See [Performance Analysis Tools](#performance-analysis-tools).
- [tar](https://www.gnu.org/software/tar/) v1.35 - GNU tar archiving utility
- [vim](https://github.com/vim/vim) v9.1.0
- [which](https://savannah.gnu.org/projects/which/) v2.23 - Show full path of shell commands
