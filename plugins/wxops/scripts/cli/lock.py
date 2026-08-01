#!/usr/bin/env python3
# GEB-L3
# Input: caller, project conventions, and local dependencies
# Output: behavior defined by scripts/cli/lock.py
# Pos: plugins/wxops/scripts/cli/lock.py
"""同号 browser-profile 并发锁：login 与拉数互斥。"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

try:
    import fcntl
except ImportError:  # Windows 等无 fcntl
    fcntl = None  # type: ignore[assignment]


class ProfileLockError(RuntimeError):
    """browser-profile 已被其他进程占用。"""


class ProfileLock:
    """持有 flock 的锁对象；进程退出时 OS 自动释放。"""

    def __init__(self, path: Path, fd: int, noop: bool = False) -> None:
        self.path = path
        self.fd = fd
        self.noop = noop
        self._released = False

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        if self.noop:
            return
        try:
            if fcntl is not None:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass

    def __enter__(self) -> ProfileLock:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


def _read_lock_pid(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8").strip()
        if text:
            return text.split()[0]
    except Exception:
        pass
    return "未知"


def acquire_profile_lock(workspace: Path) -> ProfileLock:
    """返回持有 fd 的锁对象；调用方需在命令生命周期内持有引用。"""
    lock_path = workspace / "browser-profile.lock"
    workspace.mkdir(parents=True, exist_ok=True)

    if fcntl is None:
        # Windows 降级：不真正互斥，仅提示
        print(
            "⚠ 当前平台无 fcntl，browser-profile 并发锁已降级为 no-op"
            "（多进程同号仍可能冲突）",
            file=sys.stderr,
        )
        return ProfileLock(lock_path, -1, noop=True)

    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, OSError):
        os.close(fd)
        pid = _read_lock_pid(lock_path)
        if pid == "未知":
            msg = (
                f"账号浏览器登录态正被进程 {pid} 使用（login 与拉数互斥）。\n"
                f"请检查是否有残留 wxops 进程。\n"
                f"锁文件：{lock_path.resolve()}"
            )
        else:
            msg = (
                f"账号浏览器登录态正被进程 {pid} 使用（login 与拉数互斥）。\n"
                f"请等待该进程结束后重试；若确认该进程已卡死，可先 kill {pid} 再重试。\n"
                f"锁文件：{lock_path.resolve()}"
            )
        raise ProfileLockError(msg) from None

    try:
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, f"{os.getpid()}\n".encode("utf-8"))
        os.fsync(fd)
    except OSError:
        pass

    return ProfileLock(lock_path, fd, noop=False)


@contextmanager
def profile_lock(workspace: Path) -> Iterator[ProfileLock]:
    """with 语法糖，退出时释放。"""
    lock = acquire_profile_lock(workspace)
    try:
        yield lock
    finally:
        lock.release()
