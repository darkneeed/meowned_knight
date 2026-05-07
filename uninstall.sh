#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCHER_PATH="/usr/local/bin/mknight"
ASSUME_YES=0

if [[ "${1:-}" == "--yes" ]]; then
  ASSUME_YES=1
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "uninstall.sh must run as root. Re-run with sudo." >&2
  exit 1
fi

if [[ "${ASSUME_YES}" -ne 1 ]]; then
  read -r -p "Remove mknight from this host? [y/N]: " CONFIRM
  if [[ "${CONFIRM}" != "y" && "${CONFIRM}" != "Y" ]]; then
    echo "Uninstall cancelled."
    exit 0
  fi
fi

rm -f "${LAUNCHER_PATH}"
cd /
rm -rf "${PROJECT_DIR}"

echo "mknight removed from ${PROJECT_DIR}"
