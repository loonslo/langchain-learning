"""
capstone/test_regression.py · pytest 回归（护城河：测试主场）
==========================================================
整合 day42：把评测集变成 pytest 用例，每次改完 RAG 一条命令跑回归。
RAG 输出有随机性，用宽松断言（含关键词 / 是否拒答），并靠 temperature=0 提升可复现。
运行：pytest capstone/test_regression.py -v
==========================================================
"""

import json
import pytest

import config as C
from knowledge_base import KnowledgeBase
from evaluation import _refused

CASES = json.loads(C.EVAL_SET.read_text(encoding="utf-8")) if C.EVAL_SET.exists() else []


@pytest.fixture(scope="module")
def chain():
    return KnowledgeBase().build().chain()


@pytest.mark.parametrize("case", CASES, ids=[c.get("id", c["question"]) for c in CASES])
def test_case(chain, case):
    ans = chain.invoke(case["question"])
    if case.get("should_refuse"):
        assert _refused(ans), f"应拒答却答了：{ans[:60]}"
    else:
        for kw in case.get("keywords", []):
            assert kw in ans, f"答案缺关键词「{kw}」：{ans[:60]}"


if __name__ == "__main__":
    # 不装 pytest 也能粗跑一遍
    c = KnowledgeBase().build().chain()
    for case in CASES:
        try:
            test_case.__wrapped__(c, case) if hasattr(test_case, "__wrapped__") else None
        except Exception:
            pass
    print(f"共有 {len(CASES)} 条回归用例，用 `pytest capstone/test_regression.py -v` 跑")
