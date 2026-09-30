"""从本章启动服务；跨章依赖由 tools/run_chapter.py 设置。"""

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    # 默认只监听本机；放进容器时要用 --host 0.0.0.0，宿主机才访问得到（见 5.5）
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run("serve_fastapi:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
