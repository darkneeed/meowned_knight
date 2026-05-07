from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    project_root: Path
    state_dir: Path
    log_file: Path
    language: str
    log_level: str
    dry_run: bool


def build_app_config(project_root: Path, language: str, log_level: str, dry_run: bool) -> AppConfig:
    state_dir = project_root / ".state"
    return AppConfig(
        project_root=project_root,
        state_dir=state_dir,
        log_file=project_root / "app.log",
        language=language,
        log_level=log_level.upper(),
        dry_run=dry_run,
    )

