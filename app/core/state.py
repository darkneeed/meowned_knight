from __future__ import annotations

import logging
import shutil
from datetime import datetime, UTC
from pathlib import Path


class BackupManager:
    def __init__(self, state_dir: Path, dry_run: bool, logger: logging.Logger) -> None:
        self.state_dir = state_dir
        self.dry_run = dry_run
        self.logger = logger
        self.session_dir = self.state_dir / "backups" / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def backup_file(self, path: Path) -> Path | None:
        if not path.exists():
            return None
        backup_target = self.session_dir / path.as_posix().lstrip("/")
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        if self.dry_run:
            self.logger.info("dry-run backup %s -> %s", path, backup_target)
            return backup_target
        shutil.copy2(path, backup_target)
        self.logger.info("backup %s -> %s", path, backup_target)
        return backup_target

