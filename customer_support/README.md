# 企业客服知识库助手 · Day54 产品版本

这是 Day51～54 累积得到的产品目录。当前主链包含自由问答、多文档摄取、混合检索、来源引用、拒答和离线评测。

## PyCharm 直接运行

只需配置一次：

1. 项目解释器选择 `D:\workspace\langchain-learning\.venv\Scripts\python.exe`。
2. 将 `customer_support/src` 标记为 Sources Root。
3. 新建 Python Module 运行配置。
4. Module name 填 `customer_support.app`。
5. Working directory 选择 `D:\workspace\langchain-learning\customer_support`。

以后直接点击 PyCharm 运行按钮，然后输入自己的问题。输入 `exit` 或 `退出` 结束，不需要配置 `PYTHONPATH`，也不需要填写运行参数。

## 开发验收

开发评测单独建立 Module 运行配置：

```text
Module name: customer_support.evaluation
Working directory: D:\workspace\langchain-learning\customer_support
```

自动化测试直接在 PyCharm 中右键 `tests` 目录运行。测试替身只存在于 `tests/`，不会进入主程序。

## 当前产品链

```text
用户输入
  → 全部 Markdown 摄取
  → Chroma 语义检索 + BM25 关键词检索
  → RRF 融合
  → CustomerSupportAssistant
  → 有证据生成 / 无证据拒答
  → 答案和真实来源
```

默认使用本机 Ollama `qwen3.5:9b`，embedding 默认运行在 CPU。Day54 是本地可运行里程碑，持久化 API、身份、租户隔离和部署能力将在后续日期继续接入同一产品主链。
