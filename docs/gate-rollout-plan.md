# 全量 Gate 化 rollout 计划

> 阶段 1（全量结构修复）已完成，见 [course-v2-structure-validation.md](course-v2-structure-validation.md)。
> 本文件是阶段 2 的分批计划：只把**有可执行接口、能注入故障**的章节改成 gate；纯概念章用“清单 + 产物”验收，不硬造 gate。

## 1. 已完成

| 批次 | 章节 | 结果 |
|---|---|---|
| 样板 | L1.6 / L2.9 / L3.4 / L4.4 / L5.1（2.5 / 2.4 / 3.3 / 4.5 / 5.1） | 16/16、14/14、14/14、14/14、17/17；见 [gate-samples-validation.md](gate-samples-validation.md) |
| B1 | L1.1–L1.5、L1.7（1.1–1.5、1.8） | 11/11、10/10、10/10、12/12、11/11、11/11；见 [gate-b1-validation.md](gate-b1-validation.md) |
| B2a | L2.1–L2.3（2.1–2.3） | 6/6、9/9、10/10；见 [gate-b2a-validation.md](gate-b2a-validation.md) |
| B2b | L2.3–L2.8（2.6–2.11） | 9/9、7/7、7/7、9/9、9/9、8/8；见 [gate-b2b-validation.md](gate-b2b-validation.md) |
| B3a | L3.1–L3.5（3.1、3.2、3.4、3.5） | 8/8、6/6、7/7、8/8；见 [gate-b3a-validation.md](gate-b3a-validation.md) |
| B3b | L3.6（3.6 清单、3.7、3.10） | 3.7 8/8、3.10 5/5；3.6 清单；见 [gate-b3b-validation.md](gate-b3b-validation.md) |
| B4a | L4.1–L4.3（4.1–4.4） | 8/8、4/4、4/4、5/5；见 [gate-b4a-validation.md](gate-b4a-validation.md) |
| B4b | L4.3/L4.5（4.6、4.7） | 7/7、4/4；见 [gate-b4b-validation.md](gate-b4b-validation.md) |
| B4c | L4.5–L5.6（4.8–4.10） | 6/6、4/4、6/6；见 [gate-b4c-validation.md](gate-b4c-validation.md) |
| B4d ✅ | 3.9、4.11、4.12、4.14 | 7/7、4/4、5/5、5/5；见 [gate-b4d-validation.md](gate-b4d-validation.md) |
| B5a | L5.1（5.2） | 5/5；见 [gate-b5a-validation.md](gate-b5a-validation.md) |
| B5b ✅ | 5.3、5.4、5.5、5.7、5.8 | 4/4、4/4、5/5、7/7、5/5；见 [gate-b5b-validation.md](gate-b5b-validation.md) |

## 2. 分批顺序

按 v2 路径从浅到深，每批只改一个层级，便于复用 gate 结构、控制回归成本。

| 批次 | v2 阶段 | 章节 | 数量 | Gate 类型 |
|---|---|---|---|---|
| B1 ✅ | L1 模型接口 | 1.1、1.2、1.3、1.4、1.5、1.8 | 6 | 假 LLM + 请求/响应契约 + 失败注入 |
| B2a ✅ | L2 检索主链 | 2.1、2.2、2.3 | 3 | 固定文档/片段 + 离线检索替身 |
| B2b ✅ | L2 检索进阶 | 2.6、2.7、2.8、2.9、2.10、2.11 | 6 | 固定文档/片段 + 指标 + 离线检索替身 |
| B3a ✅ | L3 评测基础 | 3.1、3.2、3.4、3.5 | 4 | 固定样本 + 指标/数据契约 |
| B3b ✅ | L3 评测进阶 | 3.6（清单）、3.7、3.10 | 3 | 固定样本 + 回归报告；3.6 走清单 |
| B4a ✅ | L4 控制流基础 | 4.1、4.2、4.3、4.4 | 4 | 脚本化 planner + 状态图 |
| B4b ✅ | L4 可靠/路由 | 4.6、4.7 | 2 | 假函数 + 固定 JSON |
| B4c ✅ | L4 规划/观测 | 4.8、4.9、4.10 | 3 | 脚本化 planner + 内存 trace/store |
| B4d ✅ | L4 交互/协作 | 3.9、4.11、4.12、4.14 | 4 | 轨迹断言 + HITL/权限 |
| B5b | L5 生产 | 5.3、5.4、5.5、5.7、5.8 | 5 | TestClient + 假 store + 故障注入 |
| B6a ✅ | 选型/校准/门禁 | 6.1、8.5、8.9 | 3 | 规则/指标/判定纯函数 |
| B6b | 证据/专项 | 8.6、9.x、项目步骤、选修 | 待定 | 清单/契约 + 可复现报告 |

**不做 gate 的章节**：纯概念/选型/导读章（如 0.1、0.2、3.1 的部分、4.1、4.15、6.1、9.8 等）只在 README 里保留“读完后能回答什么 + 产出什么”，避免 82 章全是模板。

## 3. 每批的 Definition of Done

每章必须有：

1. `gate/starter.py`：闭卷骨架，只有接口与要求。
2. `gate/gate_check.py`：离线验收，不调用真实模型；用替身注入故障。
3. `README.md`：闭卷规则、任务、故障注入表、验收标准、提交物、通过后对照。
4. `workbook.md`：闭卷记录、预测、gate 结果、解释题、未验证边界。
5. 参考实现保持原样，通过 gate 后才对照。

每批必须验证：

- 参考解跑通全部检查；骨架默认 0 通过。
- `python -m pytest tools chapters/test_new_lessons.py -q` 通过。
- `python tools/check_course_links.py` 断链 0。
- `ruff check` 通过。
- 新增/修改的 README 不破坏 `v2 路径` 标签与索引。
- 写一份批次验证记录，更新 `TASKS.md` 与 `PROJECT_STATUS.md`。

## 4. B1 详细契约（已落地）

| 章节 | 闭卷接口 | 主要故障注入 |
|---|---|---|
| 1.1 首次调用 | `build_messages` / `parse_response` / `call_once` | 空问题、超时、空响应、非 dict、usage 缺失 |
| 1.2 输出控制 | `build_request` / `collect_stream` / `stream_text` | 参数越界、空流、坏片段、迭代中断、流超时 |
| 1.3 结构化输出 | `parse_model_json` / `validate_code_review` | 非法 JSON、缺字段、类型错、repair 一次/失败 |
| 1.4 上下文与多轮 | `SessionMemory` / `trim_history(messages, max_chars)` | 串台、引用污染、system 被裁、负预算 |
| 1.5 工具调用 | `build_tools` / `dispatch_tool` / `run_tool_loop` | 未知工具、参数错、工具异常、超步数 |
| 1.8 CLI 助手 | `run_cli(inputs, chat_fn, tools, max_turns)` | clear/quit、空输入、工具回灌、超轮数 |

B1 的 gate 全部用假 `chat_fn`，不依赖网络/密钥；1.8 只验证 CLI 行为，不验证真实模型质量。

## 5. 风险与取舍

- **模板疲劳**：不是每章都值得 gate。判断标准：有没有可注入的失败？没有就写清单，不写 gate。
- **维护成本**：每增加一个 gate 就多一份 starter 和验收脚本；优先覆盖核心路径，选修线最后做。
- **真实质量**：gate 只验证结构/边界；真实 RAG/Agent 质量仍由评测集、真实模型和上线证据决定。
- **目录稳定**：不重命名章节，避免 82 章的交叉链接再次断裂；v2 顺序由标签表达。

## 6. 当前状态

- 阶段 1：完成。
- B1：完成（2026-10-18）。
- B2a：完成（2026-10-18）。
- B2b：完成（2026-10-18）。
- B3a：完成（2026-10-18）。
- B3b：完成（2026-10-18）。
- B4a：完成（2026-10-18）。
- B4b：完成（2026-10-18）。
- B4c：完成（2026-10-18）。
- B4d：完成（2026-10-18）。
- B5a：完成（2026-10-18）。
- B5b：下一批（5.3–5.5、5.7、5.8）。
- B6：排期中。
