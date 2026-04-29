"""从 packages.csv 加载安装包配置（表格维护，替代大块 YAML）。"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def _truthy(cell: str) -> bool:
    s = cell.strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _strip_row(row: dict[str, str | None]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in row.items():
        if k is None:
            continue
        key = str(k).strip()
        if not key:
            continue
        out[key] = (v or "").strip() if v is not None else ""
    return out


def load_packages_csv(csv_path: Path) -> dict[str, dict[str, Any]] | None:
    """读取 packages.csv，返回 filename -> 包配置字典。

    若文件不存在或除表头外无有效行，返回 None（调用方沿用 YAML）。
    """
    if not csv_path.is_file():
        return None

    packages: dict[str, dict[str, Any]] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return None
        for raw in reader:
            row = _strip_row(raw)
            filename = row.get("filename", "").strip()
            if not filename or filename.startswith("#"):
                continue

            name = row.get("name", "").strip()
            category = row.get("category", "").strip()
            if not name or not category:
                continue

            pkg: dict[str, Any] = {
                "name": name,
                "category": category,
            }

            sub = row.get("menu_subfolder", "").strip()
            if sub:
                pkg["menu_subfolder"] = sub

            if row.get("is_priority", "").strip() and _truthy(row["is_priority"]):
                pkg["is_priority"] = True

            for key in (
                "win32_args",
                "darwin_args",
                "check_absolute_path",
                "check_vst_file",
                "vst_format",
                "post_install_cmd",
                "help_text",
            ):
                val = row.get(key, "").strip()
                if val:
                    pkg[key] = val

            packages[filename] = pkg

    if not packages:
        return None

    return packages
