from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Operation(StrEnum):
    APPLY = "apply"
    INSTALL = "install"
    UNINSTALL = "uninstall"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    STATUS = "status"
    INFO = "info"


@dataclass(slots=True)
class CliOptions:
    operation: Operation | None
    service_codes: list[int]
    all_services: bool
    log_level: str
    lang: str
    dry_run: bool
    interactive: bool = False


@dataclass(slots=True)
class ModuleResult:
    code: int
    name: str
    operation: Operation
    success: bool
    changed: bool = False
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    unsupported: bool = False
    needs_reboot: bool = False

    def summary_line(self) -> str:
        status = "OK" if self.success else "FAIL"
        if self.unsupported:
            status = "SKIP"
        return f"[{status}] {self.code}={self.name} {self.operation.value}: {self.message}"
