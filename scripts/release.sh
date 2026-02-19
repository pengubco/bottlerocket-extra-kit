#!/usr/bin/env bash
# release.sh - Tag a commit, push the tag, and build+publish the kit.
#
# Usage: ./scripts/release.sh <version>
#   version: the extra-kit release version, e.g. 1.0.2
#
# The script will:
#   1. Create/update a git tag vVERSION on HEAD
#   2. Force-push the tag to origin
#   3. Run make build-and-publish with the version substituted into generate-twoliter-toml

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ── Argument validation ────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <version> [VENDOR]" >&2
    echo "  version  e.g. 1.0.2" >&2
    echo "  VENDOR   ECR vendor alias (default: peng)" >&2
    exit 1
fi

VERSION="$1"
VENDOR="${2:-peng}"
TAG="v${VERSION}"

# Basic semver sanity check
if ! [[ "${VERSION}" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9._-]+)?$ ]]; then
    echo "Error: version '${VERSION}' does not look like a semver (e.g. 1.0.2)" >&2
    exit 1
fi

cd "${REPO_ROOT}"

# ── Step 1: tag the current commit ────────────────────────────────────────────
echo "==> Tagging HEAD as ${TAG}"
git tag -f "${TAG}" -m "Release ${TAG}"

# ── Step 2: push (or update) the tag on origin ────────────────────────────────
echo "==> Pushing tag ${TAG} to origin"
git push origin "${TAG}" --force

# ── Step 3: build and publish with the given version ──────────────────────────
# Override the hardcoded 1.0.1 in the generate-twoliter-toml target by passing
# RELEASE_VERSION; the Makefile reads it via the environment when present.
# We patch the invocation inline using make's variable override syntax.
echo "==> Running make build-and-publish VENDOR=${VENDOR} (version=${VERSION})"
make build-and-publish \
    VENDOR="${VENDOR}" \
    RELEASE_VERSION="${VERSION}"
