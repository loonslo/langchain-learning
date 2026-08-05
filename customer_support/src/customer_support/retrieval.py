"""用 RRF 融合语义排名与关键词排名，不直接相加不同量纲的原始分数。"""

from langchain_core.documents import Document


def reciprocal_rank_fusion( rankings: list[list[Document]], limit: int = 3
                            ) -> list[Document]:
    scores: dict[str, float] = {}
    documents: dict[str, Document] = {}
    for ranking in rankings:
        for rank,document in enumerate(ranking,1):
            key = str(document.metadata['chunk_id'])
            documents[key] = document
            scores[key] = scores.get(key,0.0)+1/(60+rank)
    keys = sorted(scores,key=lambda key:(-scores[key],key))[:limit]
    return [documents[key] for key in keys]