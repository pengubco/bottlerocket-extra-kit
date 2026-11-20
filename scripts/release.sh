#!/usr/bin/env bash
# release.sh - Cut a multi-arch release of the kit and create a GitHub release.
#
# Usage: ./scripts/release.sh [flags] <version>
#   version: the new extra-kit release version, e.g. 1.0.6
#
# Steps:
#   1. Preflight: clean tree, tag vVERSION does not exist yet, gh logged in,
#      Infra.toml present.
#   2. Set release-version to VERSION in Twoliter.toml and RELEASE_VERSION in
#      the Makefile (keeping the current core-kit/kernel-kit/SDK pins, or
#      bumping them to the latest with --latest), refresh Twoliter.lock, and
#      commit. Skipped when the tree already declares VERSION.
#   3. Build the kit for every arch in ARCHES (default: x86_64 aarch64).
#   4. Publish. twoliter pushes every arch archive for this commit under one
#      multi-arch OCI index.
#   5. Verify the published index contains every arch (needs crane).
#   6. Push the commit and an annotated tag vVERSION, then create the GitHub
#      release with the dependency pins, package list and changelog.
#
# The tag is created only after publishing succeeds, so a failed build never
# leaves behind a tag without an artifact. HEAD must not move between build and
# publish, because the kit archive name embeds `git describe`.
#
# Flags:
#   --latest            Bump core-kit/kernel-kit/SDK to the latest upstream
#                       before releasing (default: keep the current pins).
#   --draft             Create the GitHub release as a draft.
#   --attach-archives   Upload the per-arch kit tarballs as release assets.
#   --skip-build        Reuse archives already in build/kits for this commit.
#   -h, --help          Show this help.
#
# Environment variables:
#   VENDOR   Vendor in Infra.toml/Twoliter.toml to publish to (default: peng).
#   ARCHES   Space-separated architectures (default: "x86_64 aarch64").
#   REMOTE   Git remote to push to (default: origin).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
KIT="bottlerocket-extra-kit"

VENDOR="${VENDOR:-peng}"
ARCHES="${ARCHES:-x86_64 aarch64}"
REMOTE="${REMOTE:-origin}"
LATEST=false
DRAFT=false
ATTACH=false
SKIP_BUILD=false
VERSION=""

usage() { sed -n '2,/^$/{ s/^# //; s/^#//; p }' "$0"; }
die() { echo "Error: $*" >&2; exit 1; }
step() { echo; echo "==> $*"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --latest)          LATEST=true ;;
        --draft)           DRAFT=true ;;
        --attach-archives) ATTACH=true ;;
        --skip-build)      SKIP_BUILD=true ;;
        -h|--help)         usage; exit 0 ;;
        -*)                die "unknown option: $1" ;;
        *)                 [[ -z "$VERSION" ]] || die "unexpected argument: $1"; VERSION="$1" ;;
    esac
    shift
done

[[ -n "$VERSION" ]] || { usage >&2; exit 1; }
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9._-]+)?$ ]] \
    || die "version '${VERSION}' does not look like semver (e.g. 1.0.6)"
TAG="v${VERSION}"

cd "${REPO_ROOT}"

# Read a pinned version from Twoliter.toml. Arg: kit name, or "sdk".
pin() {
    if [[ "$1" == "sdk" ]]; then
        sed -n '/^\[sdk\]/,/^\[/p' Twoliter.toml | grep '^version' | head -1 | cut -d'"' -f2
    else
        grep -A3 "name = \"$1\"" Twoliter.toml | grep '^version' | head -1 | cut -d'"' -f2
    fi
}

current_release_version() {
    grep '^release-version' Twoliter.toml | head -1 | cut -d'"' -f2
}

# ── Step 1: preflight ─────────────────────────────────────────────────────────
step "Preflight checks"
command -v gh >/dev/null || die "gh CLI not found"
gh auth status >/dev/null 2>&1 || die "gh is not logged in; run 'gh auth login'"
[[ -f Infra.toml ]] || die "Infra.toml not found; create it from Infra-template.toml"
grep -q "^\[vendor\.${VENDOR}\]" Infra.toml || die "vendor '${VENDOR}' not defined in Infra.toml"
[[ -z "$(git status --porcelain)" ]] || { git status --short >&2; die "working tree is not clean"; }
git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null && die "tag ${TAG} already exists locally"
git fetch -q --tags "${REMOTE}"
git ls-remote --exit-code --tags "${REMOTE}" "refs/tags/${TAG}" >/dev/null 2>&1 \
    && die "tag ${TAG} already exists on ${REMOTE}"
BRANCH="$(git symbolic-ref --short HEAD)" || die "HEAD is detached; check out a branch"
PREV_TAG="$(git describe --tags --abbrev=0 --match 'v[0-9]*' 2>/dev/null || true)"
echo "Branch ${BRANCH}, previous tag ${PREV_TAG:-<none>}, arches: ${ARCHES}"

# ── Step 2: set the release version and commit ────────────────────────────────
if [[ "$LATEST" == "true" || "$(current_release_version)" != "$VERSION" ]]; then
    step "Setting release-version ${VERSION} (latest upstream pins: ${LATEST})"
    if [[ "$LATEST" == "true" ]]; then
        make --no-print-directory generate-twoliter-toml RELEASE_VERSION="${VERSION}"
    else
        # The make target redirects into Twoliter.toml, which would truncate it
        # before it is read, so read the current pins from a copy.
        src="$(mktemp)"; cp Twoliter.toml "$src"
        make --no-print-directory generate-twoliter-toml RELEASE_VERSION="${VERSION}" TWOLITER_SOURCE="$src"
        rm -f "$src"
    fi
    sed -i "s/^RELEASE_VERSION ?= .*/RELEASE_VERSION ?= ${VERSION}/" Makefile
    make --no-print-directory update

    git add Twoliter.toml Twoliter.lock Makefile
    if git diff --cached --quiet; then
        echo "Nothing to commit."
    else
        git commit -q -m "chore: Release ${TAG}" -- Twoliter.toml Twoliter.lock Makefile
        echo "Committed: $(git log --oneline -1)"
    fi
fi
[[ "$(current_release_version)" == "$VERSION" ]] \
    || die "Twoliter.toml release-version is $(current_release_version), expected ${VERSION}"

BUILD_ID="$(git describe --always --dirty --exclude '*' --abbrev=8)"
KIT_DIR="build/kits/${KIT}"

# ── Step 3: build every arch ──────────────────────────────────────────────────
if [[ "$SKIP_BUILD" == "false" ]]; then
    for arch in ${ARCHES}; do
        step "Building ${KIT} ${TAG} for ${arch}"
        make --no-print-directory build ARCH="${arch}"
    done
fi

ARCHIVES=()
for arch in ${ARCHES}; do
    a="${KIT_DIR}/${KIT}-${TAG}-${BUILD_ID}-${arch}.tar"
    [[ -f "$a" ]] || die "missing archive $a"
    ARCHIVES+=("$a")
done
[[ -z "$(git status --porcelain)" ]] || { git status --short >&2; die "build left the tree dirty; refusing to publish"; }

# ── Step 4: publish ───────────────────────────────────────────────────────────
step "Publishing to vendor ${VENDOR}"
make --no-print-directory publish VENDOR="${VENDOR}"

# ── Step 5: verify the published index ────────────────────────────────────────
REGISTRY="$(sed -n "/^\[vendor\.${VENDOR}\]/,/^\[/p" Infra.toml | grep '^registry' | head -1 | cut -d'"' -f2)"
IMAGE="${REGISTRY}/${KIT}:${TAG}"
if command -v crane >/dev/null; then
    step "Verifying ${IMAGE}"
    manifest="$(crane manifest "${IMAGE}")"
    for arch in ${ARCHES}; do
        case "$arch" in x86_64) oci=amd64 ;; aarch64) oci=arm64 ;; *) oci="$arch" ;; esac
        grep -q "\"architecture\":\"${oci}\"" <<<"$manifest" \
            || die "${IMAGE} has no ${oci} manifest"
        echo "  ${oci}: ok"
    done
else
    echo "crane not found; skipping verification of ${IMAGE}"
fi

# ── Step 6: tag, push, and create the GitHub release ──────────────────────────
step "Pushing ${BRANCH} and ${TAG} to ${REMOTE}"
git tag -a "${TAG}" -m "Release ${TAG}"
git push "${REMOTE}" "${BRANCH}" "refs/tags/${TAG}"

NOTES="$(mktemp)"
trap 'rm -f "$NOTES"' EXIT
{
    echo "## Usage"
    echo
    echo "Add to your project's \`Twoliter.toml\`:"
    echo
    echo '```toml'
    echo "[vendor.${VENDOR}]"
    echo "registry = \"${REGISTRY}\""
    echo
    echo "[[kit]]"
    echo "name = \"${KIT}\""
    echo "version = \"${VERSION}\""
    echo "vendor = \"${VENDOR}\""
    echo '```'
    echo
    echo "Image: \`${IMAGE}\` (build \`${BUILD_ID}\`)"
    echo
    echo "Architectures: $(for a in ${ARCHES}; do printf '`%s` ' "$a"; done)"
    echo
    echo "## Built against"
    echo
    echo "| Dependency | Version |"
    echo "|---|---|"
    echo "| bottlerocket-kernel-kit | $(pin bottlerocket-kernel-kit) |"
    echo "| bottlerocket-core-kit | $(pin bottlerocket-core-kit) |"
    echo "| bottlerocket-sdk | $(pin sdk) |"
    echo
    echo "Your project must pin the same core-kit, kernel-kit and SDK versions."
    echo
    echo "## Packages"
    echo
    for d in packages/*/; do echo "- $(basename "$d")"; done
    if [[ -n "$PREV_TAG" ]]; then
        echo
        echo "## Changes since ${PREV_TAG}"
        echo
        git log --no-merges --format='- %s (%h)' "${PREV_TAG}..${TAG}"
    fi
} > "$NOTES"

step "Creating GitHub release ${TAG}"
gh_args=(--title "${TAG}" --notes-file "$NOTES" --verify-tag)
[[ "$DRAFT" == "true" ]] && gh_args+=(--draft)
[[ "$ATTACH" == "true" ]] && gh_args+=("${ARCHIVES[@]}")
gh release create "${TAG}" "${gh_args[@]}"

echo
echo "Released ${TAG}: ${IMAGE}"
