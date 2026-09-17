#!/usr/bin/env bash
# daily-build.sh — Check for upstream kit/SDK updates and rebuild if needed.
#
# Intended to run from cron, e.g.:
#   0 6 * * * /path/to/bottlerocket-extra-kit/scripts/daily-build.sh
#
# What it does:
#   1. Queries GitHub for the latest kernel-kit, core-kit, and SDK versions.
#   2. Compares them against the versions pinned in Twoliter.toml.
#   3. If nothing changed (and --force is not set), logs the result and exits.
#   4. If any version is newer (or --force), regenerates Twoliter.toml, commits
#      the new pins, builds the kit, and optionally publishes.
#
# The commit happens before the build on purpose; see Step 5 for why.
#
# Flags:
#   --force         Build and publish even if Twoliter.toml already has the
#                   latest versions.
#   --dry-run       Show what would change without acting.
#
# Environment variables:
#   VENDOR          — ECR vendor alias for `make publish` (default: peng).
#                     Set to empty string to skip publishing.
#   REGISTRY        — OCI registry URL (e.g. public.ecr.aws/m8c0s8v8).
#                     Required for publishing unless Infra.toml already exists.
#   PUBLISH_REGIONS — Comma-separated AWS regions (default: us-west-2).
#   RELEASE_VERSION — Extra-kit release version (default: read from Makefile).
#   LOG_FILE        — Path to log file (default: /tmp/extra-kit-daily-build.log).
#   DRY_RUN         — If set to "true", same as --dry-run flag.
#   GITHUB_TOKEN    — GitHub token for API calls. Unauthenticated requests are
#                     capped at 60/hour per IP, which is easily exhausted on a
#                     shared NAT (e.g. a Cloud Desktop). If unset, the script
#                     falls back to `gh auth token` when the gh CLI is logged in.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

VENDOR="${VENDOR:-peng}"
REGISTRY="${REGISTRY:-}"
PUBLISH_REGIONS="${PUBLISH_REGIONS:-us-west-2}"
LOG_FILE="${LOG_FILE:-/tmp/extra-kit-daily-build.log}"
DRY_RUN="${DRY_RUN:-false}"
FORCE=false

# ── Parse flags ──────────────────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --force)   FORCE=true ;;
        --dry-run) DRY_RUN=true ;;
        --help|-h)
            sed -n '2,/^$/{ s/^# //; s/^#//; p }' "$0"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg" >&2
            exit 1
            ;;
    esac
done

# Log to stderr, not stdout. Several helpers below are called inside command
# substitutions, which capture stdout — logging to stdout there would swallow
# the message into the caller's variable instead of showing it.
log() {
    local ts
    ts="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    echo "[${ts}] $*" | tee -a "${LOG_FILE}" >&2
}

die() {
    log "ERROR: $*"
    exit 1
}

# ── GitHub authentication ────────────────────────────────────────────────────
# Prefer an explicit GITHUB_TOKEN; otherwise borrow the gh CLI's token if the
# user is logged in. Without a token the API allows only 60 requests/hour per
# IP, which a shared Cloud Desktop NAT address exhausts quickly.
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
if [[ -z "$GITHUB_TOKEN" ]] && command -v gh >/dev/null 2>&1; then
    GITHUB_TOKEN="$(gh auth token 2>/dev/null || true)"
fi

GH_AUTH_ARGS=()
if [[ -n "$GITHUB_TOKEN" ]]; then
    GH_AUTH_ARGS=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
fi

# Fail with an actionable message when GitHub rate limits us, instead of
# reporting the downstream symptom ("could not determine latest version").
check_rate_limit() {
    local code="$1" payload="$2"

    [[ "$code" == "403" || "$code" == "429" ]] || return 0
    echo "$payload" | grep -qi 'rate limit' || return 0

    local hint
    if [[ -n "$GITHUB_TOKEN" ]]; then
        hint="A token was sent but the request was still limited; it may be invalid or expired."
    else
        hint="No token was found. Set GITHUB_TOKEN, or run 'gh auth login' so the script can use 'gh auth token'."
    fi

    die "GitHub API rate limit exceeded (HTTP ${code}). ${hint}"
}

# Fetch the latest version for a GitHub repo. Uses releases/latest first,
# falls back to the newest tag if the repo has no releases.
get_latest_version() {
    local repo="$1"
    local version

    local http_code body
    body=$(curl -sL "${GH_AUTH_ARGS[@]}" -w '\n%{http_code}' \
        "https://api.github.com/repos/${repo}/releases/latest" 2>/dev/null) || true
    http_code=$(echo "$body" | tail -1)
    body=$(echo "$body" | sed '$d')

    if [[ "$http_code" == "200" ]]; then
        version=$(echo "$body" | grep '"tag_name"' | head -1 | cut -d'"' -f4) || true
    else
        check_rate_limit "$http_code" "$body"

        # Fallback: first tag (most recently pushed). Repos without releases
        # land here legitimately, so a non-200 above is not itself an error.
        local tags_code tags_body
        tags_body=$(curl -sL "${GH_AUTH_ARGS[@]}" -w '\n%{http_code}' \
            "https://api.github.com/repos/${repo}/tags" 2>/dev/null) || true
        tags_code=$(echo "$tags_body" | tail -1)
        tags_body=$(echo "$tags_body" | sed '$d')

        check_rate_limit "$tags_code" "$tags_body"
        [[ "$tags_code" == "200" ]] \
            || die "GitHub API returned HTTP ${tags_code} listing tags for ${repo}"

        version=$(echo "$tags_body" | grep '"name"' | head -1 | cut -d'"' -f4) || true
    fi

    [[ -z "$version" ]] && die "Could not determine latest version for ${repo}"

    # Strip leading 'v'
    echo "${version#v}"
}

# Read the SDK version a kit was built with, from that kit's Twoliter.toml at
# the given tag.
get_kit_sdk_version() {
    local repo="$1"
    local version="$2"
    local sdk

    sdk=$(curl -sfL "${GH_AUTH_ARGS[@]}" \
        "https://raw.githubusercontent.com/${repo}/v${version}/Twoliter.toml" \
        | sed -n '/^\[sdk\]/,/^\[/p' | grep '^version' | head -1 | cut -d'"' -f2) || true

    [[ -z "$sdk" ]] && die "Could not determine sdk version for ${repo} v${version}"

    echo "$sdk"
}

# Parse a version from Twoliter.toml for a given kit or sdk name.
parse_version() {
    local name="$1"
    local section="${2:-kit}"

    if [[ "$section" == "sdk" ]]; then
        sed -n '/^\[sdk\]/,/^\[/p' "${REPO_ROOT}/Twoliter.toml" \
            | grep '^version' | head -1 | cut -d'"' -f2
    else
        grep -A3 "name = \"${name}\"" "${REPO_ROOT}/Twoliter.toml" \
            | grep '^version' | head -1 | cut -d'"' -f2
    fi
}

# List uncommitted changes, empty when the working tree is clean.
dirty_tree() {
    git status --porcelain
}

# Refuse to *publish* from a dirty working tree. There is deliberately no
# override.
#
# Building dirty is fine and often useful locally. Publishing is not: the kit
# version embeds `git describe --always --dirty`, so a dirty tree yields an
# artifact tagged "-dirty" that corresponds to no commit and cannot be
# reproduced from the repository. A published kit that nobody can rebuild from
# source is not worth the convenience of skipping a commit.
#
# To build without publishing, set VENDOR to the empty string.
require_clean_tree_for_publish() {
    local dirty
    dirty="$(dirty_tree)"

    [[ -z "$dirty" ]] && return 0

    log "Working tree is not clean:"
    printf '%s\n' "$dirty" | tee -a "${LOG_FILE}" >&2
    die "Refusing to publish from a dirty tree, because the kit version embeds" \
        "'git describe' and a '-dirty' artifact matches no commit. Commit or" \
        "stash the changes above, or set VENDOR= to build without publishing."
}

# Ensure Infra.toml exists when publishing is requested.
ensure_infra_toml() {
    local infra_path="${REPO_ROOT}/Infra.toml"

    if [[ -f "$infra_path" ]]; then
        log "Using existing Infra.toml"
        return 0
    fi

    if [[ -z "$REGISTRY" ]]; then
        die "Publishing requires Infra.toml or REGISTRY env var. Set REGISTRY " \
            "to your OCI registry URL (e.g. public.ecr.aws/m8c0s8v8) or create " \
            "Infra.toml from Infra-template.toml."
    fi

    log "Generating Infra.toml (vendor=${VENDOR}, registry=${REGISTRY})"

    # Convert comma-separated regions to TOML array
    local regions_toml
    regions_toml=$(echo "$PUBLISH_REGIONS" | tr ',' '\n' | sed 's/.*/"&"/' | paste -sd, | sed 's/^/[/;s/$/]/')

    cat > "$infra_path" <<EOF
[aws]
regions = ${regions_toml}

[vendor.${VENDOR}]
registry = "${REGISTRY}"
EOF
}

cd "${REPO_ROOT}"

log "Starting daily build check (force=${FORCE})"

# ── Step 1: Resolve latest upstream versions ─────────────────────────────────
log "Fetching latest upstream versions..."
LATEST_KERNEL_KIT=$(get_latest_version "bottlerocket-os/bottlerocket-kernel-kit")
LATEST_CORE_KIT=$(get_latest_version "bottlerocket-os/bottlerocket-core-kit")
# The SDK is not chosen independently: twoliter requires the project and every
# dependency kit to agree on a single SDK, so take whatever SDK the core-kit we
# are about to pin was built with. The newest SDK release is frequently ahead of
# any kit that has adopted it.
LATEST_SDK=$(get_kit_sdk_version "bottlerocket-os/bottlerocket-core-kit" "${LATEST_CORE_KIT}")

log "  kernel-kit: ${LATEST_KERNEL_KIT}"
log "  core-kit:   ${LATEST_CORE_KIT}"
log "  sdk:        ${LATEST_SDK}"

# ── Step 2: Compare against current Twoliter.toml ────────────────────────────
CURRENT_KERNEL_KIT=$(parse_version "bottlerocket-kernel-kit" kit)
CURRENT_CORE_KIT=$(parse_version "bottlerocket-core-kit" kit)
CURRENT_SDK=$(parse_version "bottlerocket-sdk" sdk)

log "Current pins in Twoliter.toml:"
log "  kernel-kit: ${CURRENT_KERNEL_KIT}"
log "  core-kit:   ${CURRENT_CORE_KIT}"
log "  sdk:        ${CURRENT_SDK}"

CHANGED=false
CHANGES=""

if [[ "$LATEST_KERNEL_KIT" != "$CURRENT_KERNEL_KIT" ]]; then
    CHANGED=true
    CHANGES="${CHANGES}  kernel-kit ${CURRENT_KERNEL_KIT} -> ${LATEST_KERNEL_KIT}\n"
fi
if [[ "$LATEST_CORE_KIT" != "$CURRENT_CORE_KIT" ]]; then
    CHANGED=true
    CHANGES="${CHANGES}  core-kit   ${CURRENT_CORE_KIT} -> ${LATEST_CORE_KIT}\n"
fi
if [[ "$LATEST_SDK" != "$CURRENT_SDK" ]]; then
    CHANGED=true
    CHANGES="${CHANGES}  sdk        ${CURRENT_SDK} -> ${LATEST_SDK}\n"
fi

if [[ "$CHANGED" == "false" && "$FORCE" == "false" ]]; then
    log "No upstream changes detected. Nothing to do."
    exit 0
fi

if [[ "$CHANGED" == "true" ]]; then
    log "Upstream changes detected:"
    printf "%b" "$CHANGES" | tee -a "${LOG_FILE}" >&2
else
    log "No upstream changes, but --force is set. Rebuilding anyway."
fi

if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY_RUN — exiting without making changes."
    exit 0
fi

# ── Step 3: Determine release version ────────────────────────────────────────
if [[ -z "${RELEASE_VERSION:-}" ]]; then
    RELEASE_VERSION=$(grep '^RELEASE_VERSION' "${REPO_ROOT}/Makefile" \
        | head -1 | sed 's/.*?= *//')
fi
log "Using RELEASE_VERSION=${RELEASE_VERSION}"

# ── Step 4: Regenerate Twoliter.toml and refresh the lock ────────────────────
if [[ "$CHANGED" == "true" ]]; then
    log "Regenerating Twoliter.toml..."
    make generate-twoliter-toml RELEASE_VERSION="${RELEASE_VERSION}" 2>&1 | tee -a "${LOG_FILE}" >&2

    log "Running make update..."
    make update 2>&1 | tee -a "${LOG_FILE}" >&2
fi

# ── Step 5: Commit the pin bump, BEFORE building ─────────────────────────────
# This must happen before `make build`. The kit version embeds
# `git describe --always --dirty --abbrev=8` (BUILDSYS_VERSION_BUILD in
# twoliter's Makefile.toml), and that value is baked into the archive filename
# as well as passed to `publish-kit` as --build-id. Committing between build and
# publish changes HEAD, so publish looks for an archive name that the build
# never produced and fails with "No kit archive(s) exist at path ...".
# Committing first also means the published artifact is labelled with the exact
# commit that contains the pins it was built from.
if [[ "$CHANGED" == "true" ]]; then
    log "Committing updated Twoliter.toml and Twoliter.lock..."
    git add Twoliter.toml Twoliter.lock
    # --only limits the commit to these paths, so unrelated staged work in the
    # index can never be swept into an automated commit.
    git commit -q --only \
        -m "chore: Bump upstream dependencies (daily build)

Automated update to latest upstream versions:
$(printf '%b' "$CHANGES")" \
        -- Twoliter.toml Twoliter.lock

    log "Committed: $(git log --oneline -1)"
fi

# ── Step 6: Validate publish prerequisites before spending time on a build ───
# When publishing is requested, both of these would otherwise fail only after a
# multi-minute build has completed. Check them up front instead.
if [[ -n "$VENDOR" ]]; then
    ensure_infra_toml
    require_clean_tree_for_publish
fi

# ── Step 7: Build ────────────────────────────────────────────────────────────
log "Building kit..."
make build 2>&1 | tee -a "${LOG_FILE}" >&2

# ── Step 8: Publish (optional) ───────────────────────────────────────────────
if [[ -n "$VENDOR" ]]; then
    # Re-check: the build itself could have modified a tracked file.
    require_clean_tree_for_publish
    log "Publishing kit to vendor=${VENDOR}..."
    make publish VENDOR="${VENDOR}" 2>&1 | tee -a "${LOG_FILE}" >&2
    log "Published successfully."
else
    log "VENDOR is empty — skipping publish."
fi

log "Daily build complete."
