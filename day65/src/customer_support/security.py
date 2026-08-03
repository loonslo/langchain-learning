"""提示词注入第一层防护：用户与检索文档都按不可信输入检查。"""

from langchain_core.documents import Document

PATTERNS = ("ignore previous", "忽略之前", "system prompt", "系统提示词", "泄露密钥")


def suspicious(text):
    return next((x for x in PATTERNS if x in text.casefold()), None)


def filter_documents(documents: list[Document]):
    safe = []
    blocked = []
    for doc in documents:
        (blocked if suspicious(doc.page_content) else safe).append(
            doc.metadata.get("chunk_id", "unknown")
            if suspicious(doc.page_content)
            else doc
        )
    return safe, blocked
