#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER_PATH="/usr/local/bin/mknight"
INSTALL_ONLY=0

if [[ "${1:-}" == "--install-only" ]]; then
  INSTALL_ONLY=1
  shift
fi

install_launcher() {
  cat > "${LAUNCHER_PATH}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="${PROJECT_DIR}"
exec "\${PROJECT_DIR}/.venv/bin/mknight" "\$@"
EOF
  chmod 755 "${LAUNCHER_PATH}"
}

if [[ "${EUID}" -ne 0 ]]; then
  echo "mknight must run as root. Re-run with sudo." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
  export PATH="${HOME}/.local/bin:${PATH}"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

cd "${PROJECT_DIR}"
uv sync
install_launcher
if [[ "${INSTALL_ONLY}" -eq 1 ]]; then
  echo "mknight installed to ${LAUNCHER_PATH}"
  exit 0
fi
exec "${PROJECT_DIR}/.venv/bin/mknight" "$@"
