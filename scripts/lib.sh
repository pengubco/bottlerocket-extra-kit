# shellcheck shell=bash
# Shared helpers for the scripts in this directory. Source it; don't run it.

# tomlq FILE PATH — print one value from a TOML file (see scripts/go/cmd/tomlq).
# The helper is compiled once per shell session into a temp directory.
tomlq() {
    if [[ -z "${_TOMLQ_BIN:-}" || ! -x "${_TOMLQ_BIN}" ]]; then
        local lib_dir
        lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        _TOMLQ_BIN="$(mktemp -d)/tomlq"
        (cd "${lib_dir}/go" && go build -o "${_TOMLQ_BIN}" ./cmd/tomlq) \
            || { echo "failed to build tomlq" >&2; return 2; }
    fi
    "${_TOMLQ_BIN}" -f "$1" "$2"
}
