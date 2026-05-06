"""安装执行引擎：排序、调用 subprocess、运行 post_install_cmd、推进进度条。"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from logger import ErrorLogger
from menu import MenuItem


# Windows MSI/installer 返回码 3010 表示成功但需要重启
_SUCCESS_CODES = {0, 3010}


@dataclass
class InstallResult:
    name: str
    success: bool
    return_code: int | None
    help_text: str
    skipped: bool = False


def _sort_by_priority(items: list[MenuItem]) -> list[MenuItem]:
    """is_priority=true 的排在最前，保持稳定排序。"""
    priority = [it for it in items if it.pkg_config.get("is_priority")]
    rest = [it for it in items if not it.pkg_config.get("is_priority")]
    return priority + rest


def _build_command(item: MenuItem) -> str:
    """根据当前平台拼接安装命令。"""
    if sys.platform == "win32":
        args = item.pkg_config.get("win32_args", "")
    elif sys.platform == "darwin":
        args = item.pkg_config.get("darwin_args", "")
    else:
        args = ""
    return f'"{item.installer_path}" {args}'.strip()


class Executor:
    def __init__(
        self,
        i18n: dict[str, str],
        logger: ErrorLogger,
        console: Console | None = None,
    ):
        self.i18n = i18n
        self.logger = logger
        self.console = console or Console()

    def run(
        self,
        items: list[MenuItem],
        *,
        show_progress: bool = True,
        on_item_begin: Callable[[int, int, MenuItem], None] | None = None,
        on_item_end: Callable[[int, int], None] | None = None,
    ) -> list[InstallResult]:
        if not items:
            return []

        ordered = _sort_by_priority(items)
        results: list[InstallResult] = []
        n = len(ordered)

        if not show_progress:
            for i, item in enumerate(ordered):
                if on_item_begin:
                    on_item_begin(i, n, item)
                results.append(self._install_one(item))
                if on_item_end:
                    on_item_end(i, n)
            return results

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            total_task = progress.add_task(
                f"[yellow]{self.i18n['progress_total']}", total=n
            )

            for i, item in enumerate(ordered):
                if on_item_begin:
                    on_item_begin(i, n, item)
                desc = self.i18n["progress_current"].format(app_name=item.display_name)
                progress.update(total_task, description=f"[cyan]{desc}")
                results.append(self._install_one(item))
                if on_item_end:
                    on_item_end(i, n)
                progress.advance(total_task)

        return results

    def _install_one(self, item: MenuItem) -> InstallResult:
        cmd = _build_command(item)
        help_text = item.pkg_config.get("help_text", "")

        if not item.installer_path.exists():
            self.logger.log_failure(
                app_name=item.display_name,
                cmd=cmd,
                return_code=None,
                exception=f"installer not found: {item.installer_path}",
            )
            return InstallResult(
                name=item.display_name,
                success=False,
                return_code=None,
                help_text=help_text or self.i18n["error_installer_missing"].format(
                    path=str(item.installer_path)
                ),
            )

        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
            )
        except Exception as exc:  # noqa: BLE001 - 顶层兜底
            self.logger.log_failure(
                app_name=item.display_name,
                cmd=cmd,
                return_code=None,
                exception=repr(exc),
            )
            return InstallResult(
                name=item.display_name,
                success=False,
                return_code=None,
                help_text=help_text,
            )

        success = proc.returncode in _SUCCESS_CODES
        if not success:
            self.logger.log_failure(
                app_name=item.display_name,
                cmd=cmd,
                return_code=proc.returncode,
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
            )
            return InstallResult(
                name=item.display_name,
                success=False,
                return_code=proc.returncode,
                help_text=help_text,
            )

        # 成功后执行 post_install_cmd 钩子
        post_cmd = item.pkg_config.get("post_install_cmd")
        if post_cmd:
            try:
                subprocess.run(post_cmd, shell=True, capture_output=True, text=True)
            except Exception as exc:  # noqa: BLE001 - hook 失败不影响主流程
                self.logger.log_failure(
                    app_name=f"{item.display_name} (post_install)",
                    cmd=post_cmd,
                    return_code=None,
                    exception=repr(exc),
                )

        return InstallResult(
            name=item.display_name,
            success=True,
            return_code=proc.returncode,
            help_text=help_text,
        )
