"""
Day 48 · 把评测变成自动化回归测试（pytest）
==========================================================
测试工程师转 AI 应用开发  ★护城河：你最熟的主场★

Day17-20 的评测是手动跑、肉眼看。这节把它变成 pytest 用例：每次改完 RAG
（调了 chunk、换了 prompt、改了检索），一条命令跑回归，答错的立刻红灯。
普通开发很少给 LLM 应用写自动化测试——这正是测试背景的差异化优势。

知识点：
1. pytest fixture：整个测试只建一次库（scope="module"）
2. 参数化 @pytest.mark.parametrize：把评测集变成一批独立用例
3. RAG 测试为什么不能用精确断言：模型输出有随机性，
   要用"包含关键词 / 是否拒答"这类宽松断言，并把 temperature 调到 0 提升可复现

依赖：pip install pytest
运行：pytest day42_pytest_regression.py -v
   或：python day42_pytest_regression.py   （文件底部自带入口，免配置）
==========================================================
"""

import pytest
from day11_rag_pdf_sources import build_retriever, build_rag_chain


# fixture：被多个测试共享的"前置准备"。scope="module" 表示整个文件只建一次库。
@pytest.fixture(scope="module")
def rag_chain():
    retriever = build_retriever("test_doc.txt")
    return build_rag_chain(retriever)


REFUSE_HINTS = ["没有提到", "我不知道", "未提及", "无法回答"]

# 应正常回答、且答案要包含这些关键词的用例
ANSWER_CASES = [
    ("RAG 是什么", ["检索", "生成"]),
    ("FAISS 有什么作用", ["向量"]),
]
# 文档里没有、应该拒答的用例
REFUSE_CASES = [
    "这篇文档讲了量子计算吗",
    "文档里有 Python 装饰器教程吗",
]


@pytest.mark.parametrize("question,keywords", ANSWER_CASES)
def test_answer_contains_keywords(rag_chain, question, keywords):
    """宽松断言：只要答案覆盖了关键信息就算过，不要求逐字相等。"""
    answer = rag_chain.invoke(question)
    for k in keywords:
        assert k in answer, f"答案应包含「{k}」，实际：{answer}"


@pytest.mark.parametrize("question", REFUSE_CASES)
def test_should_refuse(rag_chain, question):
    """防幻觉回归：文档没有的内容必须拒答，不能瞎编。"""
    answer = rag_chain.invoke(question)
    assert any(h in answer for h in REFUSE_HINTS), f"应拒答，实际乱答：{answer}"


if __name__ == "__main__":
    import sys
    # 直接 python 跑也能触发 pytest，不依赖文件名是否以 test_ 开头
    sys.exit(pytest.main([__file__, "-v"]))


# ----------------------------------------------------------
# 小结：
# - 把评测集 + 断言写成 pytest，就有了"一键回归"——改完 RAG 立刻知道有没有退化
# - LLM 输出不稳定，断言要宽松（包含/拒答），并用 temperature=0 提升可复现
# - 这套自动化回归能直接接进 CI（每次提交自动跑），是工程成熟度的体现
#
# 动手练习：把 Day22 失败用例库 failures.json 里的题加进 REFUSE/ANSWER_CASES，
#          让"曾经答错的"永远被回归覆盖
# ----------------------------------------------------------
