"""Windows 无控制台启动入口 — 双击此文件即可启动 GUI，不会弹出 CMD 窗口。"""
import sys

if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.FreeConsole()

from gui_main import run_gui

sys.exit(run_gui())
