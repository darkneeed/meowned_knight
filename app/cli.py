from __future__ import annotations

from app.bootstrap.runtime import build_runtime, ensure_supported_runtime
from app.interfaces.cli.parser import parse_cli
from app.interfaces.menu.menu import MenuInterface
from app.services.manager import ServiceManager


def main() -> int:
    cli_options = parse_cli()
    runtime = build_runtime(cli_options)
    manager = ServiceManager(runtime=runtime)

    if cli_options.interactive:
        ensure_supported_runtime(runtime)
        return MenuInterface(manager=manager, runtime=runtime).run()

    ensure_supported_runtime(runtime)
    return manager.execute(cli_options)
