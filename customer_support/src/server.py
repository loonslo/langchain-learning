"""把客服应用作为 HTTP 服务暴露出来。

复用 ``api.create_app`` 的 FastAPI 工厂，注入由 ``bootstrap`` 装配好的
``SupportApplication``。服务内部自带 SQLite 持久化会话，因此多轮对话可以跨
HTTP 请求保留上下文，无需额外状态存储。

启动方式（见 ``app.py`` 的 ``--serve`` 或 ``uv run support-assistant --serve``）：
    uv run uvicorn src.server:create_runtime_api --factory --reload --port 8000
"""

from __future__ import annotations

import uvicorn

from .api import create_app
from .bootstrap import build_application


def create_runtime_api():
    """FastAPI 工厂入口，供 ``uvicorn ...:create_runtime_api --factory`` 调用。"""

    application = build_application()
    return create_app(application)


def main(host: str = "127.0.0.1", port: int = 19100) -> None:
    """以开发服务器直接启动客服 API。

    默认端口 19100：Windows 上 8000/8080 常被 Hyper-V 保留（netsh 可见
    excludedportrange 7981-8080），19090 也可能被旧进程占用，故用较冷门的端口。
    """

    uvicorn.run(
        "src.server:create_runtime_api",
        factory=True,
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
