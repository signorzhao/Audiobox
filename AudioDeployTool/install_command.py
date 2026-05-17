"""安装命令解析：默认「安装包路径 + 静默参数」，可选整行 install_cmd。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def uses_install_cmd(pkg_config: dict[str, Any]) -> bool:
    return bool(str(pkg_config.get("install_cmd", "")).strip())


def find_installer_path(
    installers_dir: Path, filename: str, category: str = ""
) -> Path:
    """在 Installers 下查找文件；未找到时返回占位路径（供菜单键与 {installer} 占位）。"""
    if installers_dir.is_dir():
        matches = sorted(
            p
            for p in installers_dir.rglob(filename)
            if p.is_file() and not p.name.startswith(".")
        )
        if matches:
            return matches[0]
    cat = category.strip().lower()
    if cat:
        return installers_dir / cat / filename
    return installers_dir / filename


def expand_install_cmd(
    template: str, *, installer_path: Path, base_dir: Path
) -> str:
    """展开 install_cmd 中的 {installer}、{base} 占位符。"""
    return (
        template.replace("{installer}", str(installer_path))
        .replace("{base}", str(base_dir))
    )


def build_command(
    installer_path: Path, pkg_config: dict[str, Any], base_dir: Path
) -> str:
    custom = str(pkg_config.get("install_cmd", "")).strip()
    if custom:
        return expand_install_cmd(
            custom, installer_path=installer_path, base_dir=base_dir
        )
    if sys.platform == "win32":
        args = pkg_config.get("win32_args", "")
    elif sys.platform == "darwin":
        args = pkg_config.get("darwin_args", "")
    else:
        args = ""
    return f'"{installer_path}" {args}'.strip()


def requires_installer_file(pkg_config: dict[str, Any]) -> bool:
    return not uses_install_cmd(pkg_config)
