#!/bin/bash
# Create nerdctl-<version>-vendor.tar.gz, the Go module vendor directory for
# nerdctl, reproducibly.
#
# The output must be byte-identical on every machine, because Cargo.toml pins
# its sha512. That holds because:
#   - `go mod vendor` output is fully determined by nerdctl's go.mod/go.sum,
#     and the module proxy serves checksum-verified module contents;
#   - tar runs with sorted entries, a fixed mtime and numeric root ownership;
#   - gzip -n omits the file name and timestamp from the header.
#
# Usage: create-vendor-tarball.sh [output-dir]   (default: this directory)
set -euo pipefail

VERSION="2.1.6"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${1:-${SCRIPT_DIR}}"
TARBALL_NAME="nerdctl-${VERSION}-vendor.tar.gz"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "${WORKDIR}"' EXIT

# Keep the caller's GOPROXY (some networks block proxy.golang.org and use
# GOPROXY=direct). With direct, go clones each module with git; ignore the
# user's global git config so a url.<ssh>.insteadOf rewrite can't push those
# anonymous HTTPS clones onto SSH, which fails or gets rate limited.
export GOPROXY="${GOPROXY:-$(go env GOPROXY)}"
export GIT_CONFIG_GLOBAL=/dev/null
export GOFLAGS="-mod=mod"
export GOTOOLCHAIN="local"
export GOPATH="${WORKDIR}/gopath"
export GOMODCACHE="${WORKDIR}/gopath/pkg/mod"

cd "${WORKDIR}"
echo "Downloading nerdctl v${VERSION}..." >&2
curl -fsSL "https://github.com/containerd/nerdctl/archive/refs/tags/v${VERSION}.tar.gz" | tar -xzf -
cd "nerdctl-${VERSION}"

echo "Vendoring dependencies..." >&2
go mod vendor

echo "Creating ${TARBALL_NAME}..." >&2
tar --sort=name --mtime='1970-01-01 00:00:00Z' --owner=0 --group=0 --numeric-owner \
    --format=gnu -cf - vendor/ | gzip -9 -n > "${WORKDIR}/${TARBALL_NAME}"
chmod u+w -R "${GOMODCACHE}" 2>/dev/null || true

mv "${WORKDIR}/${TARBALL_NAME}" "${OUT_DIR}/${TARBALL_NAME}"
echo "SHA512: $(sha512sum "${OUT_DIR}/${TARBALL_NAME}" | awk '{print $1}')"
