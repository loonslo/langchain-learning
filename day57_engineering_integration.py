"""
Day 57 · 工程化接入（把阶段4 的能力挂进项目）
==========================================================
测试工程师转 AI 应用开发 · 阶段5 毕业项目

把阶段4 的重试/缓存/成本优化/安全/pytest 回归/trace 接进毕业项目。
这天不发明新东西，是"接线"：确认每个工程能力在项目里都有落点。

下表是接线清单——面试被问"你的工程化体现在哪"，照这个答，每条都指到一个文件。
==========================================================
"""

INTEGRATION = [
    ("重试 / 超时 / fallback", "Day42 day42_reliability.py", "模型调用层加 timeout + 指数退避重试"),
    ("缓存 + model routing",   "Day43 day43_cost_cache_routing.py", "重复问走缓存、简单问走便宜模型，省成本"),
    ("成本 / token 统计",      "capstone/monitoring.py", "每次请求记 token+成本，喂 Day62 监控"),
    ("安全 guardrails",        "Day47 day47_security_guardrails.py + Day64", "注入防护 + PII 脱敏 + 内容审核"),
    ("pytest 回归",            "capstone/test_regression.py", "评测集变 pytest 用例，一条命令跑回归"),
    ("trace 可观测",           "Day22 day22_langsmith_eval.py", "LangSmith 定位失败是检索还是生成"),
]


def check_pytest():
    """跑一遍项目回归集，确认工程化接线没把功能搞坏。"""
    import subprocess, sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent
    subprocess.run([sys.executable, "-m", "pytest", "capstone/test_regression.py", "-q"], cwd=ROOT)


if __name__ == "__main__":
    print("===== 工程化接线清单 =====")
    for cap, where, how in INTEGRATION:
        print(f"\n[{cap}]\n  落点：{where}\n  做法：{how}")
    print("\n===== 跑一遍回归确认没搞坏 =====")
    print("（需要 pytest + .env + 本地 embedding；跑：pytest capstone/test_regression.py -q）")
    # check_pytest()   # 取消注释即在本机跑
    print("\n要点：工程化是'接线'不是炫技——每个能力都要在项目里有落点、有回归兜底。")
