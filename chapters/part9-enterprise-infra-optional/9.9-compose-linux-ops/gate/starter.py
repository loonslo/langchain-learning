"""L5.7 扩展 · 部署前配置检查 · 闭卷骨架

规则：只读本文件和本章 README 的 gate 任务书；通过 gate 之前不要打开
src/enterprise_support/runtime.py。实现 configuration_errors，然后运行：

    python chapters/part9-enterprise-infra-optional/9.9-compose-linux-ops/gate/gate_check.py
"""

from __future__ import annotations


def configuration_errors(settings: dict) -> tuple[str, ...]:
    """返回启动前配置错误（空元组=通过）。

    settings: database_url/redis_url/qdrant_url/app_env。
    校验：
    - database_url 以 postgresql:// 开头；
    - redis_url 以 redis:// 开头；
    - qdrant_url 是 http(s)://；
    - app_env=production 时 database_url 不得含 change-me。
    只做形状检查，不验证连通性。
    """
    raise NotImplementedError("实现配置检查")
