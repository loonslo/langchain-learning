# Day51：企业客服知识库助手

这是一个最小可运行的客服 RAG 项目。程序先从本地 FAQ 检索证据；没有命中证据时直接拒答，不调用聊天模型；命中后才让模型整理答案，并从检索文档的 metadata 返回来源。

## 项目结构

```text
customer_support/
├── data/knowledge/customer_faq.md
├── src/customer_support/
│   ├── settings.py    # 读取模型、资料路径与检索配置
│   ├── knowledge.py   # 加载、切块并创建 Chroma Retriever
│   ├── assistant.py   # 输入检查、证据分支、回答与来源整理
│   ├── ollama_model.py # 本地 Ollama HTTP 适配器
│   ├── bootstrap.py   # 创建 embedding、Retriever 与聊天模型
│   └── cli.py         # 命令行入口
├── tests/
├── .env.example
├── .gitignore
└── pyproject.toml
```

## 运行

```powershell
python -m pip install -e .
Copy-Item .env.example .env
support-assistant --check-data
support-assistant --question "退款多久到账？"
python -m pytest -q
```

默认使用本机 Ollama 的 `qwen3.5:9b`，embedding 在 CPU 上运行。本地适配器会省略未使用的 `tools` 字段，避开当前环境中空工具数组导致的 502。要改用 DeepSeek，请在本机 `.env` 中切换 provider 并填写密钥；不要把 `.env` 提交到仓库。

## 当前边界

- `0.55` 是待评测的相关度起始值，不代表生产最优值。
- Chroma 仅在内存中创建，程序重启后会重新构建。
- 当前只有一份示例 FAQ，尚未包含权限过滤、对话记忆和线上评测。
