# L3.6 LangSmith 可观测性 · 清单验收

> 3.6 依赖 LangSmith 外部服务，做不出可重复的离线 gate。这里用**可核对清单**代替 gate：
> 不硬造 `gate_check.py`，也不把“跑通一次”当成可观测性验收。

## 前置

- `LANGSMITH_API_KEY` 已配置（`.env`，不要提交）。
- `DEEPSEEK_API_KEY` 和本地 embedding 模型可用。
- 已运行 3.4/3.5 生成 `chapters/shared-data/eval_set_full.json`（在线评估需要）。

## 步骤

1. 运行 `python tools/run_chapter.py 3.6`，确认输出一次 RAG 回答。
2. 打开 LangSmith 的 `rag-evaluation` 项目，找到这次 trace；记录 experiment/run 链接或截图。
3. 在 trace 里核对至少三步：
   - retriever 召回了哪些片段；
   - prompt 实际收到的上下文；
   - LLM 的输入/输出。
4. 故意制造一次失败（例如临时用错误的 `DEEPSEEK_API_KEY`，或把 `base_url` 指向不可达地址），再跑一次；在 trace 里找到失败的步骤和错误信息。
5. 运行在线评估部分（配置了 key 时），确认 dataset 和 experiment 已创建；记录 experiment 名称。
6. 检查证据里没有密钥、没有真实用户隐私；只保留脱敏后的链接/截图和文字观察。

## 验收标准

- [ ] 至少一条成功 trace 的链接/截图。
- [ ] 能指出检索、prompt、LLM 三步的实际内容。
- [ ] 至少一条失败 trace，并能说出失败发生在哪一步。
- [ ] 在线评估的 dataset/experiment 已创建（没有 key 时明确写“未验证”）。
- [ ] 证据中没有密钥、token、真实用户 PII。

## 记录模板

```text
日期：
LangSmith 项目：
成功 trace（链接/截图）：
三步观察：
  1. retriever：
  2. prompt：
  3. LLM：
失败 trace：
  失败步骤：
  错误信息：
在线评估：
  dataset：
  experiment：
未验证：
```

## 边界

- LangSmith 是外部服务；离线测试通过不代表 trace 已上报。
- trace 可视化不等于质量评测；质量仍要看 3.2–3.5、3.7。
- 不要把 trace 链接、密钥、用户问题直接提交到公开仓库；先脱敏。
