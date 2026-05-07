#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-${MKNIGHT_REPO_URL:-}}"
INSTALL_DIR="${2:-${MKNIGHT_INSTALL_DIR:-/opt/mknight}}"
BRANCH="${MKNIGHT_BRANCH:-main}"

usage() {
  cat <<'EOF'
Usage:
  sudo bash install.sh <repo-url> [install-dir]

Examples:
  sudo bash install.sh https://github.com/example/mknight.git
  curl -fsSL <raw-install-url> | sudo bash -s -- https://github.com/example/mknight.git

Environment variables:
  MKNIGHT_REPO_URL     Repository URL if not passed as the first argument
  MKNIGHT_INSTALL_DIR  Target directory (default: /opt/mknight)
  MKNIGHT_BRANCH       Branch to clone (default: main)
EOF
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "install.sh must run as root. Re-run with sudo." >&2
    exit 1
  fi
}

ensure_supported_os() {
  if [[ ! -r /etc/os-release ]]; then
    echo "Unsupported host: /etc/os-release is missing." >&2
    exit 1
  fi

  # shellcheck disable=SC1091
  source /etc/os-release

  if [[ "${ID:-}" != "ubuntu" || "${VERSION_ID:-}" != "24.04" ]]; then
    echo "mknight supports only Ubuntu 24.04, got ${ID:-unknown} ${VERSION_ID:-unknown}." >&2
    exit 1
  fi
}

ensure_prerequisites() {
  apt-get update
  apt-get install -y git curl ca-certificates python3
}

clone_or_update_repo() {
  if [[ -d "${INSTALL_DIR}/.git" ]]; then
    git -C "${INSTALL_DIR}" fetch --depth 1 origin "${BRANCH}"
    git -C "${INSTALL_DIR}" checkout -B "${BRANCH}" "origin/${BRANCH}"
    return
  fi

  if [[ -e "${INSTALL_DIR}" ]]; then
    echo "Install directory exists but is not a git repository: ${INSTALL_DIR}" >&2
    exit 1
  fi

  git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${INSTALL_DIR}"
}

main() {
  require_root
  ensure_supported_os

  if [[ -z "${REPO_URL}" ]]; then
    usage >&2
    exit 1
  fi

  ensure_prerequisites
  clone_or_update_repo

  cd "${INSTALL_DIR}"
  ./run.sh --install-only

  cat <<EOF
mknight installed successfully.
Repository: ${REPO_URL}
Directory:  ${INSTALL_DIR}
Command:    /usr/local/bin/mknight

Try:
  sudo mknight --help
EOF
}

main "$@"
