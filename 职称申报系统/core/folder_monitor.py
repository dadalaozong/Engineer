"""文件到达监控 — 使用 watchdog 监听申报人资料目录。

每当有新文件出现时，通过 SSE 推送事件给前端。
"""
from __future__ import annotations
import os
import time
import threading
from datetime import datetime
from typing import Callable

_monitors: dict[int, "FolderMonitor"] = {}  # applicant_id → monitor
_lock = threading.Lock()


class FolderMonitor:
    def __init__(self, applicant_id: int, folder_path: str,
                 callback: Callable[[dict], None] | None = None):
        self.applicant_id = applicant_id
        self.folder_path  = folder_path
        self.callback     = callback
        self._observer    = None
        self._running     = False
        self.events: list[dict] = []

    def start(self):
        if self._running:
            return
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        monitor = self

        class _Handler(FileSystemEventHandler):
            def on_created(self, event):
                if event.is_directory:
                    return
                ev = {
                    "type": "created",
                    "path": event.src_path,
                    "filename": os.path.basename(event.src_path),
                    "time": datetime.now().strftime("%H:%M:%S"),
                }
                monitor.events.append(ev)
                if monitor.callback:
                    monitor.callback(ev)

            def on_modified(self, event):
                if event.is_directory:
                    return
                ev = {
                    "type": "modified",
                    "path": event.src_path,
                    "filename": os.path.basename(event.src_path),
                    "time": datetime.now().strftime("%H:%M:%S"),
                }
                monitor.events.append(ev)
                if monitor.callback:
                    monitor.callback(ev)

        self._observer = Observer()
        self._observer.schedule(_Handler(), self.folder_path, recursive=True)
        self._observer.start()
        self._running = True

    def stop(self):
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=3)
        self._running = False

    @property
    def running(self):
        return self._running


def start_monitor(applicant_id: int, folder_path: str) -> FolderMonitor:
    with _lock:
        if applicant_id in _monitors:
            m = _monitors[applicant_id]
            if m.running:
                return m
        m = FolderMonitor(applicant_id, folder_path)
        m.start()
        _monitors[applicant_id] = m
        return m


def stop_monitor(applicant_id: int):
    with _lock:
        m = _monitors.pop(applicant_id, None)
    if m:
        m.stop()


def get_monitor(applicant_id: int) -> FolderMonitor | None:
    return _monitors.get(applicant_id)


def list_monitors() -> list[dict]:
    with _lock:
        return [
            {"applicant_id": aid, "folder": m.folder_path,
             "running": m.running, "event_count": len(m.events)}
            for aid, m in _monitors.items()
        ]
