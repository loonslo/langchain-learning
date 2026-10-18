"""L5.5 容器与配置 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
docker_examples.py。实现下面三个函数，然后运行：

    python chapters/part5-production/5.5-docker-packaging/gate/gate_check.py
"""

from __future__ import annotations


def render_dockerfile() -> str:
    """返回生产可用的 Dockerfile 文本。

    至少包含：FROM python 基础镜像、WORKDIR /app、先 COPY requirements 再
    RUN pip install、再 COPY . .、EXPOSE 8000、CMD 启动 5.1 服务且 host=0.0.0.0。
    不得包含明文密钥/ADD 远端 URL。
    """
    raise NotImplementedError("实现 Dockerfile")


def render_dockerignore() -> str:
    """返回 .dockerignore 文本，至少排除 .env、.git/、.venv/、__pycache__/。"""
    raise NotImplementedError("实现 .dockerignore")


def audit(text: str) -> list[str]:
    """检查 Dockerfile 的安全/结构问题，返回问题列表（无问题 []）。

    至少检查：
    - 缺 FROM / CMD / EXPOSE；
    - 含 .env 或 SECRET/API_KEY 明文；
    - 用 ADD 拉远端 URL；
    - 以 root 运行（缺少 USER 非 root）。
    """
    raise NotImplementedError("实现 Dockerfile 审计")
