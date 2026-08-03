# Day51 · 客服知识库助手 v0.1

Day51 是毕业项目的第一次真实提交。今天不创建一个叫 `app.py` 的孤立 Demo，而是从零建立一个具有真实 Python 项目结构、可以测试和运行的客服 RAG。

> 今天交付：用户输入客服问题，系统从本地 FAQ 检索证据，只根据证据回答，并返回真实来源；检索不到证据时，在调用模型前拒答。

## 1. 先理解 Day 目录的规则

从现在开始，每个 `dayNN/` 只保存当天新增或修改的完整文件。

- README 记录当天结束后的完整项目结构。
- 当天没有修改的文件只显示在结构图中，不会被重复复制。
- 某个文件再次修改时，会在对应 Day 中保存它截至当天的完整版本。
- `tools/materialize_day.py` 可以依次覆盖 Day51 到指定日期，重建当天完整项目。
- Day78 会得到最终完整交付版本。

Day51 是第一次提交，所以结构图中的所有项目文件都是今天新增。

### `customer_support` 从哪里来

`customer_support` 不是 pip 安装的第三方库，也不是 Day50 留下来的代码。它就是今天创建的项目包：

```text
day51/src/customer_support/
```

其中的 `__init__.py` 告诉 Python：这个目录是一个包。包内部使用相对导入：

```python
from .assistant import CustomerSupportAssistant
from .knowledge import build_retriever
```

开头的 `.` 表示“从当前 `customer_support` 包中导入”，不会去引用另一个项目。

测试中的下面这种写法：

```python
from customer_support.assistant import CustomerSupportAssistant
```

则是站在包外，像真实调用方一样使用今天创建的项目包。`pyproject.toml` 中的 `pythonpath = ["src"]` 让 pytest 能在 `src/` 下找到它；运行 CLI 前设置 `$env:PYTHONPATH = "src"` 也是同一个目的。

## 2. Day51 结束后的完整项目结构

```text
customer-support/
├── .env.example
├── pyproject.toml
├── data/
│   └── knowledge/
│       └── customer_faq.md
├── src/
│   └── customer_support/
│       ├── __init__.py
│       ├── settings.py
│       ├── knowledge.py
│       ├── assistant.py
│       ├── bootstrap.py
│       └── cli.py
└── tests/
    ├── test_assistant.py
    └── test_knowledge.py
```

这些文件目前物理保存在 `day51/` 下，并保持与真实项目相同的相对路径。

## 3. 今天新增了哪些文件

| 项目路径 | 今天的职责 |
|---|---|
| [`pyproject.toml`](pyproject.toml) | 声明项目名、依赖、命令行入口、src 布局和测试路径 |
| [`.env.example`](.env.example) | 告诉使用者需要配置哪些模型环境变量，不保存真实密钥 |
| [`data/knowledge/customer_faq.md`](data/knowledge/customer_faq.md) | 第一版真实业务资料 |
| [`src/customer_support/settings.py`](src/customer_support/settings.py) | 集中读取模型、知识库路径和检索阈值 |
| [`src/customer_support/knowledge.py`](src/customer_support/knowledge.py) | 加载、切块、向量化并创建 retriever |
| [`src/customer_support/assistant.py`](src/customer_support/assistant.py) | 执行一次完整的检索问答用例 |
| [`src/customer_support/bootstrap.py`](src/customer_support/bootstrap.py) | 创建真实 embedding、LLM，并组合业务对象 |
| [`src/customer_support/cli.py`](src/customer_support/cli.py) | 命令行产品入口 |
| [`tests/test_assistant.py`](tests/test_assistant.py) | 验证回答、拒答、来源和空输入四条业务规则 |
| [`tests/test_knowledge.py`](tests/test_knowledge.py) | 验证真实 FAQ 能加载且 metadata 没丢失 |

今天没有“继承但不修改”的文件，因为项目刚刚开始。

## 4. 阅读源码前先认识这些对象

Day51 源码里同时出现 Python 对象和 LangChain 对象。先把它们翻译成人话：

| 名称 | 它是什么 | 本项目中从哪里来 | 交给谁 |
|---|---|---|---|
| `Path` | Python 表示文件路径的对象 | `Settings.knowledge_path` | `TextLoader` |
| `Document` | LangChain 的“正文 + metadata”容器 | `TextLoader.load()` | Splitter 或 Retriever |
| `chunk` | 被切小后的 `Document`，不是新的特殊类型 | `split_documents()` | Embedding 和 Chroma |
| `embeddings` | 把文本变成数字向量的模型 | `build_embeddings()` | `Chroma.from_documents()` |
| `vector_store` | 保存向量并计算相似度 | `Chroma.from_documents()` | `as_retriever()` |
| `retriever` | 输入问题、输出相关 `Document` 的统一接口 | `build_retriever()` | `CustomerSupportAssistant` |
| `messages` | system/human Prompt 填入变量后的消息列表 | `PROMPT.invoke()` | ChatModel |
| `response` | 聊天模型返回的 `AIMessage` 一类对象 | `model.invoke()` | 提取 `.content` |
| `SupportAnswer` | 项目自己定义的最终结果 | `assistant.ask()` | CLI，未来也会给 API |

还要区分三类 import：

```python
from pathlib import Path                     # Python 标准库
from langchain_core.documents import Document  # pip 安装的第三方库
from .assistant import CustomerSupportAssistant # Day51 自己创建的包内模块
```

`Protocol` 也不是一个新框架。它只表达“传进来的对象至少要有哪个方法”。因此真实
Chroma Retriever 和测试 FakeRetriever 都能交给 `CustomerSupportAssistant`，业务类
不需要判断它们具体是什么类。

## 5. 为什么这样拆文件

```text
cli.py
  │ 读取参数
  ▼
bootstrap.py ──创建──> embedding / retriever / LLM
  │                         ▲
  │                         │ knowledge.py
  ▼
assistant.py ──执行──> 检索 → 拒答或生成 → 来源
  ▲
  │
settings.py + data/knowledge/customer_faq.md
```

这里不是为了追求文件数量，而是分开三种变化原因：

- 政策资料变化：修改 `data/knowledge/`。
- 检索与回答规则变化：修改 `knowledge.py` 或 `assistant.py`。
- 模型提供商和机器环境变化：修改 `.env` 或组合入口，不污染业务规则。

如果所有内容都塞进 `app.py`，Day52 开始增加多文档时就很难判断应该改哪一层。

## 6. 按这个顺序动手

所有命令先从仓库根目录开始：

```powershell
cd D:\workspace\langchain-learning
```

### 第一步：人工检查产品资料

打开 `day51/data/knowledge/customer_faq.md`，判断：

- “退款多久到账？”有明确证据，应该回答。
- “黑金会员有什么权益？”没有证据，应该拒答。

把判断写进 `workbook.md`，先定义正确行为，再看模型输出。

### 第二步：看资料怎样进入检索器

打开 `day51/src/customer_support/knowledge.py`，依次搜索：

```python
def load_chunks(...)
def build_retriever(...)
```

跟踪：文件路径 → `Document` → chunks → Chroma → 带 `0.55` 阈值的 retriever。

### 第三步：跟踪一次问答

打开 `day51/src/customer_support/assistant.py`，搜索：

```python
def ask(self, question: str)
```

按顺序确认：清理输入、拒绝空问题、检索、无证据提前拒答、构造 Prompt、调用 LLM、从 `Document.metadata` 取来源。

### 第四步：理解依赖在哪里创建

打开 `day51/src/customer_support/bootstrap.py`。`CustomerSupportAssistant` 不应该自己读取环境变量或决定使用 DeepSeek/Ollama；这些运行选择集中在组合入口。

同时观察文件开头的 `.assistant`、`.knowledge`、`.settings`：它们全部是 Day51 当天创建的包内模块。

### 第五步：先跑离线验收

```powershell
cd D:\workspace\langchain-learning\day51
..\.venv\Scripts\python.exe -m pytest -q
```

预期：`5 passed`。这些测试不调用真实模型，不消耗 API 费用。

### 第六步：运行数据检查

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe -m customer_support.cli --check-data
```

你应该看到知识库绝对路径、切块数量和 `customer_faq.md` 来源。

### 第七步：运行真实问答

先把 `.env.example` 复制为 `.env` 并填写自己的配置，然后执行：

```powershell
..\.venv\Scripts\python.exe -m customer_support.cli --question "退款多久到账？"
```

真实模型调用可能产生费用。再问资料外问题，观察相关度阈值过滤后是否进入拒答分支。

## 7. 还原 Day51 的完整项目

回到仓库根目录执行：

```powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 51
```

生成位置：

```text
.build/day51/customer-support/
```

它不包含课程 README 和工作簿，只包含可以交付的项目文件。进入生成目录后，同样可以运行测试：

```powershell
cd .build\day51\customer-support
..\..\..\.venv\Scripts\python.exe -m pytest -q
```

## 8. 今天必须理解的五条测试

| 测试 | 保护的生产行为 |
|---|---|
| 已知问题返回回答和来源 | 主业务路径可用 |
| 无证据时不调用模型 | 防止模型脱离资料编造 |
| 来源只取自 Document | 防止相信模型伪造的引用 |
| 空问题在检索前失败 | 无效请求不浪费资源 |
| 真实 FAQ 能加载和切块 | 项目不是只对 fake 生效 |

## 9. Day51 仍未解决什么

- 只有一份小型 Markdown，无法管理多来源资料。
- `0.55` 是起始阈值，还没有评测数据证明它合适。
- 没有连续对话、订单工具和人工工单。
- 没有 API、身份、安全、观测和部署。
- Chroma 使用临时 collection，进程结束后不保留索引。

这些不是漏做，而是后续迭代的真实原因。Day52 必须从“单文件知识库难以维护”这个问题继续，而不是突然学习另一个无关名词。

## 10. 完成标准

完成 `workbook.md`，并且不看代码解释：

1. `knowledge.py` 和 `assistant.py` 各自负责什么？
2. Retriever 和 LLM 的职责为什么不能混在一起？
3. 为什么来源必须来自 `Document.metadata`？
4. 为什么无证据时要在调用模型之前结束？
5. 为什么 Day51 先使用真实项目路径，而不是一个 `app.py`？
