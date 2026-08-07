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
#   4. If any version is newer (or --force), regenerates Twoliter.toml, builds
#      the kit, commits the update, and optionally publishes.
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

log() {
    local ts
    ts="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    echo "[${ts}] $*" | tee -a "${LOG_FILE}"
}

die() {
    log "ERROR: $*"
    exit 1
}

# Fetch the latest version for a GitHub repo. Uses releases/latest first,
# falls back to the newest tag if the repo has no releases.
get_latest_version() {
    local repo="$1"
    local version

    local http_code body
    body=$(curl -sL -w '\n%{http_code}' \
        "https://api.github.com/repos/${repo}/releases/latest" 2>/dev/null) || true
    http_code=$(echo "$body" | tail -1)
    body=$(echo "$body" | sed '$d')

    if [[ "$http_code" == "200" ]]; then
        version=$(echo "$body" | grep '"tag_name"' | head -1 | cut -d'"' -f4)
    else
        # Fallback: first tag (most recently pushed)
        version=$(curl -sL "https://api.github.com/repos/${repo}/tags" \
            | grep '"name"' | head -1 | cut -d'"' -f4)
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

    sdk=$(curl -sfL "https://raw.githubusercontent.com/${repo}/v${version}/Twoliter.toml" \
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
    printf "%b" "$CHANGES" | tee -a "${LOG_FILE}"
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

# ── Step 4: Regenerate Twoliter.toml and rebuild ─────────────────────────────
if [[ "$CHANGED" == "true" ]]; then
    log "Regenerating Twoliter.toml..."
    make generate-twoliter-toml RELEASE_VERSION="${RELEASE_VERSION}" 2>&1 | tee -a "${LOG_FILE}"

    log "Running make update..."
    make update 2>&1 | tee -a "${LOG_FILE}"
fi

log "Building kit..."
make build 2>&1 | tee -a "${LOG_FILE}"

# ── Step 5: Commit the update (only if Twoliter.toml changed) ────────────────
if [[ "$CHANGED" == "true" ]]; then
    log "Committing updated Twoliter.toml and Twoliter.lock..."
    git add Twoliter.toml Twoliter.lock
    git commit -q -m "chore: Bump upstream dependencies (daily build)

Automated update to latest upstream versions:
$(printf '%b' "$CHANGES")"

    log "Committed: $(git log --oneline -1)"
fi

# ── Step 6: Publish (optional) ───────────────────────────────────────────────
if [[ -n "$VENDOR" ]]; then
    ensure_infra_toml
    log "Publishing kit to vendor=${VENDOR}..."
    make publish VENDOR="${VENDOR}" 2>&1 | tee -a "${LOG_FILE}"
    log "Published successfully."
else
    log "VENDOR is empty — skipping publish."
fi

log "Daily build complete."
