from __future__ import annotations

import pytest

from app.core.contracts import Operation
from app.interfaces.cli.parser import build_parser, parse_cli


def test_parse_cli_interactive_when_no_args() -> None:
    options = parse_cli([])
    assert options.interactive is True
    assert options.operation is None


def test_parse_cli_supports_all_activate_dry_run() -> None:
    options = parse_cli(["--all", "--activate", "--dry-run", "--lang", "en"])
    assert options.interactive is False
    assert options.all_services is True
    assert options.operation is Operation.ACTIVATE
    assert options.dry_run is True
    assert options.lang == "en"


def test_parse_cli_rejects_multiple_actions() -> None:
    with pytest.raises(SystemExit):
        parse_cli(["1", "--install", "--status"])


def test_parse_cli_requires_service_or_all() -> None:
    with pytest.raises(SystemExit):
        parse_cli(["--status"])


def test_build_parser_help_includes_service_catalog_and_examples() -> None:
    help_text = build_parser("ru").format_help()

    assert "Каталог сервисов:" in help_text
    assert "1. Firewall" in help_text
    assert "Действия:" in help_text
    assert "hostctl --all --activate" in help_text
