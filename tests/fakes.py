from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path


class FakeBackupManager:
    def backup_file(self, path: Path) -> Path | None:
        return path


@dataclass
class FakeCommandResult:
    command: list[str]
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


class FakeSystem:
    managed_block_template = "# BEGIN HOSTCTL:{name}\n{content}# END HOSTCTL:{name}\n"

    def __init__(self, *, dry_run: bool = False, files: dict[str, str] | None = None, commands: dict[tuple[str, ...], FakeCommandResult] | None = None) -> None:
        self.dry_run = dry_run
        self.files = dict(files or {})
        self.command_map = dict(commands or {})
        self.recorded_commands: list[list[str]] = []
        self.is_real = False

    def is_linux(self) -> bool:
        return True

    def read_os_release(self) -> dict[str, str]:
        return {"ID": "ubuntu", "VERSION_ID": "24.04"}

    def run(self, command: list[str], check: bool = False) -> FakeCommandResult:
        self.recorded_commands.append(command)
        result = self.command_map.get(tuple(command), FakeCommandResult(command=command))
        if check and result.returncode != 0:
            raise RuntimeError(result.stderr or "command failed")
        return result

    def file_exists(self, path: str | Path) -> bool:
        return str(path) in self.files

    def read_text(self, path: str | Path) -> str:
        return self.files[str(path)]

    def write_text(self, path: str | Path, content: str, backup: bool = True) -> bool:
        key = str(path)
        if self.files.get(key) == content:
            return False
        if not self.dry_run:
            self.files[key] = content
        return True

    def remove_file(self, path: str | Path, backup: bool = True) -> bool:
        key = str(path)
        if key not in self.files:
            return False
        if not self.dry_run:
            del self.files[key]
        return True

    def replace_or_append_line(self, path: str | Path, pattern: str, replacement: str) -> bool:
        key = str(path)
        current = self.files.get(key, "")
        if replacement in current:
            return False
        if not self.dry_run:
            self.files[key] = f"{current}{replacement}\n" if current else f"{replacement}\n"
        return True

    def ensure_managed_block(self, path: str | Path, name: str, content: str) -> bool:
        key = str(path)
        block = self.managed_block_template.format(name=name, content=content)
        current = self.files.get(key, "")
        if block in current:
            return False
        if not self.dry_run:
            self.files[key] = f"{current}{block}" if current else block
        return True

    def remove_managed_block(self, path: str | Path, name: str) -> bool:
        key = str(path)
        current = self.files.get(key, "")
        begin = f"# BEGIN HOSTCTL:{name}\n"
        end = f"# END HOSTCTL:{name}\n"
        if begin not in current or end not in current:
            return False
        if not self.dry_run:
            start = current.index(begin)
            finish = current.index(end) + len(end)
            self.files[key] = current[:start] + current[finish:]
        return True


class FakeRuntime:
    def __init__(self, system: FakeSystem, *, dry_run: bool = False, language: str = "ru") -> None:
        self.system = system
        self.config = type(
            "Config",
            (),
            {
                "dry_run": dry_run,
                "language": language,
                "log_level": "INFO",
            },
        )()
        self.logger = logging.getLogger("mknight-test")
