"""交互菜单：扫描 Installers、匹配配置、分组复选框与「全选本分组」展开。"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

import questionary

from detector import InstallDetector
from grouped_checkbox import ALL_SENTINEL, grouped_checkbox


class MenuItem:
    """单个菜单项。"""

    def __init__(
        self,
        filename: str,
        installer_path: Path,
        pkg_config: dict[str, Any],
        configured: bool,
        installed: bool,
    ):
        self.filename = filename
        self.installer_path = installer_path
        self.pkg_config = pkg_config
        self.configured = configured
        self.installed = installed

    @property
    def category(self) -> str:
        return self.pkg_config.get("category", "")

    @property
    def display_name(self) -> str:
        return self.pkg_config.get("name", self.filename)


def _relative_parts(path: Path, installers_dir: Path) -> tuple[str, str | None]:
    """相对 Installers 根：返回 (一级目录名, 二级子文件夹名或 None)。"""
    try:
        rel = path.relative_to(installers_dir)
    except ValueError:
        return path.parent.name, None
    parts = rel.parts
    if len(parts) < 2:
        return path.parent.name, None
    root = parts[0]
    sub = parts[1] if len(parts) >= 3 else None
    return root, sub


def scan_installers(
    installers_dir: Path,
    packages_config: dict[str, dict[str, Any]],
    detector: InstallDetector,
) -> list[MenuItem]:
    """递归扫描 Installers，返回 MenuItem 列表。"""
    items: list[MenuItem] = []
    if not installers_dir.exists():
        return items

    for path in sorted(installers_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in {".exe", ".msi", ".pkg", ".dmg", ".bat", ".cmd"}:
            continue

        base = packages_config.get(path.name)
        if base is None:
            root, sub = _relative_parts(path, installers_dir)
            pkg_config: dict[str, Any] = {"name": path.name, "category": root}
            if sub:
                pkg_config["menu_subfolder"] = sub
            configured = False
        else:
            pkg_config = dict(base)
            configured = True
            if not str(pkg_config.get("menu_subfolder", "")).strip():
                _, sub = _relative_parts(path, installers_dir)
                if sub:
                    pkg_config["menu_subfolder"] = sub

        installed = detector.is_installed(pkg_config) if configured else False
        items.append(
            MenuItem(
                filename=path.name,
                installer_path=path,
                pkg_config=pkg_config,
                configured=configured,
                installed=installed,
            )
        )

    return items


def _expand_checkbox_raw(
    raw: list[Any] | None,
    item_by_key: dict[str, MenuItem],
) -> list[MenuItem]:
    """将复选结果中的全选节点展开为具体路径键，并与单项合并去重。"""
    if not raw:
        return []
    keys: set[str] = set()
    for sel in raw:
        if isinstance(sel, tuple) and len(sel) == 2 and sel[0] == ALL_SENTINEL:
            for k in sel[1]:
                if k in item_by_key:
                    keys.add(k)
        elif isinstance(sel, str) and sel in item_by_key:
            keys.add(sel)
    # 稳定顺序：按 item_by_key 插入顺序不可靠，按路径排序
    ordered = sorted(keys, key=lambda k: item_by_key[k].display_name.lower())
    return [item_by_key[k] for k in ordered]


def build_menu(items: list[MenuItem], i18n: dict[str, str]) -> list[MenuItem]:
    """渲染分组复选框；子文件夹内提供「全选本分组」并展开为多个安装任务。"""
    if not items:
        return []

    grouped: dict[str, list[MenuItem]] = defaultdict(list)
    for it in items:
        grouped[it.category or i18n["category_unknown"]].append(it)

    choices: list[Any] = []
    item_by_key: dict[str, MenuItem] = {}

    for category in sorted(grouped.keys()):
        cat_items = grouped[category]
        by_sub: dict[str, list[MenuItem]] = defaultdict(list)
        for it in cat_items:
            sk = str(it.pkg_config.get("menu_subfolder", "")).strip()
            by_sub[sk].append(it)

        sub_keys: list[str] = []
        if "" in by_sub:
            sub_keys.append("")
        sub_keys.extend(sorted(k for k in by_sub if k != ""))

        choices.append(questionary.Separator(f"=== {category} ==="))

        for sk in sub_keys:
            group_items = sorted(
                by_sub[sk],
                key=lambda x: x.display_name.lower(),
            )
            if sk:
                choices.append(
                    questionary.Separator(
                        i18n["menu_subfolder_header"].format(name=sk)
                    )
                )
                path_keys = [str(it.installer_path) for it in group_items]
                if len(group_items) >= 2:
                    choices.append(
                        questionary.Choice(
                            title=f"  {i18n['menu_select_all']}",
                            value=(ALL_SENTINEL, tuple(path_keys)),
                            checked=False,
                            disabled=None,
                        )
                    )

            n = len(group_items)
            for idx, it in enumerate(group_items):
                tags: list[str] = []
                if it.installed:
                    tags.append(i18n["tag_installed"])
                if not it.configured:
                    tags.append(i18n["tag_unconfigured"])
                tag_str = " ".join(tags)
                label = f"{it.display_name} {tag_str}".strip()
                key = str(it.installer_path)
                item_by_key[key] = it

                if sk:
                    branch = "└─" if idx == n - 1 else "├─"
                    title = f"    {branch} {label}"
                else:
                    title = f"  {label}"

                choices.append(
                    questionary.Choice(
                        title=title,
                        value=key,
                        checked=False,
                        disabled=None,
                    )
                )

    raw_selected = grouped_checkbox(
        i18n["menu_prompt"],
        choices=choices,
    ).ask()

    return _expand_checkbox_raw(raw_selected, item_by_key)
