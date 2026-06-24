"""
Day 56 · 认证 + 多租户 + 限流
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目（企业第一梯队）

上线给真实用户用，三件必须有：
1. 认证：没带合法 token 调不通（JWT / API key）。
2. 多租户：A 租户绝对查不到 B 租户数据——隔离落到数据层（按租户分库），不是 if 判断。
3. 限流：单租户调用频率封顶，防一个客户打爆服务和成本。

实现在 capstone/auth.py（签发/校验 JWT、按租户分 Chroma 目录、滑动窗口限流），
对外服务在 capstone/api_enterprise.py。本驱动跑 auth.py 的签发+隔离+限流演示。

依赖：pip install "python-jose[cryptography]"
==========================================================
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    print("== 认证 + 多租户隔离 + 限流演示 ==")
    subprocess.run([sys.executable, "auth.py"], cwd=ROOT / "capstone")
    print("\n起企业版服务验证 401/429/隔离：uvicorn capstone.api_enterprise:app --reload")
    print("验收：无 token 调 /v1/chat → 401；超频 → 429；A 租户查不到 B 租户数据。")
    print("要点：多租户强隔离 = 物理分库，不是查询时加个 tenant 条件（写漏一行就串）。")
