# Day1–Day10 详细章节概括：从第一次调用到看懂 RAG 底层

这一组不是在背 LangChain API，而是在逐步搭出一个 AI 应用的基本骨架：模型调用、Prompt、输出控制、结构化数据、记忆、工具、RAG，以及框架背后的 harness。

## Day1 · 第一次和大模型对话

代码在：[day01/day01_first_chat.py](../day01/day01_first_chat.py)

Day1 做的事情是：**先把“Python 程序如何调用大模型”这条最短链路跑通，再理解 Prompt 模板和 LCEL 管道。**

### 1. 先从环境变量读取 API Key

代码先执行：

```python
load_dotenv()
```

再初始化模型：

```python
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
```

这里的重点不是 DeepSeek 这个名字，而是理解 `ChatOpenAI` 是一个统一的聊天模型调用接口。DeepSeek 兼容 OpenAI 的接口格式，所以通过 `base_url` 换成 DeepSeek 地址即可。

API Key 放在环境变量里，而不是直接写进代码，是因为代码可能上传 GitHub；密钥一旦泄露，别人就可以使用你的账号调用模型。

### 2. 学习最直接的 `invoke()`

```python
response = llm.invoke("用一句话解释什么是 RAG")
print(response.content)
```

调用链非常简单：

```text
Python 字符串
  → llm.invoke()
  → 模型返回 AIMessage
  → response.content 取出文字
```

`invoke()` 返回的不是普通字符串，而是一个消息对象。只有 `.content` 才是最终文本。

这种写法适合临时问一个问题，但不适合做一个可复用的产品：角色、问题和输出处理都混在一起了。

### 3. 学习 `system`、`human` 和 Prompt 占位符

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个 Python 专家，用简洁的中文回答"),
    ("human", "{question}"),
])
```

这里有三个关键点：

- `system`：告诉模型身份、规则和回答风格；
- `human`：代表用户这一轮真正提出的问题；
- `{question}`：占位符，调用时再填入具体内容。

调用时输入的是字典：

```python
prompt_value = prompt.invoke({"question": "什么是装饰器？"})
```

也就是说，Prompt 模板把“固定规则”和“变化问题”分开了。同一个 Prompt 可以反复回答很多问题，不需要每次重新拼字符串。

### 4. 学习 LCEL：`prompt | llm | parser`

```python
parser = StrOutputParser()
chain = prompt | llm | parser
result = chain.invoke({"question": "什么是装饰器？"})
```

这条链的输入输出是：

```text
{"question": "什么是装饰器？"}
  → Prompt 模板填充成消息
  → llm 生成 AIMessage
  → StrOutputParser 提取纯文本
```

`|` 的含义是“左边的输出交给右边”。每个组件都可以单独替换：换 Prompt、换模型、换解析器，不必重写整段业务代码。

### 5. Day1 最终要记住什么？

```text
llm.invoke("一句话")              → 临时调用模型
prompt.invoke({"question": ...}) → 填充模板
prompt | llm | parser             → 可复用调用链
```

Day1 还没有真正做 RAG。代码只是让模型解释“什么是 RAG”，真正的 RAG 会从 Day7 开始。

## Day2 · 控制模型怎么说话

代码在：[day02/day02_control_output.py](../day02/day02_control_output.py)

Day2 做的事情是：**在 Day1 已经会调用模型的基础上，学习怎么控制模型的输出方式。**

### 1. 学习 `temperature`

代码分别用：

```python
temperature=0.0
temperature=1.0
```

回答同一个问题：

```python
"用一句话形容大海"
```

目的不是改变模型知识，而是观察回答风格：

- `temperature=0`：更稳定、更保守，适合分类、抽取、评测、回归测试；
- `temperature` 较高：更有变化、更有创造性，适合写文案、头脑风暴。

核心认识是：

> 大模型不是每次都必须输出完全一样的答案，参数可以控制它的随机程度。

### 2. 学习流式输出 `stream`

Day1 使用：

```python
chain.invoke(...)
```

它会等模型全部生成完，再一次性返回。

Day2 使用：

```python
for chunk in chain.stream({...}):
    print(chunk, end="", flush=True)
```

它会让模型生成一部分就立刻输出一部分，形成“打字机效果”。

区别是：

```text
invoke()  → 等全部生成完 → 一次性返回
stream()  → 边生成边返回 → 用户更快看到内容
```

流式输出主要改善用户体验，特别适合聊天页面、客服系统和长回答场景。

### 3. 它仍然沿用 Day1 的链

Day2 的核心链还是：

```python
prompt | llm | parser
```

只是增加了两个控制点：

```python
llm = ChatOpenAI(..., temperature=temp)
```

以及：

```python
chain.invoke(...)
chain.stream(...)
```

所以 Day2 没有引入 RAG、Agent 或记忆，而是在解决两个实际问题：

- 模型回答要不要稳定、可复现？
- 用户要不要等模型全部生成完？

### 4. Day2 最终要记住什么？

```text
temperature=0  → 稳定性优先
temperature高  → 创造性优先
invoke()       → 一次性拿完整结果
stream()       → 边生成边展示
```

## Day3 · 从一段文字变成程序能用的数据

代码在：[day03/day03_structured_output.py](../day03/day03_structured_output.py)

Day3 做的事情是：**解决 Day1/Day2 的模型只返回自然语言、程序无法稳定取字段的问题。**

### 1. 用 Pydantic 定义输出契约

```python
class CodeReview(BaseModel):
    summary: str = Field(description="一句话总结这段代码做什么")
    issues: list[str] = Field(description="潜在问题列表，没有就空列表")
    score: int = Field(description="代码质量分，1-10 的整数")
```

这一步相当于告诉程序：我不想要一段随意的文字，我需要一个对象，并且它必须有 `summary`、`issues`、`score` 这些字段。

### 2. 让模型直接返回结构化对象

```python
structured_llm = llm.with_structured_output(
    CodeReview,
    method="function_calling",
)
chain = prompt | structured_llm
result = chain.invoke({"code": "..."})
```

拿到结果后可以直接访问字段：

```python
print(result.summary)
print(result.score)
print(result.issues)
```

这和普通文本输出的差别是：程序不需要再从一大段回答里猜评分在哪里、问题列表在哪里。

### 3. 为什么不只写“请输出 JSON”？

如果 Prompt 只是这样写：

```text
请严格输出 JSON：{"score": 1}
```

模型仍可能多输出解释、少字段、字段类型不对，之后还要手动解析和处理异常。`with_structured_output()` 会把 schema 作为模型调用约束，底层走 function calling，通常更稳定。

代码还用同样方法做情感分析：

```python
class SentimentResult(BaseModel):
    sentiment: str
    confidence: float
    keywords: list[str]
```

### 4. Day3 最终要记住什么？

```text
自然语言回答 → 人可以看
Pydantic 对象 → 程序可以取字段、入库、断言、评测
```

对测试工程师来说，这一天非常重要：自动化测试需要明确的字段和断言，而不是对一段模糊长文本凭感觉判断。

## Day4 · 让对话记住上文

代码在：[day04/day04_memory_chat.py](../day04/day04_memory_chat.py)

Day4 做的事情是：**解决模型每次调用都“失忆”的问题，让它能够进行多轮对话。**

### 1. 先理解模型为什么没有记忆

下面两次调用彼此独立：

```python
llm.invoke("我叫小明")
llm.invoke("我叫什么名字？")
```

第二次调用不会自动看到第一次的内容。模型没有持久记忆，应用必须把历史消息再次传给它。

### 2. 给 Prompt 留一个历史插槽

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友善的助手，用简洁中文回答"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])
```

`MessagesPlaceholder` 就是“把之前的对话放在这里”。本轮问题仍然通过 `{question}` 传入。

### 3. 用 `RunnableWithMessageHistory` 自动管理历史

```python
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

chat = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)
```

调用时必须带上会话 ID：

```python
config = {"configurable": {"session_id": "user_001"}}
chat.invoke({"question": "我叫小明，在学 LangChain"}, config=config)
chat.invoke({"question": "我刚才说我在学什么？"}, config=config)
```

同一个 `session_id` 表示同一段记忆；换成另一个 ID，就是另一段互不相干的对话。

### 4. Day4 的边界

这里使用的是 `InMemoryChatMessageHistory`，数据只存在内存中：程序一重启，记忆就没了。真正产品需要文件、数据库或 LangGraph checkpoint；Day60 才会把客服会话持久化到 SQLite。

### 5. Day4 最终要记住什么？

```text
模型没有记忆
  → 应用保存历史
  → 每次调用把历史重新塞进 Prompt
  → session_id 隔离不同用户
```

## Day5 · 让模型会调用工具

代码在：[day05/day05_tool_calling.py](../day05/day05_tool_calling.py)

Day5 做的事情是：**让模型不只会说话，还能通过工具获取真实结果或执行受控动作。**

### 1. 把普通函数注册成工具

代码定义了天气和计算器：

```python
@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气，输入城市名称，例如 '北京'"""
    data = {"北京": "晴天 25°C"}
    return data.get(city, f"{city}暂无数据")
```

`@tool` 不只是装饰器，它还会把函数名、参数和 docstring 变成模型可以理解的工具说明。

### 2. 把工具清单绑定给模型

```python
llm_with_tools = llm.bind_tools([get_weather, calculate])
```

绑定后，模型可以根据用户问题决定是否需要调用工具。例如：

```text
北京天气怎么样？再帮我算 99 * 88
```

模型可能返回两个 `tool_calls`，一个调用天气，一个调用计算器。

### 3. 工具调用实际上是两轮流程

第一轮不是最终答案：

```python
response = llm_with_tools.invoke(messages)
for call in response.tool_calls:
    result = tools_map[call["name"]].invoke(call["args"])
```

程序真正执行函数，再把结果包装成 `ToolMessage`：

```python
messages.append(
    ToolMessage(content=str(result), tool_call_id=call["id"])
)
```

第二轮再把完整消息发给模型：

```python
final = llm_with_tools.invoke(messages)
```

完整流程是：

```text
用户问题
  → 模型决定调用什么工具
  → 程序执行工具
  → ToolMessage 带回真实结果
  → 模型组织最终回答
```

### 4. Day5 的关键安全认识

判断模型是否想调用工具要看：

```python
response.tool_calls
```

不能只看 `response.content`。真实项目中，删除、转账、发邮件等有副作用的工具不能让模型自由执行，必须加权限、审批和审计。

### 5. Day5 最终要记住什么？

> Tool Calling 不是模型直接执行 Python 函数，而是模型提出调用请求，程序负责验证和执行，再把结果交回模型。

## Day6 · 拼出第一个命令行聊天机器人

代码在：[day06/day06_chatbot_project.py](../day06/day06_chatbot_project.py)

Day6 做的事情是：**把前几天的零件拼成一个真正能交互的小应用。**

### 1. 这个小项目组合了哪些能力？

```text
Day1：Prompt + LCEL 的调用思路
Day4：多轮历史
Day5：工具调用
```

用户可以选择三个角色：

```python
ROLES = {
    "1": ("Python老师", "你是一个耐心的 Python 编程老师，用简洁中文解答"),
    "2": ("计算器", "你是一个计算助手，需要算数时调用 calculator 工具"),
    "3": ("自由聊天", "你是一个友善的聊天伙伴，随意聊天"),
}
```

角色切换本质上是切换 system Prompt，不是切换一套完全不同的模型。

### 2. 它如何处理一次用户输入？

主循环大致是：

```text
读取用户输入
  → 处理 quit / clear
  → 把 system + history + question 组织成 messages
  → 调模型
  → 如果有 tool_calls：执行 calculator，再调用模型
  → 输出最终回答
  → 保存用户问题和最终回答
```

对应的工具分支是：

```python
if response.tool_calls:
    messages.append(response)
    for call in response.tool_calls:
        result = calculator.invoke(call["args"])
        messages.append(ToolMessage(...))
    final = llm_with_tools.invoke(messages)
```

### 3. 为什么计算器不能直接裸用 `eval`？

代码通过：

```python
eval(expression, {"__builtins__": {}}, vars(math))
```

限制可访问的名字，禁用内置函数，只开放 `math` 模块。它不是完整安全沙箱，但体现了一个原则：模型产生的参数必须经过边界控制，不能原样执行任意代码。

### 4. 它如何处理记忆和保存？

运行期间用 `InMemoryChatMessageHistory` 保存当前会话；输入 `clear` 清空历史，输入 `quit` 时把对话写入带时间戳的 txt 文件。

工具调用的中间消息不放入长期历史，只保存“用户问题 + 最终回答”，让后续上下文更干净。

### 5. Day6 最终要记住什么？

```text
一个小应用 = 角色设定 + 输入循环 + 历史 + 工具 + 输出保存
```

Day6 的重点不是新增一个 API，而是第一次体验“多个组件如何组成产品”。

## Day7 · RAG 第一步：加载文档和切块

代码在：[day07/day07_rag_load_split.py](../day07/day07_rag_load_split.py)

Day7 做的事情是：**正式进入 RAG，先完成建库流程里的“加载文档”和“切块”两步。**

### 1. 先理解 RAG 要解决什么问题

大模型默认不知道你的公司手册、内部 Wiki 或私有 FAQ。RAG 的思路是：

```text
先从私有文档检索证据
  → 把证据放进 Prompt
  → 让模型基于证据回答
```

完整 RAG 分两部分：

```text
建库：加载 → 切块 → 向量化 → 存储
问答：问题 → 检索 → 拼上下文 → 生成
```

Day7 先用 txt 演示前两步。需要注意：这里的 `txt` 只是为了把 RAG 的主线讲简单，企业文件还要在“加载”这一步增加格式解析和 OCR；不能把所有文件都当成普通字符串直接切。

### 2. 用 `Document` 统一表示文档

```python
with open("test_doc.txt", encoding="utf-8") as f:
    text = f.read()

docs = [Document(
    page_content=text,
    metadata={"source": "test_doc.txt"},
)]
```

`page_content` 是正文，`metadata` 是来源、页码、文档 ID 等附加信息。后面回答时，metadata 可以帮助系统告诉用户“答案来自哪个文件”。

### 3. 为什么要切 chunk？

```python
splitter = RecursiveCharacterTextSplitter(
    chunk_size=120,
    chunk_overlap=20,
    separators=["\n\n", "\n", "。", "，", " ", ""],
)
chunks = splitter.split_documents(docs)
```

如果把整篇长文档直接交给模型，会浪费 token，也会让模型难以抓住重点。切块后，检索时只拿最相关的几段。

`RecursiveCharacterTextSplitter` 会优先按段落、换行、句号、逗号切，最后才按字符切。`""` 必须放最后，否则会过早逐字切割。

### 4. 企业文件要“先解析，再切块”

`RecursiveCharacterTextSplitter` 处理的是**已经拿到的字符串或 `Document`**，它不是 PDF、PPT、Excel 或图片解析器。企业内容的正确处理顺序是：

```text
原始文件
  → 识别格式、做安全检查
  → 按格式解析 / OCR，得到段落、表格、页面、幻灯片等元素
  → 为元素补充 metadata，统一成 Document
  → 按结构切块，超长时再按 token 或字符兜底
  → embedding、入库
```

可以把它理解成两层工作：

```text
解析层：PDF/PPT/Excel/图片 → 可理解的内容元素
切块层：内容元素          → 适合检索的 chunks
```

常见格式的处理方式如下。这里的“初始单元”是开始切分时应该尽量保留的边界，不是说每个单元最终只能生成一个 chunk。

| 格式 | 先解析成什么 | 推荐的初始切分单元 | 必须保留的上下文 / 注意事项 |
|---|---|---|---|
| PDF | 页面、文本块、表格；扫描 PDF 先 OCR | 页或版面区块 | `source`、页码、标题；双栏、页眉页脚、表格不能只按字符顺序硬拼 |
| Word（`.doc/.docx`） | 标题、段落、列表、表格 | 标题层级下的段落组 | 把 `一级标题 > 二级标题` 作为路径重复到 chunk 中；表格可转 Markdown |
| PowerPoint（`.ppt/.pptx`） | 幻灯片标题、正文、备注、图表文字 | 一页 slide，过长再在页内切 | 保留 `slide` 和演示文稿标题；通常不要跨 slide 合并 |
| Excel（`.xls/.xlsx`） | 工作表、表头、数据区域、公式/值 | 一个表或带重复表头的行组 | 保留 `sheet`、表名、列名；精确统计、筛选、求和更适合走 SQL/表格工具，不要只靠向量检索 |
| PNG/JPG | OCR 文本、版面框、图片描述 | 一个版面区块或 OCR 段落 | 扫描件要记录 OCR；图表还应保留原图并考虑视觉模型，多模态信息不要只剩纯文字 |
| 音频（`.mp3/.wav/.m4a`） | 带时间戳、说话人标签的转写段落 | 完整语句或一个话题段（通常几十秒） | 保留 `start_sec`、`end_sec`、`speaker`、语言和 ASR 置信度；不要按固定秒数在一句话中间生硬截断 |
| 视频（`.mp4/.mov/.mkv`） | 音轨转写 + 关键帧 OCR/图片描述 + 镜头/幻灯片边界 | 一个镜头、一个 slide 或一段连贯发言 | 文本和画面必须按时间轴对齐；只索引音轨会漏掉屏幕上的图表、代码和字幕 |
| Markdown（`.md`） | 标题、正文、代码块、列表 | 按标题层级切，再做长度兜底 | 保留标题路径；代码块不要从中间切开 |
| HTML | 正文区域、标题、列表、表格、链接 | DOM 元素 / 标题层级 | 先去掉导航、页脚、广告和重复菜单；保留 URL、页面标题和标题路径 |
| ZIP | 解包后得到一批子文件 | 对每个子文件重新按扩展名路由 | ZIP 本身不是可检索正文；要限制大小、层数和文件数量，防止路径穿越、压缩炸弹和恶意文件 |

因此，“怎么切 Excel”与“怎么切 PDF”不是同一个答案：PDF 通常以页和版面为边界，PPT 以 slide 为边界，Excel 以表格和带表头的行组为边界，图片则要先 OCR 或图像理解。只有完成这一步，才适合调用通用文本切分器。

一个生产代码通常会把“格式解析”和“切块”拆成两个函数，后面的向量库完全不需要知道原始格式：

```python
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def parse_to_documents(path: str) -> list[Document]:
    """格式适配层：每种 parse_* 都负责保留自己的结构和来源。"""
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(path)       # 一般一页或一个版面区块一个 Document
    if suffix in {".doc", ".docx"}:
        return parse_word(path)      # 标题、段落、表格
    if suffix in {".ppt", ".pptx"}:
        return parse_powerpoint(path) # 一页 slide 一个或多个 Document
    if suffix in {".xls", ".xlsx"}:
        return parse_excel(path)     # sheet / 表格 / 带表头的行组
    if suffix in {".png", ".jpg", ".jpeg"}:
        return parse_image_with_ocr(path)
    if suffix in {".mp3", ".wav", ".m4a", ".aac"}:
        return parse_audio_with_asr(path)  # 语音转文字，保留时间戳和说话人
    if suffix in {".mp4", ".mov", ".mkv", ".webm"}:
        return parse_video(path)  # 音轨转写 + 关键帧 OCR/视觉解析，按时间轴合并
    if suffix == ".md":
        return parse_markdown(path)
    if suffix in {".html", ".htm"}:
        return parse_html_main_content(path)
    if suffix == ".zip":
        return parse_zip_recursively(path)  # 先安全解包，再路由子文件
    raise ValueError(f"不支持的文件类型：{suffix}")


def split_after_parsing(path: str) -> list[Document]:
    docs = parse_to_documents(path)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=["\n\n", "\n", "。", "！", "？", "，", " ", ""],
    )
    return splitter.split_documents(docs)
```

上面的 `parse_pdf()`、`parse_excel()` 等是格式适配器的示意，不是 LangChain 自动提供的同一个万能函数。可以使用专用库（例如 PDF、Word、PPT、Excel 的解析库），也可以使用统一的文档解析服务；选择时要看表格、版面、中文 OCR 和部署成本，而不是只看“能不能读出几行文字”。LangChain 的 loader 最终也会把结果统一成 `Document`，这正是后续切块和检索能够复用的原因。

### 5. 不同内容要选不同切分策略

```text
普通段落        → RecursiveCharacterTextSplitter
Markdown/HTML   → 先按标题或 DOM 结构切，再按长度兜底
PDF/Word        → 先按页、标题、段落、表格切，尽量不跨结构边界
PPT             → 先按 slide 切，标题和备注跟随 slide
Excel           → 先按表/行组切，并在每个行组重复列名
图片/扫描件     → OCR/视觉解析后切文字，同时保留原图引用
音频            → 先 ASR 转写、VAD 识别静音和说话边界，再按完整语句或话题段合并
视频            → 音轨按音频处理；关键帧按镜头/slide 提取 OCR 与视觉描述，再以时间轴合并
```

不要为了“每块长度一样”而牺牲语义完整性。一个好的 chunk 至少要能脱离原文件回答一个局部问题，同时带上足够的标题、页码、表头或来源信息。建议每个 chunk 至少保留这些 metadata：

```python
{
    "source": "员工手册.docx",
    "file_type": "docx",
    "page": 3,                 # PDF/扫描件可用
    "slide": None,             # PPT 可用
    "sheet": None,             # Excel 可用
    "start_sec": None,         # 音频/视频片段起始时间
    "end_sec": None,           # 音频/视频片段结束时间
    "speaker": None,           # 会议、访谈等场景可用
    "section": "报销制度/差旅住宿",
    "parent_id": "原始文档或元素 ID",
}
```

### 6. 音频与视频：按时间轴构建多模态 chunk

音频和视频不是把文件丢进文本切分器，而是先建立可回跳的时间轴。最小可用方案是把语音转写成文本；企业会议、培训录屏和客服录音通常还应保留说话人和画面信息。

```text
音频文件
  → 解码 / 语音活动检测（VAD）
  → ASR 语音转写（句子、起止时间、可选说话人）
  → 相邻短句按完整语义合并
  → 带时间戳的 Document chunks

视频文件
  → 分离音轨 ─────────────────────────→ 同一套 ASR 流程
  → 按镜头或 PPT 翻页提取关键帧 → OCR / 图像描述
  → 按相同时间窗合并“说了什么 + 画面有什么”
  → 带时间戳、关键帧引用的 Document chunks
```

例如一段培训视频的 chunk 可以长成这样：

```python
Document(
    page_content=(
        "[讲师 A，00:12:34–00:13:20] 报销单必须在费用发生后 30 天内提交。\n"
        "[画面 OCR] Slide：报销时限与审批规则"
    ),
    metadata={
        "source": "财务培训.mp4",
        "file_type": "mp4",
        "start_sec": 754.0,
        "end_sec": 800.0,
        "speaker": "讲师 A",
        "keyframe": "财务培训_00-12-34.jpg",
    },
)
```

这样检索命中后，前端不仅能展示答案和引用，还能直接跳到 `00:12:34` 播放。对“讲师说了什么”这类问题，主要检索转写文本；对“第几页 PPT 展示了什么图表”这类问题，还要检索 OCR、关键帧描述，必要时把关键帧交给视觉模型复核。

音视频还需要额外的工程处理：

- **ASR 和说话人处理**：使用能返回段落时间戳的语音识别；多人会议应做说话人分离（diarization）。术语、人名和产品编号可作为热词或词表传入，并抽样人工复核。
- **视频画面处理**：培训录屏优先用 slide/场景变化取帧，会议录像可降低取帧频率；不要机械地每秒存一帧，否则索引会膨胀且产生大量重复。
- **双通道索引**：转写文本与关键帧 OCR/描述可各自建索引，在检索阶段按时间戳合并，避免“声音的答案”和“画面的证据”对不上。
- **存储与权限**：向量库里存文本和时间戳，原音视频放对象存储；检索返回的播放链接必须复用原文件的访问控制，不能因 RAG 泄露会议录音。

还要增加两个企业场景经常漏掉的检查：

- **解析质量检查**：空文本、乱码、OCR/ASR 置信度过低、表格列错位、重复页眉页脚都要记录，不能“成功生成了 chunks”就当作解析成功。
- **增量与版本检查**：文件哈希、修改时间、解析器版本应进入索引记录。文件更新时只重建受影响的文档，避免每次全量 embedding。

Day12 会用 PDF 演示“格式加载 + 页码溯源”，Day17 会补图片/扫描件和视觉模型。音视频可以沿用相同的统一接口，只是页码换成时间戳、图片引用换成关键帧引用。Day7 的 txt 示例要学会的是统一的 `Document → chunks` 接口，而不是把生产环境限定成只能读取 txt。

### 7. Day7 的两个调参点

```text
chunk_size 小 → 更精准，但可能把完整语义切断
chunk_size 大 → 语义更完整，但无关噪声更多
chunk_overlap 大 → 边界更安全，但重复内容和成本更多
```

### 8. Day7 最终要记住什么？

> RAG 的第一步不是调用模型，也不是盲目按字符切文件，而是先把复杂文件解析成“有结构、有来源的 Document”，再加工成大小合适、语义完整、可检索的 chunks。

## Day8 · RAG 第二步：向量化和语义检索

代码在：[day08/day08_rag_embed_retrieve.py](../day08/day08_rag_embed_retrieve.py)

Day8 做的事情是：**在 Day7 的 chunks 上增加 embedding 和向量库，解决“从很多块里找哪几块”的问题。**

### 1. 用 embedding 把文字变成向量

```python
embeddings = HuggingFaceEmbeddings(model_name=MODEL_PATH)
vec = embeddings.embed_query(chunks[0].page_content)
```

一段文字会变成固定维度的数字向量。语义相近的文字，通常在向量空间里的距离也更近。这里使用中文 `bge-small-zh-v1.5`，代码还打印向量维度和前几个数字，让这个过程不再是黑盒。

### 2. 用 FAISS 保存向量并找近邻

```python
vectorstore = FAISS.from_documents(chunks, embeddings)
results = vectorstore.similarity_search("RAG 是什么", k=3)
```

建库时，FAISS 会把每个 chunk 转成向量；查询时，也把问题转成向量，然后找最相似的 `k` 个块。

```text
问题 → 问题向量
文档块 → 文档向量
比较距离 → 返回最相近的文档块
```

它比单纯关键词匹配更能理解“怎么存向量”和“FAISS 有什么作用”这类表达差异。

### 3. `k` 是一个重要参数

```python
similarity_search(query, k=3)
```

- `k` 太小：可能漏掉必要证据；
- `k` 太大：会带入无关块，增加 Prompt 长度和生成噪声。

Day8 的 FAISS 只在内存中，程序结束后数据消失；后续 Day16 会学习 Chroma 持久化。

### 4. Day8 最终要记住什么？

```text
Document chunks
  → Embedding
  → FAISS 向量索引
  → similarity_search
  → 相关文档块
```

Day8 仍然没有让模型回答，只解决了 RAG 的“检索”部分。

## Day9 · 把检索和生成串成完整 RAG

代码在：[day09/day09_minimal_rag.py](../day09/day09_minimal_rag.py)

Day9 做的事情是：**把 Day7 的文档处理、Day8 的向量检索和 Day1 的模型调用接成第一条完整 RAG 问答链。**

### 1. 用 retriever 包装向量库

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,
        "fetch_k": 10,
        "lambda_mult": 0.5,
    },
)
```

这里不是简单取最相似的前三块，而是先取 10 个候选，再用 MMR 在相关性和多样性之间平衡，减少三块内容高度重复的问题。

### 2. 用 `RunnableParallel` 同时准备上下文和原问题

```python
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)
```

输入一个问题时，字典会同时做两件事：

```text
context 路：问题 → retriever → 找文档 → 拼成上下文
question 路：问题 → RunnablePassthrough → 原样保留
```

两路汇成：

```python
{
    "context": "检索到的内容",
    "question": "用户问题",
}
```

再进入 Prompt、模型和输出解析器。

### 3. 用 Prompt 限制幻觉

```text
请只根据下面的上下文回答问题。
如果上下文里没有答案，就说：我不知道。
```

代码测试了三个资料内问题和一个“今天天气怎么样”的资料外问题。资料外问题应该拒答，而不是让模型凭常识自由发挥。

### 4. Day9 最终要记住什么？

```text
问题
  → Retriever 检索
  → format_docs 拼上下文
  → Prompt 约束回答
  → LLM 生成
  → Parser 输出文本
```

完整 RAG 不是“向量库 + 模型”这么简单，真正的质量还取决于切块、召回数量、上下文拼接和拒答规则。

## Day10 · 不用 LangChain，手写 RAG 和 Agent Loop

代码在：[day10/day10_raw_sdk_rag_agent_loop.py](../day10/day10_raw_sdk_rag_agent_loop.py)

Day10 做的事情是：**故意脱离 LangChain，用标准库和裸 HTTP 手写一遍 RAG 与最小 Agent，让你看清框架到底替你封装了什么。**

### 1. 手写文档切块和关键词检索

代码定义了自己的 `Chunk`：

```python
@dataclass
class Chunk:
    text: str
    source: str
    index: int
```

然后用 `split_text()` 切块，用 `tokenize()` 把中文、英文和数字拆成 token，再用词频向量和余弦相似度计算相关性：

```python
score(query, chunk)
retrieve(query, chunks, k=3)
```

这不是工业级检索，而是为了让你看到：一个最简单的检索器也需要文本切分、token 化、打分、排序和 top-k。

### 2. 手写 OpenAI 兼容 HTTP 调用

```python
API_URL = "https://api.deepseek.com/chat/completions"
payload = {
    "model": MODEL,
    "messages": messages,
    "temperature": temperature,
}
```

`chat()` 用标准库 `urllib.request` 发送请求，手动处理 API Key、JSON、超时和返回字段。没有配置 Key 时，代码进入离线提示，保证文件仍然可读可运行。

### 3. 手写最小 RAG

```python
def raw_rag_answer(question, chunks):
    hits = retrieve(question, chunks)
    if not hits:
        return "文档中没有提到。"
    context = "\n\n".join(...)
    messages = [
        {"role": "system", "content": "只依据上下文回答；无依据就拒答。"},
        {"role": "user", "content": f"上下文：{context}\n问题：{question}"},
    ]
    return chat(messages)
```

这和 Day9 的逻辑完全对应，只是之前由 LangChain 组件完成，现在全部显式写出来。

### 4. 手写最小 ReAct Agent Loop

模型被约定为两种输出：

```text
Action: calculator[1+1]
Final: 最终答案
```

程序用正则解析 `Action`：

```python
action = parse_action(thought)
observation = tool(arg)
messages.append({"role": "user", "content": f"Observation: {observation}"})
```

然后循环调用模型，直到模型输出 `Final:`，或者达到 `max_steps`：

```python
for step in range(1, max_steps + 1):
    ...
return "达到最大步数，停止执行。"
```

### 5. Day10 最终要记住什么？

```text
LangChain 帮你封装的不是魔法，而是 harness：
检索、Prompt 拼接、消息格式、工具解析、循环、停止条件、错误兜底和日志。
```

Day10 结束时，你应该能解释一个 Agent 为什么会继续循环、为什么会停、工具结果怎样回到模型，以及框架出问题时应该去哪一层查。

## Day1–Day10 总结：这一组到底搭了什么？

```text
直接调用模型
  → 控制稳定性和流式体验
  → 结构化输出
  → 多轮记忆
  → 工具调用
  → 命令行聊天应用
  → 文档加载和切块
  → 向量检索
  → 完整 RAG
  → 手写底层 harness
```

这十天的终点不是“会写一行 LangChain”，而是能看懂一条 AI 应用链路从输入到输出经过了哪些步骤。
