# 向量库 PoC 选型卡

| 条件 | 首选起点 | 需要验证 |
|---|---|---|
| 业务已有 PostgreSQL，向量与订单/权限需要事务 Join | pgvector | HNSW 参数、过滤后 p95、主库资源隔离 |
| RAG 是独立服务，需要 payload 过滤和较轻的自托管运维 | Qdrant | tenant filter、写入吞吐、备份恢复、分片方案 |
| 已有 K8s/SRE 平台，规模/吞吐很高且要专门的分布式向量集群 | Milvus | collection/partition 多租户、资源调度、故障演练 |

不以“千万向量”一个数字决定选型。PoC 至少固定数据、嵌入模型、top-k、过滤条件、并发、
Recall@k、p95/p99、写入延迟、内存/磁盘和恢复时间，并记录版本与配置。
