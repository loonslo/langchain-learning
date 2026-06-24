"""
Day 51 · 毕业项目架构 + Git 协作工作流
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目（多日单元，不是 1 天）

从这天起把前面所有能力整合成一个跑在真实数据上、带企业特性、有公网地址的毕业项目。
代码主体在 `capstone/`，每个 dayNN 文件是"这天做哪块"的驱动/说明。

这天两件事：
1. 定项目结构，搭骨架，跑通空流程。
2. Git 协作：feature 分支 / commit 规范 / 开 PR / 自己 review 自己的 PR（不直接推 main）。
   为什么不直接推 main：PR 是留给团队和 CI 的检查点——Day58 的 CI 评测门禁就挂在 PR 上。
==========================================================
"""

ARCHITECTURE = """
capstone/
├── config.py            统一配置（复用根 common.py 的模型/embedding 工厂）
├── knowledge_base.py    加载→切割→混合检索→带溯源问答（Day12-17）
├── connector.py         真实数据接入 + 增量同步（Day54）
├── permissions.py       文档级权限过滤，检索层（Day55）
├── auth.py              JWT 认证 + 多租户 + 限流（Day56）
├── agent.py             LangGraph Agent + HITL 审批（Day28-36）
├── evaluation.py        自动化评测：指标+报告+失败库（Day18-27）
├── ci_gate.py           CI 评测门禁阈值检查（Day58）
├── monitoring.py        p95/p99 + 错误率 + 成本（Day62）
├── api.py / api_enterprise.py   FastAPI 服务（基础版 / 企业版）
├── test_regression.py   pytest 回归（Day48）
└── main.py              CLI 入口：build / ask / eval
.github/workflows/eval-gate.yml   PR 触发 pytest + 评测门禁（Day58）
"""

GIT_WORKFLOW = """
1. git switch -c feat/incremental-sync     # 开 feature 分支，不在 main 上改
2. 写代码 + 提交：git commit -m "feat: 增量同步 connector"   # commit 规范：type: 说明
3. git push -u origin feat/incremental-sync
4. 开 PR → 自己 review 一遍 diff（当成给别人看）→ CI 绿了再 merge
要点：main 永远可发布；所有改动走 PR，CI 评测门禁挡在合并前。
"""


def check_skeleton():
    """跑通空流程：能 import capstone 各模块就算骨架立住了。"""
    import importlib
    import sys
    from pathlib import Path
    cap = Path(__file__).resolve().parent / "capstone"
    sys.path.insert(0, str(cap))
    ok = []
    for m in ["config", "knowledge_base", "evaluation"]:
        try:
            importlib.import_module(m); ok.append(f"  [OK] {m}")
        except Exception as e:
            ok.append(f"  [X] {m}: {type(e).__name__}: {e}")
    return "\n".join(ok)


if __name__ == "__main__":
    print("===== 项目架构 =====")
    print(ARCHITECTURE)
    print("===== Git 协作工作流 =====")
    print(GIT_WORKFLOW)
    print("===== 骨架自检（能 import 各核心模块）=====")
    print(check_skeleton())
