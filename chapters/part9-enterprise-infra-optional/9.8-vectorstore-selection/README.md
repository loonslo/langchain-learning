# 9.8 向量存储选型：把需求写成判断依据

[全书目录](../../README.md) · [上一章 9.7](../9.7-redis-cache-ratelimit/README.md) · [下一章 9.9](../9.9-compose-linux-ops/README.md)

- **目标**：把向量库选型写成可审查的规则（已有 PostgreSQL、事务和 Join、多租户过滤、规模、K8s 运维能力），并让 Qdrant 查询始终带服务端确定的租户过滤。
- **前置**：9.7（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.8-vectorstore-selection`，进入 `.build/enterprise/9.8-vectorstore-selection/enterprise-support` 后运行 `python -m pytest -q`

## 问题

换向量库不一定改善答案。先看已有数据库、过滤需求、数据规模和运维能力，再决定采用哪种存储，并保持服务端租户过滤。

## 概念

VectorRequirements 描述约束；VectorBackend 表示选择；适配器提供统一边界。`choose_vector_backend` 按固定优先级判断：规模很大且有 Kubernetes → Milvus；需要事务或 Join 且不要求独立向量服务 → pgvector；需要租户过滤或独立向量服务 → Qdrant；都不满足 → pgvector。它给出起点建议，不是性能结论。检索后端选型与嵌入、切分和生成质量是不同层。

## 流程

1. 整理存储与运维约束。
2. choose_vector_backend 给出规则建议。
3. 使用适配器查询。
4. 在请求中加入可信租户过滤。

## 本章交付

- `vector_store.py`：选型函数、向量存储协议和 Qdrant 租户过滤适配器。
- `docs/vector_selection.md`：三者边界和 PoC 指标。
- `tests/test_vector_store.py`：验证选择依据与 Qdrant filter 不能缺失。

## 代码导读

vector_store.py 先读需求与选择函数，再读 VectorStore 和 QdrantVectorStore；详细取舍见本章选型文档。

实现文件：

- [vector_store.py](src/enterprise_support/vector_store.py)

## 练习

为已有 PostgreSQL 的小团队与已有检索平台的团队分别写需求，比较结论；检查所有查询是否含预期过滤。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.8-vectorstore-selection
cd .build/enterprise/9.8-vectorstore-selection/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

规则建议不是性能基准，真实过滤、索引、延迟与成本需各后端实测。

Milvus 没有被重复实现。若目标环境指定 Milvus，保持 `VectorStore` 契约不变，补 Milvus 适配器，并用同一数据集比较召回、p95、写入、过滤与运维成本。
