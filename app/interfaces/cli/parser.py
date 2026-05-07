from __future__ import annotations

import argparse
import sys

from app.core.contracts import CliOptions, Operation
from app.core.i18n import t
from app.core.registry import build_service_catalog


SUPPORTED_CODES = [1, 2, 3, 4, 5, 6, 7]


def resolve_cli_language(argv: list[str] | None = None) -> str:
    tokens = list(sys.argv[1:] if argv is None else argv)
    for index, token in enumerate(tokens):
        if token == "--lang" and index + 1 < len(tokens) and tokens[index + 1] in {"ru", "en"}:
            return tokens[index + 1]
        if token.startswith("--lang="):
            _, _, value = token.partition("=")
            if value in {"ru", "en"}:
                return value
    return "ru"


def build_parser(lang: str = "ru") -> argparse.ArgumentParser:
    service_lines = [
        f"  {code}. {name} - {description}"
        for code, name, description in build_service_catalog(lang)
    ]
    operation_lines = [
        f"  --{operation.value}: {t(lang, f'operation.{operation.value}.description')}"
        for operation in Operation
    ]
    example_lines = [
        f"  {t(lang, 'parser.example.activate_all')}",
        f"  {t(lang, 'parser.example_status')}",
        f"  {t(lang, 'parser.example_dry_run')}",
    ]
    epilog = "\n".join(
        [
            t(lang, "parser.epilog.services"),
            *service_lines,
            "",
            t(lang, "parser.epilog.operations"),
            *operation_lines,
            "",
            t(lang, "parser.epilog.examples"),
            *example_lines,
        ]
    )
    parser = argparse.ArgumentParser(
        prog="hostctl",
        description=t(lang, "parser.description"),
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("services", nargs="*", type=int, metavar="SERVICE_CODE", help=t(lang, "parser.services.help"))
    parser.add_argument("--install", action="store_true", help=t(lang, "parser.install.help"))
    parser.add_argument("--uninstall", action="store_true", help=t(lang, "parser.uninstall.help"))
    parser.add_argument("--activate", action="store_true", help=t(lang, "parser.activate.help"))
    parser.add_argument("--deactivate", action="store_true", help=t(lang, "parser.deactivate.help"))
    parser.add_argument("--status", action="store_true", help=t(lang, "parser.status.help"))
    parser.add_argument("--info", action="store_true", help=t(lang, "parser.info.help"))
    parser.add_argument("--all", action="store_true", dest="all_services", help=t(lang, "parser.all.help"))
    parser.add_argument("--log-level", default="INFO", help=t(lang, "parser.log_level.help"))
    parser.add_argument("--lang", choices=["ru", "en"], default=lang, help=t(lang, "parser.lang.help"))
    parser.add_argument("--dry-run", action="store_true", help=t(lang, "parser.dry_run.help"))
    return parser


def parse_cli(argv: list[str] | None = None) -> CliOptions:
    lang = resolve_cli_language(argv)
    parser = build_parser(lang)
    args = parser.parse_args(argv)
    invalid_codes = sorted(set(args.services) - set(SUPPORTED_CODES))
    if invalid_codes:
        parser.error(
            t(lang, "parser.error.unsupported_service_codes", codes=", ".join(str(code) for code in invalid_codes))
        )

    action_flags = {
        Operation.INSTALL: args.install,
        Operation.UNINSTALL: args.uninstall,
        Operation.ACTIVATE: args.activate,
        Operation.DEACTIVATE: args.deactivate,
        Operation.STATUS: args.status,
        Operation.INFO: args.info,
    }
    selected_operations = [op for op, enabled in action_flags.items() if enabled]

    if not selected_operations:
        if args.services or args.all_services:
            parser.error(t(lang, "parser.error.operation_required"))
        return CliOptions(
            operation=None,
            service_codes=[],
            all_services=False,
            log_level=args.log_level,
            lang=args.lang,
            dry_run=args.dry_run,
            interactive=True,
        )

    if len(selected_operations) > 1:
        parser.error(t(lang, "parser.error.select_exactly_one_operation"))

    if not args.services and not args.all_services:
        parser.error(t(lang, "parser.error.provide_service_or_all"))

    return CliOptions(
        operation=selected_operations[0],
        service_codes=args.services,
        all_services=args.all_services,
        log_level=args.log_level,
        lang=args.lang,
        dry_run=args.dry_run,
    )
