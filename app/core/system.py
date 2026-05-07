from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.state import BackupManager


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


class LocalSystem:
    managed_block_template = "# BEGIN HOSTCTL:{name}\n{content}# END HOSTCTL:{name}\n"

    def __init__(self, logger: logging.Logger, dry_run: bool, backup_manager: BackupManager) -> None:
        self.logger = logger
        self.dry_run = dry_run
        self.backup_manager = backup_manager
        self.is_real = True

    def is_linux(self) -> bool:
        return os.name == "posix"

    def read_os_release(self) -> dict[str, str]:
        path = Path("/etc/os-release")
        if not path.exists():
            return {}
        payload: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            payload[key] = value.strip().strip('"')
        return payload

    def run(self, command: list[str], check: bool = False) -> CommandResult:
        rendered = " ".join(command)
        self.logger.info("run %s", rendered)
        if self.dry_run:
            return CommandResult(command=command, returncode=0, stdout="", stderr="")
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
        result = CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"Command failed: {rendered}\n{result.stderr}")
        return result

    def command_exists(self, program: str) -> bool:
        return shutil.which(program) is not None

    def file_exists(self, path: str | Path) -> bool:
        return Path(path).exists()

    def read_text(self, path: str | Path) -> str:
        return Path(path).read_text(encoding="utf-8")

    def write_text(self, path: str | Path, content: str, backup: bool = True) -> bool:
        target = Path(path)
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current == content:
            return False
        if backup and target.exists():
            self.backup_manager.backup_file(target)
        self.logger.info("write %s", target)
        if self.dry_run:
            return True
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return True

    def remove_file(self, path: str | Path, backup: bool = True) -> bool:
        target = Path(path)
        if not target.exists():
            return False
        if backup:
            self.backup_manager.backup_file(target)
        self.logger.info("remove %s", target)
        if self.dry_run:
            return True
        target.unlink()
        return True

    def replace_or_append_line(self, path: str | Path, pattern: str, replacement: str) -> bool:
        target = Path(path)
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        regex = re.compile(pattern, flags=re.MULTILINE)
        if regex.search(current):
            new_text = regex.sub(replacement, current, count=1)
        else:
            separator = "" if current.endswith("\n") or not current else "\n"
            new_text = f"{current}{separator}{replacement}\n"
        return self.write_text(target, new_text)

    def ensure_managed_block(self, path: str | Path, name: str, content: str) -> bool:
        target = Path(path)
        current = target.read_text(encoding="utf-8") if target.exists() else ""
        block = self.managed_block_template.format(name=name, content=content)
        pattern = re.compile(
            rf"# BEGIN HOSTCTL:{re.escape(name)}\n.*?# END HOSTCTL:{re.escape(name)}\n?",
            flags=re.DOTALL,
        )
        if pattern.search(current):
            new_text = pattern.sub(block, current)
        else:
            separator = "" if current.endswith("\n") or not current else "\n"
            new_text = f"{current}{separator}{block}"
        return self.write_text(target, new_text)

    def remove_managed_block(self, path: str | Path, name: str) -> bool:
        target = Path(path)
        if not target.exists():
            return False
        current = target.read_text(encoding="utf-8")
        pattern = re.compile(
            rf"\n?# BEGIN HOSTCTL:{re.escape(name)}\n.*?# END HOSTCTL:{re.escape(name)}\n?",
            flags=re.DOTALL,
        )
        new_text = pattern.sub("\n", current).strip("\n")
        if new_text:
            new_text += "\n"
        if new_text == current:
            return False
        return self.write_text(target, new_text)

