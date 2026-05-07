#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER_PATH="/usr/local/bin/mknight"

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
exec "${PROJECT_DIR}/.venv/bin/mknight" "$@"
