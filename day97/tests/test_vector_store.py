from src.enterprise_support.vector_store import (
    QdrantVectorStore,
    VectorBackend,
    VectorRequirements,
    choose_vector_backend,
)


def test_vector_selection_is_explainable_not_brand_driven():
    assert choose_vector_backend(VectorRequirements(True, False, False, False, False)) is VectorBackend.PGVECTOR
    assert choose_vector_backend(VectorRequirements(False, True, True, False, False)) is VectorBackend.QDRANT
    assert choose_vector_backend(VectorRequirements(False, True, True, True, True)) is VectorBackend.MILVUS


def test_qdrant_search_always_carries_server_side_tenant_filter():
    class Client:
        def query_points(self, **kwargs):
            self.kwargs = kwargs
            return []
    client = Client()
    assert QdrantVectorStore(client).search(tenant_id="shop-a", vector=[0.1], limit=3) == []
    assert client.kwargs["query_filter"]["must"][0]["match"]["value"] == "shop-a"
