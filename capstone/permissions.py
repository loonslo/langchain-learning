"""
capstone/permissions.py · 文档级权限过滤（Day55）
==========================================================
企业 RAG 最痛、面试最常问的一题：A 部门的人不能从知识库里问出 B 部门的机密。

核心原则——**权限必须在检索层做，不能只靠 prompt 约束**：
- 靠 prompt（"不要回答无权限内容"）= 把机密塞进上下文再求模型别说，
  一次注入 / 一次模型抽风就泄露，等于没做。
- 正确做法：检索时就只捞当前用户有权看的 chunk，无权的根本进不了上下文。

做法：每个 chunk 带权限 metadata（owner / dept / 可见角色）；
检索时按"当前用户身份"过滤。为兼容向量库 + BM25 两路召回，
这里用"过量召回 → Python 谓词过滤 → 取 top_k"，最稳、最好讲清。
==========================================================
"""

from dataclasses import dataclass, field
from langchain_core.documents import Document


@dataclass
class User:
    """当前请求的用户身份。真实系统里从 JWT / session 解析（见 auth.py）。"""
    user_id: str
    dept: str = ""
    roles: set[str] = field(default_factory=set)   # 如 {"employee", "finance"}


def attach_acl(doc: Document, dept: str = "public", allow_roles=("public",)) -> Document:
    """给文档/chunk 打权限标签。建库或同步时调用。
    约定：dept=public + role=public 表示全员可见。"""
    doc.metadata["dept"] = dept
    doc.metadata["allow_roles"] = ",".join(allow_roles)   # 存字符串，跨向量库都兼容
    return doc


def can_see(meta: dict, user: User) -> bool:
    """权限判定：公开内容人人可见；否则需角色或部门命中其一。"""
    allow = set((meta.get("allow_roles") or "public").split(","))
    if "public" in allow:
        return True
    if user.roles & allow:           # 角色命中
        return True
    if meta.get("dept") and meta["dept"] == user.dept:   # 同部门
        return True
    return False


class PermissionRetriever:
    """包住 KB 的检索器：过量召回后按用户权限过滤，再截断到 top_k。"""

    def __init__(self, kb, user: User, top_k: int = 4, overfetch: int = 4):
        self.base = kb.retriever
        self.user = user
        self.top_k = top_k
        self.overfetch = overfetch

    def invoke(self, query: str):
        # 过量召回：怕过滤后不够，先多捞一些
        if hasattr(self.base, "search_kwargs"):
            self.base.search_kwargs = {"k": self.top_k * self.overfetch}
        hits = self.base.invoke(query)
        allowed = [d for d in hits if can_see(d.metadata, self.user)]
        return allowed[: self.top_k]


def permission_chain(kb, user: User):
    """带权限过滤的问答链：无权的内容根本进不了上下文。"""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    import config as C

    retriever = PermissionRetriever(kb, user, top_k=C.TOP_K)
    prompt = ChatPromptTemplate.from_template(
        "依据上下文回答，无相关信息就说'文档中没有提到'。\n"
        "上下文：\n{context}\n\n问题：{question}")
    return ({"context": (lambda q: kb._format(retriever.invoke(q))),
             "question": RunnablePassthrough()}
            | prompt | C.get_llm() | StrOutputParser())


if __name__ == "__main__":
    # 纯逻辑演示（不连模型）：同一份元数据，不同用户看到的不一样
    finance_doc = {"dept": "finance", "allow_roles": "finance"}
    public_doc = {"dept": "public", "allow_roles": "public"}

    alice = User("alice", dept="finance", roles={"employee", "finance"})
    bob = User("bob", dept="marketing", roles={"employee"})

    print("财务文档 → alice 可见：", can_see(finance_doc, alice))   # True
    print("财务文档 → bob   可见：", can_see(finance_doc, bob))     # False
    print("公开文档 → bob   可见：", can_see(public_doc, bob))      # True
    print("\n要点：同一问题，alice 和 bob 召回到的来源不同——权限在检索层生效，不靠 prompt。")
