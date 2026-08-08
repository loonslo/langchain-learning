"""CustomerSupportAssistant 的离线业务验收测试。

这里不用真实 Chroma 和 LLM：我们要测试的是 assistant 的分支与数据来源，而不是
网络、模型质量或向量算法。Fake 会记录调用参数，因此还能证明某一步“没有发生”。
"""

from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from customer_support.assistant import REFUSAL, CustomerSupportAssistant


class FakeRetriever:
    """返回预先准备的 Document，并记录 assistant 实际检索了什么问题。"""

    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.questions: list[str] = []

    def invoke(self, question: str) -> list[Document]:
        self.questions.append(question)
        return self.documents


class FakeModel:
    """返回固定答案，并统计模型被调用了几次。"""

    def __init__(self, answer: str):
        self.answer = answer
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        return SimpleNamespace(content=self.answer)


def test_known_question_returns_answer_and_real_source():
    # Arrange：准备一段“已被检索到”的真实证据和模型固定回答。
    document = Document(
        page_content="退款通常在 3–5 个工作日原路退回。",
        metadata={"source": "customer_faq.md"},
    )
    retriever = FakeRetriever([document])
    model = FakeModel("退款通常需要 3–5 个工作日。")

    # Act：输入故意带多余空格，以同时验证问题规范化。
    result = CustomerSupportAssistant(retriever, model).ask(" 退款多久到账？ ")

    # Assert：答案来自模型，source 来自 Document，检索问题已经清理空格。
    assert result.text == "退款通常需要 3–5 个工作日。"
    assert result.sources == ("customer_faq.md",)
    assert retriever.questions == ["退款多久到账？"]


def test_no_evidence_refuses_without_calling_model():
    # 即使 FakeModel 准备了一个“看似合理”的答案，无证据时也绝不能调用它。
    model = FakeModel("模型凭记忆生成的答案")
    result = CustomerSupportAssistant(FakeRetriever([]), model).ask("会员权益是什么？")
    assert result.text == REFUSAL
    assert result.sources == ()
    assert model.calls == 0


def test_source_comes_from_document_not_model_text():
    # 模型回答故意伪造一个来源，最终结构化 sources 仍必须使用 metadata。
    document = Document(page_content="客服时间为 9 点。", metadata={"source": "customer_faq.md"})
    model = FakeModel("客服 9 点上班。【来源：模型伪造.md】")
    result = CustomerSupportAssistant(FakeRetriever([document]), model).ask("几点上班？")
    assert result.sources == ("customer_faq.md",)
    assert "模型伪造.md" not in result.sources


def test_blank_question_is_rejected_before_retrieval():
    # 空输入不仅要报错，还要证明 Retriever 根本没有被调用。
    retriever = FakeRetriever([])
    with pytest.raises(ValueError, match="问题不能为空"):
        CustomerSupportAssistant(retriever, FakeModel("不会调用")).ask("  ")
    assert retriever.questions == []
