"""错误日志：仅在安装失败时写入，按运行时间生成单独文件。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional


class ErrorLogger:
    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
        self._path: Optional[Path] = None
        self._fh = None

    @property
    def path(self) -> Optional[Path]:
        return self._path

    def _ensure_open(self) -> None:
        if self._fh is not None:
            return
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = self.logs_dir / f"error_{stamp}.log"
        self._fh = self._path.open("w", encoding="utf-8")
        self._fh.write(f"# Audio Deploy CLI error log @ {datetime.now().isoformat()}\n\n")

    def log_failure(
        self,
        app_name: str,
        cmd: str,
        return_code: int | None,
        stderr: str = "",
        stdout: str = "",
        exception: str = "",
    ) -> None:
        self._ensure_open()
        assert self._fh is not None
        self._fh.write(f"[{datetime.now().isoformat()}] FAILED: {app_name}\n")
        self._fh.write(f"  cmd        : {cmd}\n")
        self._fh.write(f"  return_code: {return_code}\n")
        if exception:
            self._fh.write(f"  exception  : {exception}\n")
        if stderr:
            self._fh.write(f"  stderr     :\n{stderr}\n")
        if stdout:
            self._fh.write(f"  stdout     :\n{stdout}\n")
        self._fh.write("-" * 60 + "\n")
        self._fh.flush()

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None
