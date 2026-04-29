"""配置与语言包加载。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from packages_csv import load_packages_csv


class ConfigLoader:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.config_path = base_dir / "config.yaml"
        self.packages_csv_path = base_dir / "packages.csv"
        self.locales_dir = base_dir / "locales"
        self.installers_dir = base_dir / "Installers"
        self.logs_dir = base_dir / "logs"

    def load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        data.setdefault("global_settings", {})
        yaml_packages: dict[str, Any] = dict(data.get("packages") or {})

        csv_packages = load_packages_csv(self.packages_csv_path)
        if csv_packages is not None:
            merged = {**yaml_packages, **csv_packages}
            data["packages"] = merged
        else:
            data.setdefault("packages", yaml_packages)

        return data

    def load_locale(self, lang: str) -> dict[str, str]:
        locale_path = self.locales_dir / f"{lang}.json"
        if not locale_path.exists():
            raise FileNotFoundError(f"Locale file not found: {locale_path}")
        with locale_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def available_locales(self) -> list[str]:
        if not self.locales_dir.exists():
            return []
        return sorted(p.stem for p in self.locales_dir.glob("*.json"))
