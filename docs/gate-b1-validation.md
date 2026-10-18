# B1 Gate 验证记录 · 2026-10-18

B1 覆盖 L1 模型接口的 6 章：1.1、1.2、1.3、1.4、1.5、1.8。每章新增闭卷骨架、离线验收、README 任务书和 gate workbook；参考实现未修改。

## 范围

| 章节 | v2 路径 | 验收项 | 新增 |
|---|---|---|---|
| 1.1 首次调用 | L1.1 核心 | 11 | `gate/starter.py`、`gate/gate_check.py`、README、workbook |
| 1.2 输出控制 | L1.2 核心 | 10 | 同上 |
| 1.3 结构化输出 | L1.3 核心 | 10 | 同上 |
| 1.4 上下文与记忆 | L1.4 核心 | 12 | 同上 |
| 1.5 工具调用 | L1.5 核心 | 11 | 同上 |
| 1.8 CLI 助手 | L1.7 核心 | 11 | 同上 |

## 实际执行

### 1. 参考解

用临时参考解（验证后已清理）运行：

| Gate | 结果 |
|---|---|
| 1.1 | 11/11 passed |
| 1.2 | 10/10 passed |
| 1.3 | 10/10 passed |
| 1.4 | 12/12 passed |
| 1.5 | 11/11 passed |
| 1.8 | 11/11 passed |

### 2. 默认骨架

6 个 gate 用默认 `gate/starter.py` 运行都是 0 通过（`NotImplementedError`），退出码 1。这是预期行为：骨架不是答案。

### 3. 现有回归与结构检查

```text
python -m pytest tools chapters/test_new_lessons.py -q
28 passed

python tools/check_course_links.py
检查 261 个 Markdown 文件；断链 0 个。

python tools/apply_v2_map.py --check
合计：111 个 README；inserted=0 updated=0 unchanged=111

python -m ruff check <6 个 gate 目录>
All checks passed!
```

## 覆盖的故障

| 章节 | 主要故障 |
|---|---|
| 1.1 | 空问题、超时、模型异常、空响应、非 dict 响应、usage 缺失 |
| 1.2 | 非法 temperature/max_tokens/stop、空流、坏片段、迭代中断、流式超时 |
| 1.3 | 缺字段、类型错、非对象 JSON、repair 一次/失败/无 repair、score 越界 |
| 1.4 | 会话串台、返回引用污染、非法 role、system 被裁、负预算、非法消息 |
| 1.5 | 未知工具、参数错误、工具异常、非字符串结果、超步数、结果未回灌 |
| 1.8 | clear/quit、空输入、工具结果回灌、未知工具、模型异常、超轮数 |

## 未验证

- **没有真实学习者从零实现**：通过的是临时参考解，不是学习记录。
- **没有调用真实模型**：6 个 gate 都是离线替身；参考实现的真实模型路径未运行。
- **没有验证真实质量**：gate 只验证结构/边界，不验证回答正确性。
- **没有改参考实现**：`first_call.py`、`control_output.py`、`structured_output.py`、`context_memory.py`、`tool_calling.py`、`chatbot_project.py` 均未修改。

## 复现

```bash
# 默认检查骨架，应 0 通过
python chapters/part1-foundations/1.1-first-call/gate/gate_check.py

# 通过后检查自己的实现
python chapters/part1-foundations/1.1-first-call/gate/gate_check.py --module 你的实现.py
```

`gate/gate_report.json` 是本地运行产物，已加入 `.gitignore`。

## 边界

- B1 只覆盖 L1 的 6 章；L1 的 1.6（MCP 入门）仍是选做阅读，1.7 是原理附录。
- 这些 gate 是“结构/边界”验收，不是业务质量验收；真实质量要看评测集与真实模型。
- 下一批 B2 是 L2 的 9 章，未开始。
