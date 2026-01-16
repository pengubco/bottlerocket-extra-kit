#!/bin/bash
set -euo pipefail

VERSION="2.1.6"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR=$(mktemp -d)
trap "rm -rf ${WORKDIR}" EXIT

cd "${WORKDIR}"

# Download and extract nerdctl source
echo "Downloading nerdctl v${VERSION}..."
curl -sL "https://github.com/containerd/nerdctl/archive/refs/tags/v${VERSION}.tar.gz" | tar -xzf -

cd "nerdctl-${VERSION}"

# Vendor dependencies
echo "Vendoring dependencies (this requires network access)..."
go mod vendor

# Create vendor tarball in temp location
echo "Creating vendor tarball..."
TARBALL_NAME="nerdctl-${VERSION}-vendor.tar.gz"
tar -czf "/tmp/${TARBALL_NAME}" vendor/

# Compute SHA512
SHA512=$(sha512sum "/tmp/${TARBALL_NAME}" | awk '{print $1}')

# Move to package directory
mv "/tmp/${TARBALL_NAME}" "${SCRIPT_DIR}/"

echo ""
echo "✓ Created: ${SCRIPT_DIR}/${TARBALL_NAME}"
echo "✓ SHA512: ${SHA512}"
echo ""
echo "Next steps:"
echo "1. Update Cargo.toml and replace 'REPLACE_WITH_ACTUAL_SHA512' with:"
echo "   ${SHA512}"
echo "2. Run 'make build' to build the package"
