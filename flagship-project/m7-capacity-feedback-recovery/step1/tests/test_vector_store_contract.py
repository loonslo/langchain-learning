from langchain_core.documents import Document


class MemoryStore:
    def __init__(self):
        self.docs = []

    def upsert(self, documents):
        self.docs = documents

    def delete_source(self, source_id):
        self.docs = [d for d in self.docs if d.metadata["source_id"] != source_id]

    def search(self, tenant_id, query, k):
        return [d for d in self.docs if d.metadata["tenant_id"] == tenant_id][:k]


def test_contract_requires_tenant_scoped_search_and_delete():
    store = MemoryStore()
    store.upsert(
        [Document(page_content="x", metadata={"tenant_id": "a", "source_id": "s"})]
    )
    assert len(store.search("a", "x", 3)) == 1 and store.search("b", "x", 3) == []
    store.delete_source("s")
    assert store.docs == []
