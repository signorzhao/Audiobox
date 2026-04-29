"""Audio Deploy CLI - 主入口。"""

from __future__ import annotations

import argparse
import locale
import sys
from pathlib import Path

from rich.console import Console

from config_loader import ConfigLoader
from detector import InstallDetector
from executor import Executor
from logger import ErrorLogger
from menu import build_menu, scan_installers
from privilege import ensure_admin
from reporter import render_report

DEFAULT_LANG = "zh-CN"
SUPPORTED_LANGS = ("zh-CN", "en-US")


def _detect_default_lang() -> str:
    try:
        sys_lang, _ = locale.getlocale()
    except Exception:
        sys_lang = None
    if sys_lang and sys_lang.lower().startswith(("zh", "chinese")):
        return "zh-CN"
    if sys_lang and sys_lang.lower().startswith(("en", "english")):
        return "en-US"
    return DEFAULT_LANG


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audio Workstation Deploy CLI",
    )
    parser.add_argument(
        "--lang",
        choices=SUPPORTED_LANGS,
        default=None,
        help="Interface language (default: auto-detect)",
    )
    parser.add_argument(
        "--no-uac",
        action="store_true",
        help="Skip UAC elevation prompt (Windows only). Useful for dry-run / debugging.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    console = Console()

    base_dir = Path(__file__).parent.absolute()
    loader = ConfigLoader(base_dir)

    lang = args.lang or _detect_default_lang()
    try:
        i18n = loader.load_locale(lang)
    except FileNotFoundError:
        # 兜底回落到默认语言
        lang = DEFAULT_LANG
        i18n = loader.load_locale(lang)

    if not args.no_uac:
        ensure_admin(notice=i18n["uac_request"])

    try:
        config = loader.load_config()
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        return 2

    console.print(f"[bold cyan]{i18n['title']}[/bold cyan]\n")

    detector = InstallDetector(config.get("global_settings", {}))

    console.print(f"[dim]{i18n['scanning_installers']}[/dim]")
    items = scan_installers(loader.installers_dir, config.get("packages", {}), detector)

    if not items:
        console.print(f"[yellow]{i18n['no_installers_found']}[/yellow]")
        return 0

    selected = build_menu(items, i18n)
    if not selected:
        console.print(f"[yellow]{i18n['menu_no_selection']}[/yellow]")
        return 0

    error_logger = ErrorLogger(loader.logs_dir)
    try:
        executor = Executor(i18n=i18n, logger=error_logger, console=console)
        results = executor.run(selected)
    finally:
        error_logger.close()

    log_path = str(error_logger.path) if error_logger.path else None
    render_report(results, i18n, log_path=log_path, console=console)

    return 0 if all(r.success for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
