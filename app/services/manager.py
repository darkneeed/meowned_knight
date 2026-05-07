from __future__ import annotations

from app.core.contracts import CliOptions, ModuleResult
from app.core.i18n import t
from app.core.registry import build_service_registry


class ServiceManager:
    def __init__(self, runtime) -> None:
        self.runtime = runtime
        self.registry = build_service_registry()

    def execute(self, options: CliOptions) -> int:
        service_codes = sorted(self.registry) if options.all_services else options.service_codes
        results: list[ModuleResult] = []
        for code in service_codes:
            service = self.registry[code]
            result = service.execute(options.operation, self.runtime)
            results.append(result)
            print(result.summary_line())
            if result.details:
                for key, value in result.details.items():
                    print(f"  {key}: {value}")

        changed = any(result.changed for result in results)
        if self.runtime.config.dry_run:
            print(t(self.runtime.config.language, "summary.dry_run"))
        elif changed:
            print(t(self.runtime.config.language, "summary.changed"))
        else:
            print(t(self.runtime.config.language, "summary.unchanged"))
        return 0 if all(result.success for result in results) else 1
