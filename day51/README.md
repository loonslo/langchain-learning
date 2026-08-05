# Day51 · 建立客服知识问答的最小闭环

Day51 是毕业项目的第一次真实提交。今天不是先背 RAG 名词，而是完成一个可观察的用户任务：

> 用户输入客服问题；系统先找本地资料，有证据才调用模型组织答案，并返回真实来源；没有证据时在调用模型前拒答。

## 1. 这四天怎样学习

从 Day51 开始，每天固定使用同一个顺序：

1. 在 workbook.md 写下运行前预测。
2. 运行或阅读代码，记录实际现象。
3. 用测试证明一条具体业务规则。
4. 主动破坏一行保护，看到对应测试失败后恢复。
5. 当天结束前观察一个尚未解决的问题，把证据留给下一天。

不要在刚打开 Day 时直接从头抄代码。代码回答“怎样实现”，工作簿先帮助你弄清“用户要什么、当前哪里失败、为什么值得改”。

## 2. 先定义用户眼中的正确行为

先打开 [customer_faq.md](data/knowledge/customer_faq.md)，不要打开 assistant.py。

在 [workbook.md](workbook.md) 第 1 节判断：

- “退款多久到账？”资料里是否有证据？
- “黑金会员有什么权益？”资料里是否有证据？
- 订单发货后还能否直接修改地址？

这一步的目的不是考记忆，而是先建立验收标准。否则模型生成一句流畅文字时，你没有依据判断它究竟对不对。

## 3. Day 目录怎样组成完整项目

从现在开始，每个 dayNN 只保存当天新增或修改的完整文件：

- README 记录当天结束后的完整结构。
- 当天没有修改的文件只出现在结构图，不重复复制。
- 文件再次修改时，对应 Day 保存它截至当天的完整版本。
- tools/materialize_day.py 会按日期依次覆盖，重建指定日期的完整项目。

Day51 是第一次提交，所以全部项目文件都在今天创建：

~~~text
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
~~~

customer_support 不是 pip 安装的第三方库，而是 src/customer_support 下今天创建的项目包。包内的 from .assistant import ... 中，点表示“从当前包导入”。

## 4. 先认识请求链中的对象

| 名称 | 人话解释 | 从哪里来 | 交给谁 |
|---|---|---|---|
| Path | 文件路径对象 | Settings.knowledge_path | TextLoader |
| Document | 正文和 metadata 的容器 | TextLoader.load | Splitter 或 Retriever |
| chunk | 切小后的 Document | split_documents | Embedding 和 Chroma |
| embeddings | 把文字转换成向量的模型 | build_embeddings | Chroma |
| vector_store | 保存向量并计算相似度 | Chroma.from_documents | retriever |
| retriever | 输入问题，返回相关 Document | build_retriever | CustomerSupportAssistant |
| messages | 填好 context 和 question 的消息 | PROMPT.invoke | ChatModel |
| SupportAnswer | 稳定的答案和来源结果 | assistant.ask | CLI |

三类 import 也要分清：

~~~python
from pathlib import Path
from langchain_core.documents import Document
from .assistant import CustomerSupportAssistant
~~~

它们分别来自 Python 标准库、安装的第三方库和本项目当前包。

## 5. 先画职责，再读实现

~~~text
cli.py
  │ 接收命令行参数
  ▼
bootstrap.py ──创建──> embedding / retriever / LLM
  │                         ▲
  │                         │ knowledge.py
  ▼
assistant.py ──执行──> 检索 → 拒答或生成 → 来源
  ▲
  │
settings.py + data/knowledge/customer_faq.md
~~~

这些文件不是为了显得像“大项目”，而是因为变化原因不同：

- 政策内容变化：修改 data/knowledge。
- 检索实现变化：修改 knowledge.py。
- 回答和拒答规则变化：修改 assistant.py。
- 模型与机器环境变化：修改环境配置或 bootstrap.py。
- 用户入口变化：修改 cli.py，业务规则仍复用 assistant。

在 workbook.md 第 2、3 节填写每个文件的输入、输出和一次请求的数据流。

## 6. 按观察顺序动手

所有命令先从仓库根目录开始：

~~~powershell
cd D:\workspace\langchain-learning
~~~

### 第一步：看资料如何变成可检索对象

打开 day51/src/customer_support/knowledge.py，依次跟踪：

~~~python
load_chunks(...)
build_retriever(...)
~~~

在纸上补全：

> 文件路径 → Document → chunks → Chroma → retriever

重点观察 source metadata 在哪里写入，以及 threshold 为什么允许 retriever 返回空列表。

### 第二步：跟踪有证据与无证据两条分支

打开 day51/src/customer_support/assistant.py，找到 ask。不要逐行翻译语法，先找七个动作：

1. 清理问题。
2. 拒绝空输入。
3. 调用 retriever。
4. 无证据时提前结束。
5. 把 Document 正文放入 Prompt。
6. 调用模型组织答案。
7. 只从 Document.metadata 生成来源。

在 workbook.md 第 3 节先写预测，再对照代码修正。

### 第三步：理解真实对象在哪里创建

打开 bootstrap.py。CustomerSupportAssistant 不负责选择 DeepSeek、Ollama 或 embedding 模型；它只使用外部交给它的两个能力。这样测试可以换成不会联网的 Fake。

### 第四步：先跑离线测试

~~~powershell
cd D:\workspace\langchain-learning\day51
..\.venv\Scripts\python.exe -m pytest -q
~~~

这些测试不调用真实模型。不要只记录 passed，要在 workbook.md 第 4 节写清每条测试保护的业务风险。

### 第五步：运行数据检查

~~~powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe -m customer_support.cli --check-data
~~~

记录知识库路径、切块数量和来源。这个输出将在今天结束时用于发现下一步问题。

### 第六步：可选的真实问答

复制 .env.example 为 .env 并填写配置后运行：

~~~powershell
..\.venv\Scripts\python.exe -m customer_support.cli --question "退款多久到账？"
~~~

再问一个资料外问题。真实模型可能产生费用；如果环境不可用，离线测试仍可完成今天的核心学习。

## 7. 主动破坏一次保护

按 workbook.md 第 6 节选择一个实验：

- 删除“documents 为空就拒答”的分支，观察哪个测试阻止模型在无证据时运行。
- 或让来源不再取自 Document.metadata，观察引用测试怎样失败。

实验前先预测，实验后立即恢复，并重新跑到全绿。思考发生在“预测与实际是否一致”这里，而不是发生在照抄代码时。

## 8. 还原 Day51 完整项目

~~~powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 51
cd .build\day51\customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
..\..\..\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
~~~

materialize 目录只包含项目文件，不包含课程 README 和工作簿。

## 9. 今天的测试到底证明什么

| 测试行为 | 能证明 |
|---|---|
| 已知问题返回答案和来源 | 主业务分支能够组合检索结果与模型结果 |
| 无证据时不调用模型 | 拒答发生在生成之前 |
| 来源只取自 Document | 不相信模型自报的引用 |
| 空问题在检索前失败 | 无效输入不会浪费检索和模型调用 |
| 真实 FAQ 能加载和切块 | 代码不是只对 Fake 数据生效 |

它们不能证明 0.55 是最佳阈值，也不能证明真实模型永远正确。

## 10. 在结束前发现 Day52 的问题

不要直接背“单文件无法维护”这句话。完成 workbook.md 第 7 节，亲自观察：

- Settings.knowledge_path 只指向 customer_faq.md。
- load_chunks 一次只处理一个文件。
- --check-data 只展示一个来源。

再设想退款和配送由两个团队分别维护。根据这三个代码事实，写下当前方式会遇到的具体困难。

Day52 将从你记录的现象继续，而不是突然宣布一个新术语。

## 11. 完成标准

完成 workbook.md，并能不看代码解释：

1. 用户问题怎样走到最终答案？
2. 为什么无证据时不能只靠 Prompt 约束模型？
3. 为什么来源来自 Document.metadata？
4. 哪条测试证明模型在拒答时没有被调用？
5. 当前程序为什么只认识一份资料？
