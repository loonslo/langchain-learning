"""Day 51-60 驱动脚本共用的安全子进程执行工具。"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 900.0
LOG = logging.getLogger("capstone.driver")


class DriverError(RuntimeError):
    """可预期的驱动执行错误；CLI 应把它转换为非零退出码。"""


def positive_timeout(value: str) -> float:
    """argparse 类型：只接受正数秒数。"""
    try:
        timeout = float(value)
    except ValueError as exc:
        raise ValueError("超时时间必须是数字") from exc
    if timeout <= 0:
        raise ValueError("超时时间必须大于 0")
    return timeout


def require_file(path: Path, purpose: str = "文件") -> Path:
    """确认入口文件存在，返回解析后的绝对路径。"""
    resolved = path.resolve()
    if not resolved.is_file():
        raise DriverError(f"{purpose}不存在：{resolved}")
    return resolved


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    label: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """无 shell 执行命令，失败/超时立即终止调用链。"""
    workdir = cwd.resolve()
    if not workdir.is_dir():
        raise DriverError(f"{label} 的工作目录不存在：{workdir}")
    if not command:
        raise DriverError(f"{label} 的命令为空")

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    LOG.info("开始：%s", label)
    try:
        result = subprocess.run(
            [str(part) for part in command],
            cwd=workdir,
            env=env,
            check=True,
            timeout=timeout,
            text=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise DriverError(f"{label} 超时（{timeout:g} 秒）") from exc
    except subprocess.CalledProcessError as exc:
        raise DriverError(f"{label} 失败（退出码 {exc.returncode}）") from exc
    except OSError as exc:
        raise DriverError(f"{label} 无法启动：{exc}") from exc
    LOG.info("完成：%s", label)
    return result


def run_python(
    arguments: Sequence[str],
    *,
    cwd: Path,
    label: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    """用当前解释器运行 Python 脚本或模块。"""
    return run_process(
        [sys.executable, *arguments],
        cwd=cwd,
        label=label,
        timeout=timeout,
    )


def configure_logging(verbose: bool = False) -> None:
    """为命令行驱动配置简洁、可检索的日志。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def cli_error(exc: DriverError) -> int:
    """记录预期错误并返回稳定的 CLI 失败码。"""
    LOG.error("%s", exc)
    return 1
