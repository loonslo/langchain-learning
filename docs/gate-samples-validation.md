# 5 个样板章 Gate 改造验证 · 2026-10-18

把 `docs/curriculum-v2.md` 里的 5 个样板章改成“闭卷 + 故障注入 + 验收”的 gate 版本。只改这 5 章的教学层与验收脚本，没有改参考实现、capstone 或旗舰项目。

## 范围

| 新编号 | 原章节 | 新增/改写 |
|---|---|---|
| L1.6 手写 Harness | 2.5 裸 SDK 与循环 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| L2.9 RAG 评测基线 | 2.4 RAG 评测种子 | `gate/starter.py`、`gate/gate_check.py`、`gate/cases.json`、README、workbook |
| L3.4 LLM Judge 与校准 | 3.3 LLM 评委 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| L4.4 ReAct 与工具设计 | 4.5 ReAct 工具循环 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| L5.1 FastAPI 服务与可靠性 | 5.1 FastAPI 服务 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |

每章的统一结构：

- `gate/starter.py`：闭卷骨架，只有接口与要求，函数体是 `NotImplementedError`。
- `gate/gate_check.py`：离线验收，不调用真实模型；用脚本化模型/工具/存储注入故障。
- `README.md`：闭卷规则、任务、故障注入表、验收标准、提交物、通过后对照。
- `workbook.md`：闭卷记录、预测、gate 结果、解释题、未验证边界。

## 实际执行

### 1. Gate 脚本自检

用临时参考解运行（验证后已清理，不随仓库交付）：

| Gate | 命令 | 结果 |
|---|---|---|
| L1.6 | `python chapters/part2-rag/2.5-raw-sdk-rag-agent-loop/gate/gate_check.py --module .tmp/gate_solutions/l16.py` | 16/16 passed |
| L2.9 | `python chapters/part2-rag/2.4-eval-seed/gate/gate_check.py --module .tmp/gate_solutions/l29.py` | 14/14 passed |
| L3.4 | `python chapters/part3-evals/3.3-llm-judge/gate/gate_check.py --module .tmp/gate_solutions/l34.py` | 14/14 passed |
| L4.4 | `python chapters/part4-agents-langgraph/4.5-react-agent/gate/gate_check.py --module .tmp/gate_solutions/l44.py` | 14/14 passed |
| L5.1 | `python chapters/part5-production/5.1-serve-fastapi/gate/gate_check.py --module .tmp/gate_solutions/l51.py` | 17/17 passed |

### 2. 骨架必须失败

用默认 `gate/starter.py` 运行，5 个 gate 都是 0 通过（`NotImplementedError`），退出码 1。这是预期行为：骨架不是答案。

### 3. 现有回归

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed
```

### 4. 静态检查

```text
python -m ruff check chapters/part2-rag/2.5-raw-sdk-rag-agent-loop/gate ...
All checks passed!
```

## 未验证

- **没有真实学习者从零实现**：通过的是临时参考解，不是学习记录。gate 通过只证明脚本的验收逻辑成立，不代表本人已掌握。
- **没有调用真实模型**：5 个 gate 都是离线替身；L3.4/L5.1 的真实模型路径未运行。
- **没有真实部署**：5.1 只验证 FastAPI 服务边界，没有 Docker、公网、压测、恢复。
- **没有验证 gate 与真实 RAG/Agent 的对接**：2.9 用固定结果、4.4 用脚本化模型；真实质量仍要看 2.3/4.5 的参考实现与后续评测。

## 复现方式

从仓库根目录：

```bash
# 默认检查骨架，应 0 通过
python chapters/part2-rag/2.5-raw-sdk-rag-agent-loop/gate/gate_check.py

# 通过后检查自己的实现（把路径换成你的文件）
python chapters/part2-rag/2.5-raw-sdk-rag-agent-loop/gate/gate_check.py --module 你的实现.py
```

`gate/gate_report.json` 是本地运行产物，已加入 `.gitignore`；要保留证据时，把结论抄进对应 `workbook.md`，或手动强制入库。

## 边界

- 这次改造只覆盖 5 个样板章，其余 77 章仍是原来的阅读/运行型；不要从这次提交推断全部课程已 gate 化。
- 5 个 gate 的检查项是“结构性/边界性”验收，不是业务质量验收；真实质量要靠评测集、真实模型和上线证据。
- 参考实现仍是教材，不在闭卷阶段阅读；通过 gate 后再对照。
