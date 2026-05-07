"""Windows 无控制台启动入口 — 双击此文件即可启动 GUI，不会弹出 CMD 窗口。"""
from gui_main import run_gui
import sys

sys.exit(run_gui())
