"""提示词注入第一层防护：用户与检索文档都按不可信输入检查。"""

from langchain_core.documents import Document

PATTERNS = ("ignore previous", "忽略之前", "system prompt", "系统提示词", "泄露密钥")


def suspicious(text):
    """返回命中的第一个可疑短语，没有命中返回 None。这只是关键词第一层，不能替代模型侧防护和权限控制。"""
    return next((x for x in PATTERNS if x in text.casefold()), None)


def filter_documents(documents: list[Document]):
    """把检索到的文档分成 (安全文档, 被拦截文档的 chunk_id 列表)；正文含可疑短语的文档被拦截。"""
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
        """问题含可疑短语时抛 ValueError，此前不做任何检索、工具调用或工单操作。"""
        pattern = suspicious(question)
        if pattern:
            raise ValueError(f"检测到可疑指令：{pattern}")
        return self.application.handle(question, **kwargs)

    def ask(self, question, **kwargs):
        return self.handle(question, **kwargs).answer

    def __getattr__(self, name):
        return getattr(self.application, name)
