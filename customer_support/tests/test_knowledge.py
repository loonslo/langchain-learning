"""连接真实 FAQ 文件的轻量集成测试。

集成测试会让多个真实模块一起工作，用来保护路径、文件编码和元数据等连接点。
"""
from src.ingestion import load_chunks
from src.settings import Settings


def test_real_faq_can_be_loaded_and_split():
    # 这里不使用 Fake：它保护真实路径、UTF-8 加载、切块和来源 metadata。
    chunks = load_chunks(Settings.from_env().knowledge_path / "customer_faq.md")
    assert chunks
    assert all(chunk.metadata["source"] == "customer_faq.md" for chunk in chunks)
    assert any("退款" in chunk.page_content for chunk in chunks)
