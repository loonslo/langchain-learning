"""
Day 48 · 把评测变成自动化回归测试（pytest）
==========================================================
测试工程师转 AI 应用开发  ★护城河：你最熟的主场★

Day17-20 的评测是手动跑、肉眼看。这节把它变成 pytest 用例：每次改完 RAG
（调了 chunk、换了 prompt、改了检索），一条命令跑回归，答错的立刻红灯。
普通开发很少给 LLM 应用写自动化测试——这正是测试背景的差异化优势。

知识点（前 3 条是原理，后 5 条是"能进 CI 的写法"）：
1. pytest fixture：整个会话只建一次库（scope="session"），embedding 模型只加载一次
2. 参数化 @pytest.mark.parametrize + ids：评测集变成一批独立、可读的用例
3. RAG 测试为什么不能用精确断言：模型输出有随机性，要用"包含关键词 / 是否拒答"
   这类宽松断言，并把 temperature 调到 0 提升可复现
4. 路径必须相对本文件：CI 里 pytest 的工作目录不一定是仓库根目录
5. 环境没配好 → skip（说明原因），质量退化 → fail；两者绝不能混成同一种红色。
   CI 里设 RAG_TEST_STRICT=1，让"环境没配好"也变成红灯，避免回归被静默跳过
6. 同一个问题只调一次模型（answer 缓存）：LLM 用例是花钱且慢的，断言可以有很多条
7. 关键词判定要归一化（全角/半角、大小写、空格）并支持"同义词任选其一"，
   否则测的是模型的措辞习惯，而不是它有没有答对
8. 失败留痕：跑完把结果写进 reports/day48_failures.json，下游 day26 诊断脚本能直接读

依赖：pip install pytest
运行：pytest day48_pytest_regression.py -v
   或：python day48_pytest_regression.py   （文件底部自带入口，免配置）
环境变量：
   RAG_TEST_STRICT=1        环境缺失时判失败而不是跳过（CI 建议开）
   RAG_TEST_LATENCY_MS=15000 单次问答延迟预算，超了算退化
==========================================================
"""

import json
import os
import time
import unicodedata
from pathlib import Path

import pytest

from common import EMBED_MODEL_PATH
from day12_rag_pdf_sources import build_retriever, build_rag_chain

# 路径一律相对本文件：CI 里 pytest 可能从任意目录启动，相对 cwd 的路径必炸
HERE = Path(__file__).resolve().parent
DOC_PATH = HERE / "test_doc.txt"
EXTRA_CASES = HERE / "day48_cases.json"          # 可选：失败用例库（只增不减），没有就跳过
FAILURE_LOG = HERE / "reports" / "day48_failures.json"

STRICT = os.getenv("RAG_TEST_STRICT") == "1"
LATENCY_BUDGET_MS = float(os.getenv("RAG_TEST_LATENCY_MS", "15000"))


# ---------- 用例集：inline 是基线，外置 JSON 用来把"曾经答错的"永久锁住 ----------
# keywords 里每一项是"一组同义词，任选其一即可"，避免测成模型的措辞习惯
BASE_CASES = [
    {"id": "rag_concept", "question": "RAG 是什么",
     "keywords": [["检索"], ["生成", "回答"]]},
    # 原来的问法是"FAISS 有什么作用"——文档只把 FAISS 列为向量库之一，并没讲它的作用，
    # 模型其实是拒答的，只因为拒答语里带了"向量"就误判为通过（老版本的假绿灯）。
    # 期望值要对齐文档真实覆盖到的信息，否则回归测的是运气。
    {"id": "vectorstore_options", "question": "LangChain 可以接哪些向量数据库",
     "keywords": [["faiss"], ["chroma"]]},
    {"id": "langgraph_value", "question": "LangGraph 的核心价值是什么",
     "keywords": [["可控", "控制", "流程"], ["状态", "节点"]]},
    {"id": "refuse_quantum", "question": "这篇文档讲了量子计算吗", "should_refuse": True},
    {"id": "refuse_decorator", "question": "文档里有 Python 装饰器教程吗", "should_refuse": True},
]

REFUSE_HINTS = ["没有提到", "未提到", "未提及", "没有相关信息", "没有提及",
                "我不知道", "无法回答", "无法从", "文档中没有"]


def load_cases() -> list[dict]:
    """inline 基线 + 可选外置用例库；同 id 以外置为准（方便临时改期望值）。"""
    cases = {c["id"]: c for c in BASE_CASES}
    if EXTRA_CASES.exists():
        for c in json.loads(EXTRA_CASES.read_text(encoding="utf-8")):
            cases[c["id"]] = c
    return list(cases.values())


CASES = load_cases()
ANSWER_CASES = [c for c in CASES if not c.get("should_refuse")]
REFUSE_CASES = [c for c in CASES if c.get("should_refuse")]


# ---------- 断言工具：归一化后再匹配 ----------
def _norm(text: str) -> str:
    """全角转半角 + 转小写 + 去空白。测"答没答对"，不测"排版习惯"。"""
    return "".join(unicodedata.normalize("NFKC", text).lower().split())


def _refused(answer: str) -> bool:
    n = _norm(answer)
    return any(_norm(h) in n for h in REFUSE_HINTS)


def _missing_keyword(answer: str, keyword_groups) -> str | None:
    """返回第一个没被覆盖的关键词组（组内任选其一即算覆盖），全覆盖则返回 None。"""
    n = _norm(answer)
    for group in keyword_groups:
        group = [group] if isinstance(group, str) else group   # 兼容旧写法 ["检索"]
        if not any(_norm(k) in n for k in group):
            return " / ".join(group)
    return None


# ---------- 前置条件：环境没配好要说清楚，不能伪装成质量问题 ----------
def _missing_prereqs() -> list[str]:
    missing = []
    if not os.getenv("DEEPSEEK_API_KEY"):
        missing.append("DEEPSEEK_API_KEY 未配置（.env）")
    if not DOC_PATH.exists():
        missing.append(f"测试文档不存在：{DOC_PATH.name}")
    if not Path(EMBED_MODEL_PATH).exists():
        missing.append(f"embedding 模型路径不存在：{EMBED_MODEL_PATH}")
    return missing


@pytest.fixture(scope="session")
def rag_chain():
    missing = _missing_prereqs()
    if missing:
        reason = "环境未就绪：" + "；".join(missing)
        # 本地缺 key/模型是常态 → skip；CI 里设 RAG_TEST_STRICT=1 → fail，
        # 否则回归会"全绿地跳过"，比红灯更危险。
        pytest.fail(reason) if STRICT else pytest.skip(reason)
    return build_rag_chain(build_retriever(str(DOC_PATH)))


RESULTS: dict[str, dict] = {}     # case_id -> 结果记录，会话结束后落盘


@pytest.fixture(scope="session")
def ask(rag_chain):
    """按问题缓存答案：LLM 调用又慢又花钱，一个问题只应该跑一次，断言可以有很多条。"""
    cache: dict[str, str] = {}

    def _ask(case: dict) -> str:
        q = case["question"]
        if q not in cache:
            t0 = time.perf_counter()
            cache[q] = rag_chain.invoke(q)
            RESULTS[case["id"]] = {
                "case_id": case["id"], "question": q, "answer": cache[q],
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                "passed": True, "reason": "",
            }
        return cache[q]

    return _ask


def _fail(case_id: str, reason: str):
    RESULTS.setdefault(case_id, {"case_id": case_id}).update(passed=False, reason=reason)


@pytest.fixture(scope="session", autouse=True)
def dump_results():
    """会话结束把每条用例的结果写盘：失败要能复盘，下游 day26 诊断脚本直接读这个文件。"""
    yield
    if RESULTS:
        FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)
        FAILURE_LOG.write_text(
            json.dumps(list(RESULTS.values()), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ---------- 用例 ----------
@pytest.mark.parametrize("case", ANSWER_CASES, ids=[c["id"] for c in ANSWER_CASES])
def test_answer_covers_key_facts(ask, case):
    """宽松断言：只要答案覆盖了关键信息就算过，不要求逐字相等。"""
    answer = ask(case)

    if not answer.strip():
        _fail(case["id"], "空回答")
        pytest.fail("模型返回空回答")

    # 先查拒答：不然"文档中没有提到检索和生成"这种回答会带着关键词蒙混过关
    if _refused(answer):
        _fail(case["id"], "该答却拒答")
        pytest.fail(f"该答却拒答，实际：{answer[:120]}")

    missing = _missing_keyword(answer, case["keywords"])
    if missing:
        _fail(case["id"], f"缺关键词：{missing}")
        pytest.fail(f"答案应包含「{missing}」，实际：{answer[:120]}")


@pytest.mark.parametrize("case", REFUSE_CASES, ids=[c["id"] for c in REFUSE_CASES])
def test_should_refuse(ask, case):
    """防幻觉回归：文档没有的内容必须拒答，不能瞎编。"""
    answer = ask(case)
    if not _refused(answer):
        _fail(case["id"], "应拒答却硬答")
        pytest.fail(f"应拒答，实际乱答：{answer[:120]}")


def test_latency_within_budget():
    """延迟也是会退化的指标（换模型、加 rerank、放大 k 都会拖慢），一并纳入回归。
    复用上面已经跑过的调用，不额外花钱。"""
    latencies = {r["case_id"]: r["latency_ms"] for r in RESULTS.values() if "latency_ms" in r}
    if not latencies:
        pytest.skip("本轮没有实际调用（用例被跳过或单独 -k 运行）")
    slowest_id = max(latencies, key=latencies.get)
    assert latencies[slowest_id] <= LATENCY_BUDGET_MS, (
        f"最慢用例 {slowest_id} 耗时 {latencies[slowest_id]:.0f}ms，"
        f"超过预算 {LATENCY_BUDGET_MS:.0f}ms（可用 RAG_TEST_LATENCY_MS 调整）"
    )


if __name__ == "__main__":
    import sys
    # 直接 python 跑也能触发 pytest，不依赖文件名是否以 test_ 开头
    sys.exit(pytest.main([__file__, "-v"]))


# ----------------------------------------------------------
# 小结：
# - 把评测集 + 断言写成 pytest，就有了"一键回归"——改完 RAG 立刻知道有没有退化
# - LLM 输出不稳定，断言要宽松（包含/拒答 + 归一化 + 同义词任选），并用 temperature=0
# - 能进 CI 的四个细节：路径相对本文件、环境缺失 skip 而非报错（CI 用 STRICT 反转）、
#   同一问题只调一次模型、结果落盘可复盘
# - 别只测正确性：延迟也是会悄悄退化的指标，顺手纳入同一套回归
#
# 动手练习：把 Day22/Day26 失败用例库里的题写进 day48_cases.json（同样的 id/question/
#          keywords/should_refuse 结构），让"曾经答错的"永远被回归覆盖。
# ----------------------------------------------------------
