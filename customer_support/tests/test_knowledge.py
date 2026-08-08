"""连接 Day51 真实 FAQ 文件的轻量集成测试。"""
from src.customer_support.ingestion import load_chunks
from src.customer_support.settings import Settings


def test_real_faq_can_be_loaded_and_split():
    # 这里不使用 Fake：它保护真实路径、UTF-8 加载、切块和来源 metadata。
    chunks = load_chunks(Settings.from_env().knowledge_path)
    assert chunks
    assert all(chunk.metadata["source"] == "customer_faq.md" for chunk in chunks)
    assert any("退款" in chunk.page_content for chunk in chunks)
