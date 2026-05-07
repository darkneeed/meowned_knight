from __future__ import annotations

from app.core.contracts import CliOptions, Operation
from app.core.i18n import t
from app.core.registry import build_service_catalog


def _operation_descriptions(lang: str) -> list[tuple[str, str]]:
    return [
        (operation.value, t(lang, f"operation.{operation.value}.description"))
        for operation in Operation
    ]


class MenuInterface:
    def __init__(self, manager, runtime) -> None:
        self.manager = manager
        self.runtime = runtime
        self.lang = runtime.config.language

    def run(self) -> int:
        registry = self.manager.registry
        print(t(self.lang, "menu.header"))
        print(t(self.lang, "menu.intro"))
        print()
        print(t(self.lang, "menu.services_title"))
        for code, name, description in build_service_catalog(self.lang):
            print(f"{code}. {name} - {description}")
        print()
        print(t(self.lang, "menu.operations_title"))
        for operation, description in _operation_descriptions(self.lang):
            print(f"- {operation}: {description}")
        while True:
            raw_code = input(t(self.lang, "menu.choose_service")).strip()
            if raw_code == "0":
                return 0
            if raw_code == "8":
                service_codes = []
                all_services = True
                print(t(self.lang, "menu.selected_all_services"))
            elif raw_code.isdigit() and int(raw_code) in registry:
                service_codes = [int(raw_code)]
                all_services = False
                service = registry[int(raw_code)]
                print(
                    t(
                        self.lang,
                        "menu.selected_service",
                        name=service.name,
                        description=t(self.lang, f"service.{service.code}.description"),
                    )
                )
            else:
                print(t(self.lang, "menu.invalid"))
                continue

            raw_operation = input(t(self.lang, "menu.choose_operation")).strip().lower()
            try:
                operation = Operation(raw_operation)
            except ValueError:
                print(t(self.lang, "menu.invalid"))
                continue

            options = CliOptions(
                operation=operation,
                service_codes=service_codes,
                all_services=all_services,
                log_level=self.runtime.config.log_level,
                lang=self.lang,
                dry_run=self.runtime.config.dry_run,
            )
            result = self.manager.execute(options)
            print(t(self.lang, "menu.done"))
            return result
