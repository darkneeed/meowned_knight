from __future__ import annotations

from pathlib import Path

from app.core.contracts import ModuleResult, Operation


class BaseService:
    code: int
    name: str

    def execute(self, operation: Operation, runtime) -> ModuleResult:
        handler = getattr(self, operation.value)
        return handler(runtime)

    def apply(self, runtime) -> ModuleResult:
        result = self.activate(runtime)
        result.operation = Operation.APPLY
        return result

    def unsupported(self, operation: Operation, reason: str) -> ModuleResult:
        return ModuleResult(
            code=self.code,
            name=self.name,
            operation=operation,
            success=True,
            unsupported=True,
            message=reason,
        )

    @staticmethod
    def package_installed(runtime, package_name: str) -> bool:
        result = runtime.system.run(["dpkg-query", "-W", "-f=${Status}", package_name])
        return "install ok installed" in result.stdout

    @staticmethod
    def apt_install(runtime, packages: list[str]) -> bool:
        runtime.system.run(["apt-get", "update"], check=True)
        runtime.system.run(["apt-get", "install", "-y", *packages], check=True)
        return True

    @staticmethod
    def apt_remove(runtime, packages: list[str], purge: bool = False) -> bool:
        command = ["apt-get", "purge" if purge else "remove", "-y", *packages]
        runtime.system.run(command, check=True)
        return True

    @staticmethod
    def service_is_active(runtime, unit: str) -> bool:
        result = runtime.system.run(["systemctl", "is-active", unit])
        return result.returncode == 0 and result.stdout.strip() == "active"

    @staticmethod
    def service_is_enabled(runtime, unit: str) -> bool:
        result = runtime.system.run(["systemctl", "is-enabled", unit])
        return result.returncode == 0 and result.stdout.strip() == "enabled"

    @staticmethod
    def managed_file_info(path: str | Path) -> dict[str, str]:
        target = Path(path)
        return {"path": str(target), "exists": str(target.exists()).lower()}
