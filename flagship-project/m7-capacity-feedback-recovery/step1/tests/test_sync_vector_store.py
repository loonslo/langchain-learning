from langchain_core.documents import Document

from customer_support.sync import SyncPlan, apply_plan


class Store:
    def __init__(self):
        self.upserted = []
        self.deleted = []

    def upsert(self, documents):
        self.upserted.extend(documents)

    def delete_source(self, source_id):
        self.deleted.append(source_id)

    def search(self, tenant_id, query, k):
        return []


def test_sync_plan_reaches_the_vector_store_contract():
    store = Store()
    document = Document(page_content="new", metadata={"source_id": "new.md"})
    apply_plan(
        store,
        SyncPlan(("new.md",), ("old.md",)),
        {"new.md": [document]},
    )

    assert store.deleted == ["old.md"]
    assert store.upserted == [document]
