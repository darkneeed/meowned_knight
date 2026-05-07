from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from app.core.contracts import CliOptions, Operation
from app.core.i18n import t
from app.core.registry import build_service_catalog


def _maintenance_actions(lang: str) -> list[tuple[int, str, str]]:
    return [
        (9, "update", t(lang, "menu.maintenance.update")),
        (10, "reinstall", t(lang, "menu.maintenance.reinstall")),
        (11, "remove", t(lang, "menu.maintenance.remove")),
    ]


class MenuInterface:
    ANSI_RESET = "\033[0m"
    ANSI_BOLD = "\033[1m"
    ANSI_DIM = "\033[2m"
    ANSI_CYAN = "\033[96m"
    ANSI_GREEN = "\033[92m"
    ANSI_YELLOW = "\033[93m"
    ANSI_RED = "\033[91m"
    ANSI_WHITE = "\033[97m"

    def __init__(self, manager, runtime) -> None:
        self.manager = manager
        self.runtime = runtime
        self.lang = runtime.config.language
        self.color_enabled = self._supports_color()

    def _supports_color(self) -> bool:
        if os.environ.get("NO_COLOR"):
            return False
        if os.environ.get("TERM", "").lower() == "dumb":
            return False
        return sys.stdout.isatty()

    def _clear_screen(self) -> None:
        if not sys.stdout.isatty():
            return
        print("\033[2J\033[H", end="")

    def _paint(self, text: str, *styles: str) -> str:
        if not self.color_enabled or not styles:
            return text
        return f"{''.join(styles)}{text}{self.ANSI_RESET}"

    def _width(self) -> int:
        columns = shutil.get_terminal_size(fallback=(100, 20)).columns
        return max(72, min(columns, 110))

    def _rule(self, symbol: str = "─") -> str:
        return symbol * self._width()

    def _print_header(self) -> None:
        dry_run_state = t(self.lang, "menu.state_on" if self.runtime.config.dry_run else "menu.state_off")
        status_line = t(
            self.lang,
            "menu.status_line",
            mode=t(self.lang, "menu.mode_interactive"),
            language=self.lang.upper(),
            dry_run=dry_run_state,
        )

        print(self._paint(self._rule("="), self.ANSI_DIM))
        print(self._paint(t(self.lang, "menu.header"), self.ANSI_BOLD, self.ANSI_WHITE))
        print(self._paint(t(self.lang, "menu.subtitle"), self.ANSI_CYAN))
        print(self._paint(status_line, self.ANSI_DIM))
        print(self._paint(self._rule("-"), self.ANSI_DIM))
        print(self._paint(t(self.lang, "menu.examples_title"), self.ANSI_BOLD, self.ANSI_CYAN))
        print(f"  {t(self.lang, 'parser.example.activate_all')}")
        print(f"  {t(self.lang, 'parser.example_status')}")
        print(f"  {t(self.lang, 'parser.example_dry_run')}")
        print(self._paint(self._rule("-"), self.ANSI_DIM))
        print(t(self.lang, "menu.intro"))
        print()

    def _print_services(self) -> None:
        print(self._paint(t(self.lang, "menu.services_title"), self.ANSI_BOLD, self.ANSI_CYAN))
        for code, name, description in build_service_catalog(self.lang):
            print(f"  {self._paint(f'{code})', self.ANSI_CYAN)} {self._paint(name, self.ANSI_BOLD, self.ANSI_WHITE)}")
            print(f"     {self._paint(description, self.ANSI_DIM)}")
        print()

    def _print_operations(self) -> None:
        print(self._paint(t(self.lang, "menu.default_action_title"), self.ANSI_BOLD, self.ANSI_CYAN))
        print(f"  - {t(self.lang, 'menu.default_action')}")
        print(f"  - {t(self.lang, 'menu.default_action_all')}")
        print()
        print(self._paint(t(self.lang, "menu.maintenance_title"), self.ANSI_BOLD, self.ANSI_CYAN))
        for code, name, description in _maintenance_actions(self.lang):
            print(f"  {self._paint(f'{code})', self.ANSI_YELLOW)} {self._paint(name, self.ANSI_BOLD, self.ANSI_WHITE)}")
            print(f"     {self._paint(description, self.ANSI_DIM)}")
        print()
        print(self._paint(t(self.lang, "menu.tip"), self.ANSI_YELLOW))

    def _maintenance_scripts(self) -> dict[str, list[str]]:
        project_root = Path(self.runtime.config.project_root)
        install_script = project_root / "install.sh"
        uninstall_script = project_root / "uninstall.sh"
        return {
            "update": ["bash", str(install_script)],
            "reinstall": ["bash", str(install_script), "--reinstall"],
            "remove": ["bash", str(uninstall_script), "--yes"],
        }

    def _run_maintenance(self, action_name: str) -> int:
        print(self._paint(t(self.lang, "menu.selected_maintenance", name=action_name), self.ANSI_GREEN))

        if action_name == "remove":
            confirmation = input(self._paint(t(self.lang, "menu.remove.confirm"), self.ANSI_BOLD, self.ANSI_RED)).strip()
            if confirmation != "DELETE":
                print(self._paint(t(self.lang, "menu.remove.cancelled"), self.ANSI_YELLOW))
                return 0

        print(self._paint(t(self.lang, "menu.maintenance.running", name=action_name), self.ANSI_CYAN))
        command = self._maintenance_scripts()[action_name]
        env = os.environ.copy()
        env["MKNIGHT_INSTALL_DIR"] = str(self.runtime.config.project_root)
        completed = subprocess.run(command, check=False, env=env)
        if completed.returncode == 0:
            print(self._paint(t(self.lang, "menu.maintenance.success"), self.ANSI_GREEN, self.ANSI_BOLD))
        else:
            print(self._paint(t(self.lang, "menu.maintenance.failure"), self.ANSI_RED, self.ANSI_BOLD))
        return completed.returncode

    def run(self) -> int:
        registry = self.manager.registry
        maintenance_actions = {code: name for code, name, _ in _maintenance_actions(self.lang)}
        self._clear_screen()
        self._print_header()
        self._print_services()
        self._print_operations()
        while True:
            raw_code = input(self._paint(t(self.lang, "menu.choose_service"), self.ANSI_BOLD, self.ANSI_CYAN)).strip()
            if raw_code == "0":
                return 0
            if raw_code == "8":
                service_codes = []
                all_services = True
                print(self._paint(t(self.lang, "menu.selected_all_services"), self.ANSI_GREEN))
            elif raw_code.isdigit() and int(raw_code) in maintenance_actions:
                return self._run_maintenance(maintenance_actions[int(raw_code)])
            elif raw_code.isdigit() and int(raw_code) in registry:
                service_codes = [int(raw_code)]
                all_services = False
                service = registry[int(raw_code)]
                print(
                    self._paint(
                        t(
                            self.lang,
                            "menu.selected_service",
                            name=service.name,
                            description=t(self.lang, f"service.{service.code}.description"),
                        ),
                        self.ANSI_GREEN,
                    )
                )
            else:
                print(self._paint(t(self.lang, "menu.invalid"), self.ANSI_RED))
                continue

            options = CliOptions(
                operation=Operation.APPLY,
                service_codes=service_codes,
                all_services=all_services,
                log_level=self.runtime.config.log_level,
                lang=self.lang,
                dry_run=self.runtime.config.dry_run,
            )
            result = self.manager.execute(options)
            print(self._paint(t(self.lang, "menu.done"), self.ANSI_GREEN, self.ANSI_BOLD))
            return result
