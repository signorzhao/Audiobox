"""已安装状态检测。

策略：
- Windows：支持绝对路径检测 + VST 池遍历检测
- macOS / 其他平台：本期不参与检测，统一返回 False（保留扩展点）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


def _expand(path: str) -> str:
    return os.path.expandvars(os.path.expanduser(path))


class InstallDetector:
    def __init__(self, global_settings: dict[str, Any]):
        self.vst_paths: dict[str, list[str]] = global_settings.get("vst_paths", {})
        self.platform = sys.platform

    def is_installed(self, pkg_config: dict[str, Any]) -> bool:
        if self.platform != "win32":
            # macOS 暂不参与检测，留待后续扩展
            return False

        absolute = pkg_config.get("check_absolute_path")
        if absolute and Path(_expand(absolute)).exists():
            return True

        vst_file = pkg_config.get("check_vst_file")
        vst_format = pkg_config.get("vst_format")
        if vst_file and vst_format:
            for base in self.vst_paths.get(vst_format, []):
                candidate = Path(_expand(base)) / vst_file
                if candidate.exists():
                    return True

        return False
