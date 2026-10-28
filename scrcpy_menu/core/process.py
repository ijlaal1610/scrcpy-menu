"""Robust process execution and non-blocking real-time log streaming for scrcpy."""

import os
import sys
import time
import signal
import threading
import subprocess
from collections import deque
from typing import List, Callable, Optional


class ScrcpyProcessManager:
    """Manages scrcpy subprocess execution, stream draining, and real-time logging."""

    def __init__(self, max_log_lines: int = 1000):
        self.process: Optional[subprocess.Popen] = None
        self.max_log_lines = max_log_lines
        self.logs: deque = deque(maxlen=max_log_lines)
        self.log_callbacks: List[Callable[[str], None]] = []
        self.exit_callbacks: List[Callable[[int], None]] = []
        self._lock = threading.Lock()
        self._active_cmd: List[str] = []

    def register_log_callback(self, cb: Callable[[str], None]):
        """Register a callback invoked whenever a new output line arrives."""
        with self._lock:
            self.log_callbacks.append(cb)

    def register_exit_callback(self, cb: Callable[[int], None]):
        """Register a callback invoked when scrcpy process terminates."""
        with self._lock:
            self.exit_callbacks.append(cb)

    def is_running(self) -> bool:
        """Check if scrcpy process is currently active."""
        if self.process is None:
            return False
        return self.process.poll() is None

    def start(self, cmd: List[str]) -> bool:
        """Start scrcpy process with non-blocking stream readers."""
        if self.is_running():
            self._emit_log("[!] A scrcpy instance is already running. Please stop it first.\n")
            return False

        self._active_cmd = list(cmd)
        self._emit_log(f"[*] Starting scrcpy: {' '.join(cmd)}\n")

        try:
            # We merge stderr into stdout for combined chronological logging
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line-buffered
                encoding="utf-8",
                errors="replace"
            )

            # Spawn daemon thread to drain stream continuously
            t = threading.Thread(target=self._reader_thread, daemon=True)
            t.start()
            return True
        except Exception as e:
            self._emit_log(f"[!] Failed to launch process: {e}\n")
            self.process = None
            return False

    def _reader_thread(self):
        """Background worker draining stdout without blocking the OS buffer."""
        proc = self.process
        if not proc or not proc.stdout:
            return

        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                self._emit_log(line)
        except Exception as e:
            self._emit_log(f"[!] Log reader error: {e}\n")
        finally:
            try:
                proc.stdout.close()
            except Exception:
                pass

            rc = proc.wait()
            self._emit_log(f"[*] Process terminated with exit code {rc}\n")
            with self._lock:
                callbacks = list(self.exit_callbacks)
            for cb in callbacks:
                try:
                    cb(rc)
                except Exception:
                    pass

    def _emit_log(self, text: str):
        """Append log to ring buffer and notify callbacks."""
        with self._lock:
            self.logs.append(text)
            callbacks = list(self.log_callbacks)

        for cb in callbacks:
            try:
                cb(text)
            except Exception:
                pass

    def stop(self, timeout_sec: float = 3.0):
        """Gracefully stop running scrcpy process."""
        proc = self.process
        if not proc or proc.poll() is not None:
            return

        self._emit_log("[*] Terminating scrcpy...\n")
        try:
            proc.terminate()
            start_wait = time.time()
            while time.time() - start_wait < timeout_sec:
                if proc.poll() is not None:
                    break
                time.sleep(0.1)

            if proc.poll() is None:
                self._emit_log("[*] Process did not exit, forcing kill...\n")
                proc.kill()
        except Exception as e:
            self._emit_log(f"[!] Error stopping process: {e}\n")

    def get_logs(self) -> str:
        """Return all collected logs as a single string."""
        with self._lock:
            return "".join(self.logs)

    def clear_logs(self):
        """Clear log history buffer."""
        with self._lock:
            self.logs.clear()
