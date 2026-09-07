"""一键启动客服助手：同时拉起后端 API 与前端静态站点。

用法：
    uv run python run.py                 # 默认后端 19100 / 前端 19888
    uv run python run.py --backend-port 19100 --frontend-port 19888
    uv run support-run                   # 等价于上面的默认行为（见 pyproject.toml）

后端为 FastAPI（src.server），前端为 frontend/index.html 的静态站点。
所有地址均绑定 127.0.0.1，仅本机访问，不受系统代理影响。
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import webbrowser

from urllib.request import urlopen
from urllib.error import URLError

import uvicorn

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")


def is_port_in_use(host: str, port: int) -> bool:
    """检测端口是否已被占用（避免启动时出现 WinError 10048 的崩溃式 traceback）。"""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0


def kill_port(port: int) -> bool:
    """尝试结束占用端口的进程（Windows 下通过 netsh/Get-NetTCPConnection）。"""

    try:
        out = subprocess.run(
            ["powershell", "-Command",
             f"(Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue).OwningProcess"],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except Exception:
        return False
    killed = False
    for pid in {p.strip() for p in out.split() if p.strip().isdigit()}:
        try:
            os.kill(int(pid), 9)
            killed = True
        except Exception:
            pass
    if killed:
        time.sleep(1)
    return killed


def wait_for_url(url: str, timeout: float = 60.0, interval: float = 1.0) -> bool:
    """轮询直到目标 URL 返回 2xx，或超时。"""

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=3) as resp:
                if 200 <= resp.status < 400:
                    return True
        except (URLError, OSError, ConnectionError):
            pass
        time.sleep(interval)
    return False


def run_backend(host: str, port: int):
    """以子进程方式运行 FastAPI 后端。"""

    # 复用 api.create_app 工厂；用 uvicorn 直接加载，避免重复写启动逻辑。
    config = uvicorn.Config(
        "src.server:create_runtime_api",
        factory=True,
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    server.run()


def run_frontend(host: str, port: int):
    """以子进程方式运行前端静态站点。"""

    import http.server
    import socketserver

    os.chdir(FRONTEND_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer((host, port), handler) as httpd:
        httpd.serve_forever()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="客服助手一键启动（后端 + 前端）")
    parser.add_argument("--host", default="127.0.0.1", help="绑定地址")
    parser.add_argument("--backend-port", type=int, default=19100, help="后端端口")
    parser.add_argument("--frontend-port", type=int, default=19888, help="前端站点端口")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args(argv)

    import threading

    backend_url = f"http://{args.host}:{args.backend_port}"
    frontend_url = f"http://{args.host}:{args.frontend_port}"

    # 端口预检：若被占用，先尝试清理，仍失败则给出明确提示后退出。
    for name, port in (("后端", args.backend_port), ("前端", args.frontend_port)):
        if is_port_in_use(args.host, port):
            print(f"[端口冲突] {name}端口 {port} 已被占用，尝试自动清理…", file=sys.stderr)
            if not kill_port(port) or is_port_in_use(args.host, port):
                print(
                    f"[失败] 无法释放端口 {port}。请先关闭占用该端口的进程，"
                    f"或用 --backend-port / --frontend-port 指定其他端口。",
                    file=sys.stderr,
                )
                return 1

    # 后端先起（加载 embedding/模型较慢），前台线程负责它。
    backend_thread = threading.Thread(
        target=run_backend, args=(args.host, args.backend_port), daemon=True
    )
    frontend_thread = threading.Thread(
        target=run_frontend, args=(args.host, args.frontend_port), daemon=True
    )

    print(f"[启动] 后端  -> {backend_url}")
    print(f"[启动] 前端  -> {frontend_url}")
    backend_thread.start()
    frontend_thread.start()

    # 等前端站点先就绪，再等后端（模型加载更慢）。
    fe_ok = wait_for_url(frontend_url + "/", timeout=20)
    be_ok = wait_for_url(backend_url + "/health", timeout=120)

    if not (fe_ok and be_ok):
        print("[警告] 服务未在预期时间内就绪，请查看上方日志。", file=sys.stderr)

    print()
    print("=" * 56)
    print("  客服助手已启动")
    print(f"  网页界面 : {frontend_url}/")
    print(f"  API 文档 : {backend_url}/docs")
    print("=" * 56)
    print("  按 Ctrl+C 退出（将同时关闭前后端）。")
    print()

    if not args.no_browser:
        time.sleep(1.5)
        webbrowser.open(frontend_url + "/")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[退出] 正在关闭服务…")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
