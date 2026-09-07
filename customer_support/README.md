# 企业客服知识库助手 · Day54 产品版本

这是 Day51～54 累积得到的后端产品目录。Day79 的独立浏览器前端位于仓库根目录的 `day79/`。

## Windows、macOS 通用启动方式

建议在项目根目录使用 [uv](https://docs.astral.sh/uv/) 创建统一命名的虚拟环境：

```shell
uv sync --python 3.12
```

复制 `.env.example` 为 `.env`，填写真实的 `LLM_API_KEY`，然后运行：

```shell
uv run python -m src.app
```

以上命令在 PowerShell、cmd、zsh 和 bash 中相同，不需要添加 PowerShell 的 `&`
运算符，也不需要手写 `.venv` 中的解释器路径。

## 网页界面（HTTP 服务 + 静态前端）

后端已封装为 FastAPI 服务（`src/server.py`，复用 `src/api.py` 的契约）。

### 一键启动（推荐）

同时拉起后端 API 与前端静态站点，并自动打开浏览器：

```shell
# 方式一：命令行
uv run python run.py
# 仅启动不自动开浏览器：
uv run python run.py --no-browser

# 方式二：Windows 双击 run.bat（已内置 HF_HUB_OFFLINE=1 与 TMPDIR）
run.bat
```

默认地址（均绑定 127.0.0.1，仅本机访问）：

- 网页界面：`http://127.0.0.1:19888/`
- API 文档：`http://127.0.0.1:19100/docs`

端口可用参数覆盖：`uv run python run.py --backend-port 19100 --frontend-port 19888`。

### 仅启动后端

```shell
# 默认监听 127.0.0.1:19100（8000/8080 在 Windows 上常被 Hyper-V 保留，会导致 bind 失败）
uv run support-assistant --serve
# 或显式指定端口：
uv run support-assistant --serve --port 19100
```

- 接口：`GET /health`、`POST /chat`（字段见 `src/api.py` 的 `ChatRequest`/`ChatResponse`）。
- 多轮对话通过 `session_id` + SQLite 会话库持久化，跨请求保留上下文。

打开前端页面（纯静态，无需 npm 构建）：

```shell
# 用浏览器直接打开，或将 frontend/ 作为静态目录托管
# 页面默认连接 http://127.0.0.1:19100，与上面的服务端口一致
start frontend/index.html
```

### 模型 provider 切换

`.env` 通过 `LLM_PROVIDER` 选择对话模型：

- `LLM_PROVIDER=deepseek`：云端 DeepSeek，需要 `LLM_API_KEY`。
- `LLM_PROVIDER=ollama`：本地 Ollama，**无需 API key**。示例：

  ```dotenv
  LLM_PROVIDER=ollama
  LLM_MODEL=gemma4:12b        # 改为你本地已有的模型名，如 qwen3.5:9b
  LLM_BASE_URL=http://localhost:11434
  ```

  Ollama 走原生 HTTP 适配器（`src/ollama_model.py`），绕开 OpenAI 兼容层的
  `tools: []` 问题，避免 qwen3 等模型返回 502。

> 注意：首次启动会在本地加载 embedding 模型（已缓存到 `~/.cache/huggingface`）。
> 若处于离线/代理环境导致模型拉取失败，可设置 `HF_HUB_OFFLINE=1` 强制使用本地缓存。

## VS Code / PyCharm 直接运行

VS Code 已提供跨平台配置。Code Runner 的 `Run Code` 会通过 `uv` 使用项目环境；若在
“运行和调试”中选择“运行客服助手”，先执行 `Python: Select Interpreter` 并选择项目的
`.venv`。两种入口都不需要填写平台专用的解释器路径。

PyCharm 只需选择项目根目录下的 `.venv` 作为解释器，并新建 Python Module 运行配置：

```text
Module name: src.app
Working directory: 当前项目根目录
```

输入 `exit` 或 `退出` 结束。入口必须以模块形式运行，不要把 `src` 单独设为工作目录。

## 开发验收

开发评测单独建立 Module 运行配置：

```text
Module name: src.evaluation
Working directory: 当前项目根目录
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
