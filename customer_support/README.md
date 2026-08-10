# 企业客服知识库助手 · Day54 产品版本

这是 Day51～54 累积得到的产品目录。当前主链包含自由问答、多文档摄取、混合检索、来源引用、拒答和离线评测。

## PyCharm 直接运行

只需配置一次：

1. 项目解释器选择 `D:\workspace\langchain-learning\.venv\Scripts\python.exe`。
2. 保持项目根目录 `D:\workspace\langchain-learning\customer_support` 为工作目录；当前代码包名为 `src`，不要把 `src` 单独作为工作目录。
3. 新建 Python Module 运行配置。
4. Module name 填 `src.app`。
5. Working directory 选择 `D:\workspace\langchain-learning\customer_support`。

以后直接点击 PyCharm 运行按钮，然后输入自己的问题。输入 `exit` 或 `退出` 结束，不需要配置 `PYTHONPATH`，也不需要填写运行参数。终端中也可运行 `python -m src.app`。

## 开发验收

开发评测单独建立 Module 运行配置：

```text
Module name: src.evaluation
Working directory: D:\workspace\langchain-learning\customer_support
```

自动化测试直接在 PyCharm 中右键 `tests` 目录运行。测试替身只存在于 `tests/`，不会进入主程序。

## 当前产品链

```text
用户输入
  → SupportApplication（补全短追问、保存会话历史）
  → LangGraph（验证 → 检索 → 回答）
  → 全部 Markdown 摄取
  → Chroma 语义检索 + BM25 关键词检索
  → RRF 融合
  → CustomerSupportAssistant
  → 有证据生成 / 无证据拒答
  → 答案和真实来源
```

当前聊天模型统一使用 DeepSeek `deepseek-chat`，需要在本机 `.env` 中配置 `LLM_API_KEY`；embedding 默认运行在 CPU。Ollama 适配器文件仅作为历史学习材料保留，不会被产品装配入口加载。持久化 API、身份、租户隔离和部署能力将在后续日期继续接入同一产品主链。

## 零基础阅读路线

这个项目解决的事情可以用一句话概括：**把散落在 Markdown 文件里的客服规则，变成“先找资料、再按资料回答”的本地问答程序。**

建议按下面的顺序阅读，不必一开始就理解所有 LangChain 类名：

1. `src/app.py`：程序入口。了解用户输入如何进入系统、回答怎样打印出来。
2. `src/bootstrap.py`：装配入口。了解配置怎样创建模型、检索器和助手。
3. `src/application.py` 与 `conversation.py`：短追问如何补全上一轮上下文，并保存本次会话记录。
4. `src/workflow.py`：验证、检索和回答如何被表示为一张有条件分支的 LangGraph 状态图。
5. `src/assistant.py`：核心业务规则。重点看“没有证据就拒答、有证据才调用模型、来源来自文档”。
6. `src/ingestion.py` 和 `knowledge.py`：资料如何从 Markdown 切成小块，再交给 Chroma 和关键词检索。
7. `src/retrieval.py`：为什么要同时使用语义检索与关键词检索，以及如何用 RRF 合并结果。
8. `tests/`：每个测试都是一个可运行的小例子；先读 `test_assistant.py`，能最快理解核心规则如何被验证。

### 先认识四个词

- **Markdown**：普通文本格式的文档，本项目把它作为客服资料来源。
- **Document**：LangChain 用来表示“一段正文 + 附加信息”的对象；附加信息可记录来源文件名。
- **向量（embedding）**：将一段文本转换成一串数字，方便比较两段文本在“意思”上是否接近。
- **检索（retrieval）**：根据用户问题从资料中找出可能相关的文档块；它负责找证据，不负责组织最终答案。
- **大语言模型（LLM）**：本项目中只在已经找到证据后，把证据组织成自然语言回复，不能替代知识库补充事实。
- **RRF**：一种把多份排序结果合并的方法。同一资料在多个检索通道都排得靠前时，会获得更高的综合分数。

### 一次提问实际发生了什么

```text
用户输入问题
  → 清理多余空格
  → 检索 Markdown 切出的文档块
  → 没有证据：直接提示转人工
  → 有证据：将证据和问题交给模型组织答案
  → 从文档元数据整理真实来源文件名并显示
```

当前边界：知识库在内存中构建，程序关闭后会重新创建；命令行界面尚未接入多轮对话历史；模型临时不可用时会提示稍后重试或转人工。
