"""UAC 自动提权。仅 Windows 生效，其他平台直接通过。"""

from __future__ import annotations

import ctypes
import sys


def is_admin() -> bool:
    if sys.platform != "win32":
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ensure_admin(notice: str | None = None) -> None:
    """若非管理员，弹出 UAC 提权后退出当前进程。"""
    if sys.platform != "win32" or is_admin():
        return

    if notice:
        try:
            print(notice)
        except Exception:
            pass

    params = " ".join(f'"{a}"' for a in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    sys.exit(0)
