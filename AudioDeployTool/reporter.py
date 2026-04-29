"""结果报告：使用 Rich Table 展示安装汇总。"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from executor import InstallResult


def render_report(
    results: list[InstallResult],
    i18n: dict[str, str],
    log_path: str | None,
    console: Console | None = None,
) -> None:
    console = console or Console()
    if not results:
        return

    table = Table(
        title=f"🛠️  {i18n['report_title']}",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column(i18n["col_app"], style="dim", overflow="fold")
    table.add_column(i18n["col_status"])
    table.add_column(i18n["col_help"], width=50, overflow="fold")

    for res in results:
        if res.success:
            status = f"[green]✅ {i18n['status_success']}[/]"
        else:
            status = f"[red]❌ {i18n['status_failed']}[/]"
        table.add_row(res.name, status, res.help_text or "")

    console.print(table)

    has_failure = any(not r.success for r in results)
    if has_failure and log_path:
        console.print(f"[yellow]{i18n['msg_log_written'].format(path=log_path)}[/yellow]")

    console.print(f"\n[bold green]✨ {i18n['msg_done']}[/bold green]\n")
