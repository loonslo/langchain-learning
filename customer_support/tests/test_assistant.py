"""CustomerSupportAssistant 的离线业务验收测试。"""

from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from customer_support.assistant import REFUSAL, CustomerSupportAssistant


class FakeRetriever:
    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.questions: list[str] = []

    def invoke(self, question: str) -> list[Document]:
        self.questions.append(question)
        return self.documents


class FakeModel:
    def __init__(self, answer: str):
        self.answer = answer
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        return SimpleNamespace(content=self.answer)


def test_known_question_returns_answer_and_real_source():
    document = Document(
        page_content="退款通常在 3–5 个工作日原路退回。",
        metadata={"source": "customer_faq.md"},
    )
    retriever = FakeRetriever([document])
    model = FakeModel("退款通常需要 3–5 个工作日。")

    result = CustomerSupportAssistant(retriever, model).ask(" 退款多久到账？ ")

    assert result.text == "退款通常需要 3–5 个工作日。"
    assert result.sources == ("customer_faq.md",)
    assert retriever.questions == ["退款多久到账？"]
    assert model.calls == 1


def test_no_evidence_refuses_without_calling_model():
    model = FakeModel("模型凭记忆生成的答案")

    result = CustomerSupportAssistant(FakeRetriever([]), model).ask("会员权益是什么？")

    assert result.text == REFUSAL
    assert result.sources == ()
    assert model.calls == 0


def test_sources_only_use_existing_document_metadata_and_deduplicate():
    documents = [
        Document(page_content="证据一", metadata={"source": "folder/customer_faq.md"}),
        Document(page_content="证据二", metadata={"source": "customer_faq.md"}),
        Document(page_content="证据三", metadata={}),
    ]

    result = CustomerSupportAssistant(
        FakeRetriever(documents), FakeModel("回答【来源：模型伪造.md】")
    ).ask("问题")

    assert result.sources == ("customer_faq.md",)
    assert "模型伪造.md" not in result.sources


def test_blank_question_is_rejected_before_retrieval():
    retriever = FakeRetriever([])

    with pytest.raises(ValueError, match="问题不能为空"):
        CustomerSupportAssistant(retriever, FakeModel("不会调用")).ask(" \n\t ")

    assert retriever.questions == []
