# B6e Gate 验证记录 · 2026-10-18

B6e 覆盖 9.8 向量库选型、9.9 部署配置、9.11 vLLM 启动配置。

## 结果

| 章节 | v2 | 验收项 | 参考解 |
|---|---|---|---|
| 9.8 向量库选型 | L9 | 4 | 4/4 |
| 9.9 部署配置 | L9 | 5 | 5/5 |
| 9.11 vLLM 配置 | L9 | 5 | 5/5 |

默认骨架 0 通过。

## 回归

```text
pytest tools chapters/test_new_lessons.py -q：28 passed
check_course_links：277 个 Markdown，断链 0
apply_v2_map --check：111 unchanged
ruff：All checks passed
```

## 覆盖

- **9.8**：大规模+K8s/事务/租户/独立服务优先级、租户过滤。
- **9.9**：数据库/Redis/Qdrant 协议、生产示例密码、多错误收集。
- **9.11**：model/端口/TP/上下文/显存/env 校验、命令元组、密钥占位符。

## 未验证

- 临时参考解；未连接 Qdrant/Milvus/Postgres，未启动 vLLM/GPU。

## 复现

```bash
python chapters/part9-enterprise-infra-optional/9.8-vectorstore-selection/gate/gate_check.py
python chapters/part9-enterprise-infra-optional/9.9-compose-linux-ops/gate/gate_check.py
python chapters/part9-enterprise-infra-optional/9.11-vllm-gpu/gate/gate_check.py
```
