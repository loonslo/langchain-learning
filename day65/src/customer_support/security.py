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


class SecuredApplication:
    """在任何检索、工具或工单副作用发生前检查用户输入。"""

    def __init__(self, application):
        self.application = application

    def handle(self, question, **kwargs):
        pattern = suspicious(question)
        if pattern:
            raise ValueError(f"检测到可疑指令：{pattern}")
        return self.application.handle(question, **kwargs)

    def ask(self, question, **kwargs):
        return self.handle(question, **kwargs).answer

    def __getattr__(self, name):
        return getattr(self.application, name)
