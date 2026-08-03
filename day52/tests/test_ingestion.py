from customer_support.ingestion import ingest_directory
from customer_support.settings import PROJECT_ROOT


def test_multi_document_chunks_have_stable_traceable_ids():
    directory = PROJECT_ROOT / "data" / "knowledge"
    first, second = ingest_directory(directory), ingest_directory(directory)
    assert {d.metadata["source_id"] for d in first} >= {"refund", "shipping"}
    assert [d.metadata["chunk_id"] for d in first] == [
        d.metadata["chunk_id"] for d in second
    ]
