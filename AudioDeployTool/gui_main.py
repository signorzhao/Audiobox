"""PySide6 图形界面入口：树形多选 + 安装队列（复用 config / 扫描 / Executor）。"""

from __future__ import annotations

import locale
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config_loader import ConfigLoader, runtime_base_dir
from detector import InstallDetector
from executor import Executor, InstallResult
from logger import ErrorLogger
from menu import MenuItem, scan_installers
from privilege import ensure_admin, is_admin

DEFAULT_LANG = "zh-CN"
SUPPORTED_LANGS = ("zh-CN", "en-US")

_TREE_SELECTION_QSS = """
QTreeWidget { outline: none; }
QTreeWidget::item {
    padding: 2px 4px;
}
QTreeWidget::item:hover {
    background-color: transparent;
}
QTreeWidget::item:selected {
    background-color: transparent;
    color: palette(text);
}
QTreeWidget::item:selected:!active {
    background-color: transparent;
    color: palette(text);
}
QTreeWidget::branch:hover {
    background-color: transparent;
}
QTreeWidget::branch:selected {
    background-color: transparent;
}
"""

def _tree_row_visual() -> tuple[str, QColor, QColor]:
    """从系统 palette 派生分类/子文件夹颜色，自动适配深浅模式。"""
    pal = QApplication.instance().palette()
    cat_fg = pal.color(QPalette.ColorRole.Text)
    sub_fg = QColor(cat_fg)
    sub_fg.setAlphaF(0.65)
    return _TREE_SELECTION_QSS, cat_fg, sub_fg


def _tree_hierarchy_fonts(tree: QTreeWidget) -> tuple[QFont, QFont]:
    """分类 > 子文件夹 > 包名：字号递增 + 字重递减，与颜色/行底配合。"""
    base = QFont(tree.font())
    size = base.pointSize()
    if size <= 0:
        size = 9
        base.setPointSize(size)
    sub = QFont(base)
    sub.setPointSize(size + 4)
    sub.setWeight(QFont.Weight.Medium)
    cat = QFont(base)
    cat.setPointSize(size + 8)
    cat.setWeight(QFont.Weight.Bold)
    return cat, sub


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


def _format_report_plain(results: list[InstallResult], i18n: dict[str, str]) -> str:
    lines = [i18n["report_title"], "=" * 40]
    for res in results:
        st = i18n["status_success"] if res.success else i18n["status_failed"]
        lines.append(f"{res.name}: {st}")
        if res.help_text:
            lines.append(f"  {res.help_text}")
    lines.append("")
    lines.append(i18n["msg_done"])
    return "\n".join(lines)


def _build_tree_widget(items: list[MenuItem], i18n: dict[str, str]) -> tuple[QTreeWidget, dict[str, MenuItem]]:
    """按 category → menu_subfolder 建树；仅叶子可勾选。返回 tree 与 path→MenuItem。"""
    tree = QTreeWidget()
    tree.setHeaderLabels([i18n.get("gui_tree_column", "组件")])
    tree.setAlternatingRowColors(True)
    tree.setUniformRowHeights(False)
    tree.setIndentation(24)
    qss, cat_fg, sub_fg = _tree_row_visual()
    tree.setStyleSheet(qss)

    font_category, font_subfolder = _tree_hierarchy_fonts(tree)

    by_path: dict[str, MenuItem] = {str(it.installer_path): it for it in items}

    grouped: dict[str, list[MenuItem]] = defaultdict(list)
    for it in items:
        grouped[it.category or i18n["category_unknown"]].append(it)

    for category in sorted(grouped.keys()):
        cat_item = QTreeWidgetItem(tree, [category])
        cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
        cat_item.setFont(0, font_category)
        cat_item.setForeground(0, cat_fg)
        cat_item.setExpanded(True)

        by_sub: dict[str, list[MenuItem]] = defaultdict(list)
        for it in grouped[category]:
            sk = str(it.pkg_config.get("menu_subfolder", "")).strip()
            by_sub[sk].append(it)

        sub_keys: list[str] = []
        if "" in by_sub:
            sub_keys.append("")
        sub_keys.extend(sorted(k for k in by_sub if k != ""))

        for sk in sub_keys:
            group_items = sorted(
                by_sub[sk],
                key=lambda x: x.display_name.lower(),
            )
            if sk:
                sub_item = QTreeWidgetItem(cat_item, [i18n["gui_subfolder_label"].format(name=sk)])
                sub_item.setFlags(sub_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                sub_item.setFont(0, font_subfolder)
                sub_item.setForeground(0, sub_fg)
                sub_item.setExpanded(True)
                parent_for_leaves = sub_item
            else:
                parent_for_leaves = cat_item

            for it in group_items:
                tags: list[str] = []
                if it.installed:
                    tags.append(i18n["tag_installed"])
                if not it.configured:
                    tags.append(i18n["tag_unconfigured"])
                tag_str = (" " + " ".join(tags)) if tags else ""
                label = f"{it.display_name}{tag_str}"
                leaf = QTreeWidgetItem(parent_for_leaves, [label])
                leaf.setFlags(
                    leaf.flags()
                    | Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsEnabled
                )
                leaf.setCheckState(0, Qt.CheckState.Unchecked)
                leaf.setData(0, Qt.ItemDataRole.UserRole, str(it.installer_path))

    tree.resizeColumnToContents(0)
    return tree, by_path


def _set_all_leaves(tree: QTreeWidget, state: Qt.CheckState) -> None:
    def walk(item: QTreeWidgetItem) -> None:
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path is not None and isinstance(path, str):
            item.setCheckState(0, state)
        for i in range(item.childCount()):
            walk(item.child(i))

    for i in range(tree.topLevelItemCount()):
        walk(tree.topLevelItem(i))


def _collect_checked_items(tree: QTreeWidget, by_path: dict[str, MenuItem]) -> list[MenuItem]:
    out: list[MenuItem] = []

    def walk(item: QTreeWidgetItem) -> None:
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if path is not None and isinstance(path, str):
            if item.checkState(0) == Qt.CheckState.Checked:
                it = by_path.get(path)
                if it is not None:
                    out.append(it)
        for i in range(item.childCount()):
            walk(item.child(i))

    for i in range(tree.topLevelItemCount()):
        walk(tree.topLevelItem(i))
    return out


class InstallWorker(QThread):
    """在后台线程执行安装，避免阻塞 UI。"""

    finished_ok = Signal(object)
    failed = Signal(str)
    item_started = Signal(int, int, str)
    item_finished = Signal(int, int)

    def __init__(
        self,
        items: list[MenuItem],
        i18n: dict[str, str],
        logs_dir: Path,
    ):
        super().__init__()
        self._items = items
        self._i18n = i18n
        self._logs_dir = logs_dir

    def run(self) -> None:
        from rich.console import Console

        logger = ErrorLogger(self._logs_dir)
        try:
            console = Console(file=open(os.devnull, "w"), width=120, force_terminal=True)
            executor = Executor(self._i18n, logger, console=console)

            def on_begin(i: int, total: int, item: MenuItem) -> None:
                self.item_started.emit(i, total, item.display_name)

            def on_end(i: int, total: int) -> None:
                self.item_finished.emit(i + 1, total)

            results = executor.run(
                self._items,
                show_progress=False,
                on_item_begin=on_begin,
                on_item_end=on_end,
            )
            log_path = str(logger.path) if logger.path else None
            self.finished_ok.emit((results, log_path))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(repr(exc))
        finally:
            logger.close()


class MainWindow(QMainWindow):
    def __init__(
        self,
        items: list[MenuItem],
        i18n: dict[str, str],
        logs_dir: Path,
    ):
        super().__init__()
        self._i18n = i18n
        self._logs_dir = logs_dir
        self._worker: InstallWorker | None = None

        self.setWindowTitle(i18n.get("gui_window_title", i18n["title"]))
        self.resize(960, 640)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._tree, self._by_path = _build_tree_widget(items, i18n)
        layout.addWidget(self._tree, stretch=1)

        btn_row = QHBoxLayout()
        self._btn_select_all = QPushButton(i18n.get("gui_select_all", "全选"))
        self._btn_clear = QPushButton(i18n.get("gui_clear", "清除勾选"))
        self._btn_install = QPushButton(i18n.get("gui_install", "开始安装"))
        btn_row.addWidget(self._btn_select_all)
        btn_row.addWidget(self._btn_clear)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_install)
        layout.addLayout(btn_row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 1)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        self._progress.setFormat("%v / %m")
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status = QLabel("")
        layout.addWidget(self._status)

        self._btn_select_all.clicked.connect(
            lambda: _set_all_leaves(self._tree, Qt.CheckState.Checked)
        )
        self._btn_clear.clicked.connect(
            lambda: _set_all_leaves(self._tree, Qt.CheckState.Unchecked)
        )
        self._btn_install.clicked.connect(self._on_install_clicked)

    def _on_install_clicked(self) -> None:
        selected = _collect_checked_items(self._tree, self._by_path)
        if not selected:
            QMessageBox.information(
                self,
                self._i18n["title"],
                self._i18n.get("gui_no_selection", self._i18n["menu_no_selection"]),
            )
            return

        self._btn_install.setEnabled(False)
        self._btn_select_all.setEnabled(False)
        self._btn_clear.setEnabled(False)
        self._tree.setEnabled(False)
        n = len(selected)
        self._progress.setVisible(True)
        self._progress.setRange(0, n)
        self._progress.setValue(0)
        self._status.setText(self._i18n.get("gui_install_running", "正在安装…"))

        self._worker = InstallWorker(selected, self._i18n, self._logs_dir)
        self._worker.item_started.connect(self._on_install_item_started)
        self._worker.item_finished.connect(self._on_install_item_finished)
        self._worker.finished_ok.connect(self._on_install_finished)
        self._worker.failed.connect(self._on_install_failed)
        self._worker.start()

    def _on_install_item_started(self, index0: int, total: int, app_name: str) -> None:
        self._progress.setMaximum(total)
        fmt = self._i18n.get(
            "gui_install_progress",
            "正在安装 ({current}/{total})：{app_name}",
        )
        self._status.setText(
            fmt.format(current=index0 + 1, total=total, app_name=app_name)
        )

    def _on_install_item_finished(self, completed: int, total: int) -> None:
        self._progress.setMaximum(total)
        self._progress.setValue(completed)

    def _on_install_finished(self, payload: object) -> None:
        results, log_path = payload  # type: ignore[misc]
        self._reset_install_ui()
        text = _format_report_plain(results, self._i18n)
        if log_path and any(not r.success for r in results):
            text += "\n\n" + self._i18n["msg_log_written"].format(path=log_path)

        dlg = QDialog(self)
        dlg.setWindowTitle(self._i18n.get("gui_report_title", self._i18n["report_title"]))
        v = QVBoxLayout(dlg)
        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText(text)
        v.addWidget(te)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        bb.accepted.connect(dlg.accept)
        v.addWidget(bb)
        dlg.resize(560, 420)
        dlg.exec()

    def _on_install_failed(self, msg: str) -> None:
        self._reset_install_ui()
        QMessageBox.critical(self, self._i18n["title"], msg)

    def _reset_install_ui(self) -> None:
        self._progress.setVisible(False)
        self._progress.setRange(0, 1)
        self._progress.setValue(0)
        self._status.setText("")
        self._btn_install.setEnabled(True)
        self._btn_select_all.setEnabled(True)
        self._btn_clear.setEnabled(True)
        self._tree.setEnabled(True)


def run_gui(lang: str | None = None, *, skip_uac: bool = False) -> int:
    """启动 Qt 事件循环；返回进程退出码。"""
    base_dir = runtime_base_dir()
    loader = ConfigLoader(base_dir)

    lang = lang or _detect_default_lang()
    try:
        i18n = loader.load_locale(lang)
    except FileNotFoundError:
        lang = DEFAULT_LANG
        i18n = loader.load_locale(lang)

    app = QApplication(sys.argv)

    if not skip_uac:
        if sys.platform == "win32" and not is_admin():
            QMessageBox.information(
                None,
                i18n.get("gui_uac_title", i18n["title"]),
                i18n.get("gui_uac_body", i18n["uac_request"]),
            )

        ensure_admin(notice=i18n["uac_request"])

    try:
        config = loader.load_config()
    except FileNotFoundError as exc:
        QMessageBox.critical(None, i18n["title"], str(exc))
        return 2

    detector = InstallDetector(config.get("global_settings", {}))
    items = scan_installers(loader.installers_dir, config.get("packages", {}), detector)

    if not items:
        QMessageBox.information(None, i18n["title"], i18n["no_installers_found"])
        return 0

    win = MainWindow(items, i18n, loader.logs_dir)
    win.show()
    return int(app.exec())


if __name__ == "__main__":
    sys.exit(run_gui())
