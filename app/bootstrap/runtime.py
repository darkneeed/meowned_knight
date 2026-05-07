from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app.core.config import AppConfig, build_app_config
from app.core.contracts import CliOptions
from app.core.logging import configure_logging
from app.core.state import BackupManager
from app.core.system import LocalSystem


@dataclass(slots=True)
class Runtime:
    config: AppConfig
    system: LocalSystem


def build_runtime(cli_options: CliOptions) -> Runtime:
    project_root = Path(__file__).resolve().parents[2]
    config = build_app_config(
        project_root=project_root,
        language=cli_options.lang,
        log_level=cli_options.log_level,
        dry_run=cli_options.dry_run,
    )
    logger = configure_logging(level=config.log_level, log_file=config.log_file)
    backup_manager = BackupManager(state_dir=config.state_dir, dry_run=config.dry_run, logger=logger)
    system = LocalSystem(
        logger=logger,
        dry_run=config.dry_run,
        backup_manager=backup_manager,
    )
    return Runtime(config=config, system=system)


def ensure_supported_runtime(runtime: Runtime) -> None:
    system = runtime.system
    if not system.is_linux():
        raise SystemExit("mknight supports only local Linux hosts.")
    if os.geteuid() != 0:
        raise SystemExit("mknight must run as root.")
    release = system.read_os_release()
    os_id = release.get("ID", "")
    version = release.get("VERSION_ID", "")
    if os_id != "ubuntu" or version != "24.04":
        raise SystemExit(f"mknight supports only Ubuntu 24.04, got {os_id or 'unknown'} {version or 'unknown'}.")
