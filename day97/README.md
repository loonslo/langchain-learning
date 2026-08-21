# Day97 · pgvector、Qdrant、Milvus 的选型与 Qdrant 适配器

不要背“某向量库一定最好”。选型取决于已有 PostgreSQL、事务和 Join 需求、过滤/多租户、
向量规模、K8s 运维能力与团队已有平台。今天把选型写成可审查规则，并让 Qdrant 查询始终
携带服务端确定的租户过滤。

## 今日交付

- `vector_store.py`：选型函数、向量存储协议和 Qdrant 租户过滤适配器。
- `docs/vector_selection.md`：三者边界和 PoC 指标。
- `tests/test_vector_store.py`：验证选择依据与 Qdrant filter 不能缺失。

## 今日边界

Milvus 没有被重复实现。若 JD 点名 Milvus，保持 `VectorStore` 契约不变，补 Milvus
适配器，并用同一数据集比较召回、p95、写入、过滤与运维成本。
