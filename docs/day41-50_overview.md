# Day41–Day50 详细章节概括：从能跑的 Agent 到可部署、可测试、可选型的系统

这一组的主线是：把前面的 RAG/Agent 做成 HTTP 服务，补齐超时、重试、成本、缓存、数据库、容器和安全，再回到测试优势，用 pytest 自动回归，最后了解 LoRA 以及 Prompt/RAG/微调的选型。

## Day41 · 用 FastAPI 把 RAG 做成 HTTP 服务

代码在：[day41/day41_serve_fastapi.py](../day41/day41_serve_fastapi.py)

Day41 做的事情是：**把只能在命令行运行的 RAG 包成可被前端和其他服务调用的 HTTP API。**

### 1. 不只增加 `/chat`

这一版服务包含：

```text
/chat     → 问答
/feedback → 点赞/点踩
/stats    → 请求数、失败率、成本、p95
/history  → 按用户查历史并分页
/health   → 存活探针，不查依赖
/ready    → 就绪探针，检查依赖
```

这说明服务化不等于把命令行 `input()` 换成一个函数。线上服务还需要状态、成本、反馈、探针和错误边界。

### 2. trace、token、成本要贯穿请求

一次 `/chat` 需要记录：

```text
trace_id
question / answer
latency
token usage
cost
引用来源
成功或失败
```

这些数据后面会被 Day44 的 SQLite 数据层、评测和运营统计使用。

### 3. health 和 ready 的区别

```text
/health → 进程还活着吗？应该快速返回
/ready   → 模型、向量库、数据库等依赖准备好了吗？
```

不能让健康检查每次都做很重的检索，也不能把依赖没有准备好误报成服务健康。

### 4. Day41 最终要记住什么？

> 一个能上生产的 AI API，除了返回答案，还要能查、能统计、能反馈、能判断是否准备好。

## Day42 · 超时、重试和成本统计

代码在：[day42/day42_reliability.py](../day42/day42_reliability.py)

Day42 做的事情是：**给 LLM 调用加可靠性边界，并开始算清每次调用用了多少 token、花了多少钱。**

### 1. 超时防止请求无限等待

```python
llm = get_llm(temperature=0, timeout=20, max_retries=0)
```

没有超时，一次上游卡住可能占住服务线程或协程，最终拖垮整个 API。超时后要返回可识别的失败或降级结果。

### 2. 手写指数退避理解重试原理

```text
第 1 次失败 → 等 1 秒
第 2 次失败 → 等 2 秒
第 3 次失败 → 等 4 秒
```

指数退避给瞬时故障恢复时间，也避免大量请求同时疯狂重试。代码里的手写版本是为了学习，生产版本应使用统一的 retry/fallback 封装。

### 3. 从 usage metadata 统计成本

```python
usage = response.usage_metadata or {}
total_tokens = usage.get("total_tokens")
```

token 数、模型价格和请求次数结合起来，才能知道“这个月为什么费用上涨”。

### 4. Day42 最终要记住什么？

> 重试不是越多越好；要区分瞬时错误和确定性错误，并把超时、token、成本都变成可观测数据。

## Day43 · 缓存和模型路由降低成本

代码在：[day43/day43_cost_cache_routing.py](../day43/day43_cost_cache_routing.py)

Day43 做的事情是：**用缓存避免重复调用，用模型路由把简单问题交给便宜模型。**

### 1. 最小缓存：问题到答案

```python
_CACHE = {}

def ask_with_cache(question: str) -> str:
    key = md5(question.encode("utf-8")).hexdigest()
    if key in _CACHE:
        return _CACHE[key]
    answer = llm.invoke(question).content
    _CACHE[key] = answer
    return answer
```

相同问题命中缓存后，不再调用模型，既省钱又降低延迟。

### 2. model routing

```text
简单问题 → cheap model
复杂问题 → strong model
```

示例代码为了自包含，用同一个模型模拟 cheap/strong；真实系统可以替换为不同价格和能力的模型。

### 3. 缓存不是简单的字典

生产缓存要考虑：

```text
TTL 过期
Prompt 版本
知识库版本
租户隔离
模型版本
```

否则知识更新后仍返回旧答案，或者一个租户命中另一个租户的结果。

### 4. Day43 最终要记住什么？

> 缓存优化“重复调用”，路由优化“每次调用价格”；两者都不能脱离正确性、版本和评测。

## Day44 · 用 SQLite 做业务数据层

代码在：[day44/day44_sqlite_persistence.py](../day44/day44_sqlite_persistence.py)

Day44 做的事情是：**把 LLM 应用的调用结果变成可查询、可分析、可回流的业务日志。**

### 1. 业务日志要记录什么？

```text
谁在什么时候问了什么
用了哪个模型
花了多少 token / 钱
多久返回
是否失败
用户是否点赞/点踩
```

只存问答文本，后面无法做成本核算、延迟分析、失败诊断和评测集回流。

### 2. 代码解决六类生产坑

```text
连接泄漏       → 正确关闭连接
database locked → WAL 和并发处理
全表扫描       → user_id 等字段建索引
表结构不可演进 → schema 版本和迁移
数据不可分析   → 记录 token/cost/latency/error
分页漂移       → 稳定游标分页
```

### 3. SQLite 什么时候够用？

单机服务、内部工具和中小并发可以使用 SQLite；真正的限制不是“永远不能生产”，而是多副本部署时多个进程无法可靠共享同一个文件。

### 4. 和 Day35 checkpoint 的区别

```text
checkpoint → 恢复 Agent 图状态
业务日志   → 成本、失败、反馈、评测和运营查询
```

### 5. Day44 最终要记住什么？

> AI 应用的数据库不只是保存聊天记录，而是线上质量、成本和改进闭环的事实来源。

## Day45 · 用 Docker 打包部署

代码在：[day45/day45_trace_docker.py](../day45/day45_trace_docker.py)

Day45 做的事情是：**把代码、依赖和运行环境封装成可复制的镜像，解决“在我机器上能跑”的问题。**

### 1. Dockerfile 的基本结构

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "...:app", "--host", "0.0.0.0", "--port", "8000"]
```

先复制依赖文件再安装，可以让 Docker 在代码变化但依赖不变时复用缓存层。

### 2. `.dockerignore` 为什么重要？

不把 `.venv`、缓存、日志、密钥和本地向量库盲目复制进镜像，减少镜像体积，也避免把敏感文件打包进去。

### 3. Day45 最终要记住什么？

> Docker 的目标是可复现运行环境；正式交付还要继续考虑非 root、健康检查、密钥注入和正确的启动命令。

## Day46 · 结构化调用日志和 Ollama 本地推理

代码在：[day46/day46_ollama_inference.py](../day46/day46_ollama_inference.py)

Day46 做的事情是：**一边深化可观测性，一边了解怎样把模型从云 API 替换成本地 Ollama。**

### 1. 为每次调用写 JSONL 日志

```python
record = {
    "ts": datetime.now().isoformat(),
    "question": question,
}
record["latency_ms"] = ...
record["tokens"] = ...
record["ok"] = True
```

JSONL 一行一个 JSON 对象，适合追加、检索和被日志系统采集。

### 2. Ollama 解决什么问题？

```text
开源模型 → 本机 Ollama → LangChain ChatOllama → 应用链
```

数据可以留在自己的机器上，不需要每次调用云 API，也没有云端 token 费用；代价是需要本地硬件、模型下载和推理性能管理。

### 3. Day46 最终要记住什么？

> 模型供应商可以替换，但调用契约、延迟、token、错误和质量观测不能消失。

## Day47 · 安全护栏：注入、PII 和密钥

代码在：[day47/day47_security_guardrails.py](../day47/day47_security_guardrails.py)

Day47 做的事情是：**建立 AI 应用的信任边界，防止用户、文档和工具结果借模型权限做出非预期动作。**

### 1. 不可信输入不只有用户

```text
用户输入       → 直接注入
RAG 文档       → 间接注入
网页/搜索结果   → 外部指令注入
工具返回       → 被污染的数据
```

攻击者可以往知识库里放一篇恶意文档，用户什么都没做，模型检索后也可能被诱导。

### 2. 代码演示四类防线

```text
build_messages  → 结构化隔离数据和指令
scan_input      → 检测注入信号并分级
mask_pii        → 脱敏并支持必要时还原
scrub_secrets   → 清理日志中的密钥
```

关键词黑名单只能当告警或弱信号，真正防线是工具白名单、只读权限、高风险动作人工确认和数据/指令分离。

### 3. 脱敏和拦截的方向不同

```text
脱敏 → 宁可多脱，避免漏掉敏感信息
拦截 → 注意误伤，过度拦截会让业务方关闭护栏
```

所以二者不能用同一套“越严格越好”的阈值。

### 4. Day47 最终要记住什么？

> 安全不是给 Prompt 加一句“不要被攻击”，而是建立输入隔离、权限、工具边界、PII 处理和回归测试。

## Day48 · 用 pytest 把 RAG 变成自动回归

代码在：[day48/day48_pytest_regression.py](../day48/day48_pytest_regression.py)

Day48 做的事情是：**把 Day18–Day20 的手动评测变成测试工程师熟悉的 pytest 回归。**

### 1. 用 fixture 复用昂贵资源

```python
@pytest.fixture(scope="session")
def retriever():
    ...
```

整个测试会话只建一次向量库、只加载一次 embedding，避免每个 case 都重复初始化。

### 2. 用参数化把评测集变成测试用例

```python
@pytest.mark.parametrize("case", eval_set, ids=lambda c: c["id"])
def test_rag_case(case, retriever):
    answer = ask(case["question"])
    assert ...
```

每个 case 都有可读 ID，失败时能定位是哪道业务题退化。

### 3. LLM 不适合精确字符串断言

```text
不推荐：assert answer == "标准答案全文"
推荐：   关键词、拒答、引用、同义词和结构性断言
```

模型可能换一种说法但意思正确，所以测试要验证事实和边界，而不是卡死措辞。

### 4. skip 和 fail 要分开

```text
环境未配置 → skip，并说明原因
质量退化   → fail，阻止回归通过
```

CI 可以用 `RAG_TEST_STRICT=1` 把环境缺失也升级为失败，避免所有测试都因为“跳过”而看起来绿色。

### 5. Day48 最终要记住什么？

> 测试背景的优势不是会写 pytest 语法，而是能把 AI 的不稳定输出转成可解释、可持续运行的回归规则。

## Day49 · 真实口径跑一次 LoRA 微调

代码在：[day49/day49_lora_finetune.py](../day49/day49_lora_finetune.py)

Day49 做的事情是：**亲手跑一次 LoRA，理解微调流程，并用生产级回归门禁判断适配器是否真的有价值。**

### 1. LoRA 训练什么？

```text
基座模型参数 → 冻结
旁边的小型低秩矩阵 → 训练
适配器产物 → 通常只有几 MB
```

它用更少显存和时间改变模型的稳定风格或任务行为。

### 2. 生产训练不能只看 train loss

代码特别强调：

```text
只对答案计算 loss
使用 chat template
保留 held-out 验证集
设置合适 LoRA 学习率和 seed
训练后重新加载适配器
```

如果把问题部分也算进 loss，模型可能学会错误的自问自答格式；只看 train loss 下降，也可能只是记住了训练样本。

### 3. 微调后的回归门禁

```text
同一批验证用例
  → 基座模型回答并评分
  → 基座 + LoRA 回答并评分
  → 适配器没有更好 → exit 1，阻止发布
```

这和 Day48 的质量回归、后面 CI 门禁是同一种工程思想。

### 4. Day49 最终要记住什么？

> “微调跑通”不等于“微调有效”。要证明它比基座更好、重载后行为一致，并且没有破坏原有能力。

## Day50 · 选择 Prompt、RAG 还是微调

代码在：[day50/day50_concept_overview.py](../day50/day50_concept_overview.py)

Day50 做的事情是：**把 Prompt、RAG 和微调从“流行技术名词”变成可根据业务约束做出的技术选择。**

### 1. 三种方式分别解决什么？

```text
Prompt → 当前任务、规则、边界和输出格式
RAG    → 推理时注入外部知识、引用和权限过滤
微调   → 稳定改变风格、格式或领域行为
```

Prompt 不能可靠补齐模型不知道的私有知识；微调也不是动态知识库，更不会天然带引用。

### 2. 代码把选择记录成结构化结果

```python
class Strategy(str, Enum):
    PROMPT = "Prompt"
    RAG = "RAG"
    FINE_TUNING = "微调"
    RAG_AND_FINE_TUNING = "RAG + 微调"
```

`Decision` 还记录选择理由和生产检查项，使技术选型可以被评审，而不是只存在于口头经验里。

### 3. 真正的决策输入是什么？

```text
质量、时延、吞吐、权限、知识更新频率、成本、可观测性
```

知识经常变化且需要引用时优先考虑 RAG；行为和格式长期稳定时才考虑微调；简单任务先用 Prompt，避免过早引入复杂度。

### 4. Day50 最终要记住什么？

> Prompt、RAG、微调不是固定的替代关系。先定义可验证的业务目标，再用离线评测和线上观测决定是否增加 RAG 或微调。

## Day41–Day50 总结：这一组到底把什么补齐了？

```text
HTTP 服务
  → 超时 / 重试 / 成本
  → 缓存 / 模型路由
  → SQLite 业务日志
  → Docker
  → 本地推理
  → 安全护栏
  → pytest 回归
  → LoRA 体验
  → 技术选型
```

Day50 结束时，前半段的能力已经从“能调用模型”升级为“能把 AI 应用部署、观测、测试并做技术取舍”。
