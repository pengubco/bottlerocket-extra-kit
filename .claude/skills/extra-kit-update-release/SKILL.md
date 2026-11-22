---
name: extra-kit-update-release
description: Update bottlerocket-extra-kit to the latest Bottlerocket core-kit, kernel-kit and SDK, build it for x86_64 and aarch64, and optionally cut a release (publish + GitHub release). Use when asked to "update the kit", "build against latest Bottlerocket", "rebuild the extra kit", "cut/publish a release", or to add or bump a package and verify it builds.
---

# Update, build and release bottlerocket-extra-kit

Run everything from the repository root. Builds print huge logs: always redirect
to a file and inspect it with `tail`/`grep`.

## 1. Check what changed upstream

```bash
make daily-build DAILY_BUILD_ARGS=--dry-run   # compares pins with latest upstream
make check-upstream                            # packages with newer upstream releases
make check-packages                            # kit/Cargo.lock/README consistency
```

The SDK is never chosen independently: it must be the SDK the pinned core-kit
was built with (`generate-twoliter` and `daily-build.sh` already do this).

## 2. Build against the latest kits without publishing

```bash
make generate-twoliter-toml RELEASE_VERSION=<current release-version>
make update
make fetch ARCH=x86_64 && make fetch ARCH=aarch64
make build-all-arches > /tmp/extra-kit-build.log 2>&1; tail -20 /tmp/extra-kit-build.log
```

Or, to build a single package: `make build-package PACKAGE=<name> ARCH=<arch>`.

Check results in `build/kits/bottlerocket-extra-kit/<arch>/Packages`. x86-only
packages (turbostat, pcm) have no aarch64 RPM; that is expected.

## 3. Release

Only when the user asks to publish. Publishing pushes to a public registry and
creates a GitHub release.

```bash
make release-github RELEASE_VERSION=<new version> RELEASE_ARGS="--latest"
```

`scripts/release.sh --help` explains the steps and flags (`--draft`,
`--attach-archives`, `--skip-build`).

## Rules and gotchas

- **Never republish a version.** Consumers lock the kit by version and digest.
  Every publish uses a new version; `release.sh` refuses an existing git tag or
  image tag. Don't work around that.
- **Publish only from a clean, committed tree.** The kit archive name embeds
  `git describe --dirty`; HEAD must not change between build and publish.
- **Expired registry login.** `DENIED: Your authorization token has expired`
  from krane means the docker login for `public.ecr.aws` is stale:
  `aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws`
  (for a private ECR registry use `aws ecr get-login-password --region <r>`).
- **Go modules on corporate networks.** `proxy.golang.org` may be blocked, so
  `GOPROXY=direct` is used and `git` must reach GitHub over HTTPS. A transient
  "Received disconnect ... Bye Bye" while building `nerdctl` is GitHub SSH rate
  limiting; retry.
- **nerdctl vendor tarball** is generated reproducibly by
  `packages/nerdctl/create-vendor-tarball.sh`. If its sha512 mismatches, the
  vendored module set changed: regenerate and update the pin deliberately.
- **Kernel tools** (bpftool, turbostat, cpupower) build from the same AL2023
  kernel SRPM as bottlerocket-kernel-kit's kernel-6.1. When the kernel-kit is
  bumped, update the SRPM URL and sha512 in all three packages together.
- **Prefer the core kit.** If the core kit ships a tool, don't package it here; at most add the parts it leaves out under a different package name (see binutils-tools, procps-ng).
- **Cargo.lock**: after adding a package, run `cargo generate-lockfile --offline`
  and make sure the diff only adds entries.
