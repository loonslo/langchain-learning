"""连接真实知识目录的轻量集成测试。"""

from customer_support.knowledge import load_chunks
from customer_support.settings import Settings


def test_real_faq_can_be_loaded_and_split():
    faq_path = Settings.from_env().knowledge_path / "customer_faq.md"
    chunks = load_chunks(faq_path)

    assert chunks
    assert all(chunk.metadata["source"] == "customer_faq.md" for chunk in chunks)
    assert any("退款" in chunk.page_content for chunk in chunks)
