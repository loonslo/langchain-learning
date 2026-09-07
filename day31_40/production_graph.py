"""Day31-Day40 家庭购车决策 Copilot：从需求到受控发布。

这是一个“单文件教学版”。为了让初学者可以顺着一个文件读懂完整运行链路，
原来位于 ``adapters.py``、``car_mcp_server.py`` 和 ``run_online.py`` 的本地代码
已经合并到本文件中。文件底部还提供了 ``run``、``profile``、``car`` 和
``--mcp-server`` 命令入口。

主图故意保留每个生产阶段，而不是把所有逻辑藏进一个 ``agent.invoke``：

    intake -> manage_context -> safety_gate -> route -> plan -> supervisor
       -> specialist(agent-as-tool, fan-out) -> supervisor -> compose_context
       -> generate -> quality_gate -> replan/revise -> approval -> publish

真实 I/O 适配器也在本文件中。默认 ``build_online_services`` 使用真实 DeepSeek、
Tavily、只读 SQLite 和 MCP；测试通过依赖注入替换外部系统。

注意：这里的“单文件”指项目自己的 Python 源码合并为一个文件。第三方库和
运行时数据库仍然是外部依赖，这是正常的 Python 项目边界，不能通过复制代码消除。
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import json
import operator
import os
import re
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Callable, Literal, Protocol, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, Send, interrupt
from pydantic import BaseModel, Field

load_dotenv()
# 项目根目录；用于定位共享配置或其他项目级资源。
ROOT = Path(__file__).resolve().parents[1]
# 本日示例的本地数据目录；在线服务默认从这里读取 SQLite 数据库。
DATA_DIR = Path(__file__).resolve().parent / "data"
# Graph 内部统一使用的证据来源枚举，同时也是适配器字典的键类型。
Source = Literal["web", "sql", "mcp"]


# 1. 契约：模型输出只要会控制代码，就必须是结构化字段（Day32）
class RouteDecision(BaseModel):
    """路由节点的结构化输出。

    这些字段会被后续 Python 代码直接读取，所以不能只返回一段自然语言。
    Pydantic 会在模型输出不符合约束时抛错，避免把模糊文本当成程序控制信号。
    """

    # 请求的业务意图，决定后续是否需要取证以及允许使用哪些能力。
    intent: Literal["public_info", "family_data", "calculation", "chitchat"]

    # 路由允许访问的数据源；这里只是模型建议，plan 还会再次做白名单过滤。
    sources: list[Source] = Field(default_factory=list)

    # 是否属于家庭购车 Copilot 的业务范围。
    in_scope: bool = True

    # 继续执行所必需、但当前请求没有提供的信息。非空时进入 clarify，不调用外部工具。
    missing_information: list[str] = Field(default_factory=list)

    # 是否涉及发布报告等需要人工确认的动作；普通分析、下单和付款不在本程序范围内。
    requires_approval: bool = False

    # 给审计日志和调试使用的路由理由，不作为 Python 分支条件。
    reason: str


class WorkItem(BaseModel):
    """一个可以交给某个专家适配器执行的任务。"""

    # 请求内稳定的任务 ID；进入 GraphState 后会加上 request_id 前缀，避免跨请求碰撞。
    id: str

    # 任务要使用的证据来源，同时也是适配器路由键。
    source: Source

    # 发给对应 specialist/adapter 的最小任务指令。
    instruction: str

    # 执行批次。同组任务可并行，后续组可以读取前序组的精简证据。
    parallel_group: int = Field(ge=0, description="同组并行，不同组顺序执行")


class Plan(BaseModel):
    """计划节点的整体输出。"""

    # 当前请求的可执行任务清单；plan 节点会根据路由允许的数据源再次过滤。
    items: list[WorkItem]


class QualityDecision(BaseModel):
    """质量门禁的结构化决定。"""

    # pass=通过，revise=只改写，replan=补证据，human_review=必须人工判断。
    action: Literal["pass", "revise", "replan", "human_review"]

    # 0 到 100 的质量分，仅用于门禁和审计，不直接等同于购车推荐置信度。
    score: int = Field(ge=0, le=100)

    # 给 generate/replan 节点使用的可执行审核意见。
    feedback: str


class Evidence(TypedDict, total=False):
    """不同来源统一使用的证据格式。

    Web、SQL 和 MCP 的原始返回格式各不相同，先转换成这个格式，后面的
    ``compose_context`` 和 ``generate`` 就可以用同一套逻辑处理它们。
    """

    # 产生这条证据的请求 ID，用于并行任务和多轮 checkpoint 中的请求级隔离。
    request_id: str

    # 证据来源类型；决定展示标签和审计时的可信度边界。
    source: Source

    # 面向模型和日志的人类可读标题。
    title: str

    # 已截断或格式化的证据正文，不应被当作未核验的额外事实继续扩写。
    content: str

    # 可追溯来源，例如 HTTP(S) URL、SQL 查询引用或 MCP URI。
    reference: str

    # 降级、空结果或其他可信度限制。存在时报告必须向用户披露。
    warning: str


class TraceEvent(TypedDict):
    """一条可观测性事件，只保存摘要和耗时。"""

    # 产生事件的 Graph 节点名称，与 add_node 注册名保持一致。
    node: str

    # 脱敏后的简短摘要；不要在这里写入密钥、完整提示词或未经处理的 PII。
    detail: str

    # 节点本次执行耗时，单位为毫秒。
    duration_ms: int

    # 事件发生时的 Unix wall-clock 时间戳，单位为毫秒。
    at_ms: int


class GraphState(TypedDict, total=False):
    """整张 LangGraph 共享的状态。

    这是节点之间传递的状态契约，而不是要求每个节点返回全部字段。由于使用
    ``total=False``，节点可以返回 partial update；实际必填字段由流程阶段和
    ``initial_state``/``next_turn_input`` 保证。读取可能尚未产生的字段时应使用
    ``state.get``，只有已经由前置节点保证的字段才直接使用 ``state[...]``。

    ``Annotated[list, operator.add]`` 是 LangGraph 的 reducer 声明：当多个
    并行 specialist 返回 ``evidence``、``errors`` 或 ``trace`` 时，框架把列表
    追加合并，而不是让后一个结果覆盖前一个结果。
    """

    # 租户隔离标识，用于 thread 校验、权限边界和审计关联。
    tenant_id: str

    # 当前请求的全链路 ID；证据和 trace 用它区分同一 thread 中的不同轮次。
    request_id: str

    # 幂等键；publish 成功后写入 published_keys，防止重试重复发布副作用。
    idempotency_key: str

    # 已经消费过的幂等键。该列表应随 checkpoint/持久化状态保留，不能每轮清空。
    published_keys: Annotated[list[str], operator.add]

    # intake 根据 idempotency_key 是否已存在于 published_keys 计算出的重复请求标志。
    duplicate_request: bool

    # 用户原始问题，经 intake 规范化空白后保留在状态中。
    question: str

    # 经过手机号、邮箱等 PII 脱敏并通过安全检查的问题，供模型和外部工具使用。
    sanitized_question: str

    # 完整对话历史，作为可审计记录保留；publish 时追加当前问答。
    conversation_history: Annotated[list[dict[str, str]], operator.add]

    # 给模型看的近期历史窗口；由 manage_context 从完整历史派生，当前实现保留最近四轮。
    recent_history: list[dict[str, str]]

    # 较旧历史的压缩摘要，用于在不扩大上下文窗口的情况下保留长期约束和决定。
    history_summary: str

    # 已被摘要覆盖的历史条目数量，避免同一段旧历史在每轮重复摘要。
    history_summarized_count: int

    # 确定性安全门结果；为 True 时跳过 route 和所有外部服务调用。
    blocked: bool

    # 安全检查产生的风险标签，例如 pii_redacted、prompt_injection。
    risk_flags: list[str]

    # RouteDecision.model_dump() 的持久化结果；由 route 写入，after_route/plan 读取。
    route: dict

    # WorkItem.model_dump() 后的可执行任务清单，供 supervisor/dispatch/specialist 使用。
    work_items: list[dict]

    # 已完成或已失败的任务 ID；并行 specialist 返回时追加，帮助 supervisor 收敛。
    completed_items: Annotated[list[str], operator.add]

    # Supervisor 已经运行的轮数，用于限制动态 fan-out 和反思循环。
    supervisor_steps: int

    # Supervisor 最大轮数；超过后停止继续委派并记录错误。
    max_supervisor_steps: int

    # 当前请求允许完成的 specialist/tool 任务数量上限。
    max_tool_calls: int

    # 当前请求收集到的异构证据；并行 specialist 返回时追加合并。
    evidence: Annotated[list[Evidence], operator.add]

    # compose_context 生成的编号证据上下文，格式供草稿引用和质量审校使用。
    context: str

    # 当前生成阶段的答案草稿；revise/replan 可能触发后续重新生成。
    draft: str

    # QualityDecision.model_dump() 的结果，记录动作、分数和反馈。
    quality: dict

    # 已执行的草稿修订次数。
    revision_count: int

    # 允许的最大修订次数，达到上限后不再自动 revise。
    max_revisions: int

    # 已执行的补证据/重新规划次数。
    replan_count: int

    # 允许的最大重新规划次数，达到上限后转人工审批路径。
    max_replans: int

    # 当前发布控制状态：无需审批、等待审批、已批准或已拒绝。
    approval_status: Literal["not_required", "pending", "approved", "rejected"]

    # publish 节点最终返回给调用方的文本；拒绝发布时也会写入可解释的结束语。
    final_answer: str

    # 节点错误摘要；并行 specialist 失败时追加，不能用异常直接覆盖其他错误。
    errors: Annotated[list[str], operator.add]

    # 节点级审计轨迹；并行节点追加合并，内容应保持脱敏且长度受控。
    trace: Annotated[list[TraceEvent], operator.add]


# -----------------------------------------------------------------------------
# 一、外部系统适配器
# -----------------------------------------------------------------------------
#
# 初学者可以先记住一个原则：Graph 负责“先做什么、后做什么”，适配器负责
# “具体怎样访问 Web、数据库或 MCP”。这样做的好处是：
#
# 1. Graph 不需要知道 Tavily、SQLite、MCP SDK 的细节；
# 2. 测试时可以注入一个很小的 fake adapter，不消耗真实 API；
# 3. 某一个外部服务故障时，可以只替换这一层，而不用重写整张图。
#
# 下面这些类原来在 adapters.py 中。现在把它们放到主文件中，方便单文件阅读。


class TransientToolError(RuntimeError):
    """临时性工具错误，例如网络抖动、429 或短暂超时。

    这类错误通常值得重试。与之相对的永久错误见 ``PermanentToolError``。
    """


class PermanentToolError(RuntimeError):
    """重试也不会成功的工具错误，例如参数不合法、权限不足或 SQL 不安全。"""


class EvidenceAdapter(Protocol):
    """所有证据来源都遵守的最小接口。

    Graph 只调用 ``collect``，并不关心实现类背后是 HTTP、SQLite 还是 MCP。
    """

    def collect(self, instruction: str) -> list[Evidence]: ...


def call_with_timeout(fn: Callable[[], list[Evidence]], seconds: float) -> list[Evidence]:
    """运行一个同步工具，并在指定秒数后停止等待。

    有些第三方 SDK 没有统一的 timeout 参数，因此这里用线程池加一层通用护栏。
    注意：线程超时只能让当前 Graph 不再继续等待，不能强行杀掉已经发出的网络请求；
    生产环境仍然应该优先配置 SDK 自己的连接超时和读取超时。
    """

    # max_workers=1 表示这一次 collect 只启动一个后台工作线程。
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = pool.submit(fn)
    try:
        return future.result(timeout=seconds)
    except concurrent.futures.TimeoutError as exc:
        future.cancel()
        raise TransientToolError(f"工具超过 {seconds}s 未返回") from exc
    finally:
        # 不等待已经超时的任务，避免阻塞主图；cancel_futures 尽量取消尚未开始的任务。
        pool.shutdown(wait=False, cancel_futures=True)


@dataclass
class ResilientAdapter:
    """为任意证据适配器增加“超时 → 重试 → 降级”能力。

    ``inner`` 是真实工具，``fallback`` 是最终降级工具。降级结果必须明确带有
    warning，不能把“没有查到”伪装成真实业务数据。
    """

    # 主适配器；只有临时性错误才会进入重试流程。
    inner: EvidenceAdapter

    # 所有重试都失败后的降级适配器，返回结果必须带 warning。
    fallback: EvidenceAdapter

    # 单次主适配器调用允许等待的最长时间。
    timeout_seconds: float = 10.0

    # 包含第一次调用在内的最大尝试次数。
    max_attempts: int = 3

    # 指数退避的初始秒数；第 n 次重试等待 base * 2**n。
    base_delay_seconds: float = 0.05

    def collect(self, instruction: str) -> list[Evidence]:
        last_error: Exception | None = None

        # 例如 max_attempts=3 时，最多尝试第 1、2、3 次。
        for attempt in range(1, self.max_attempts + 1):
            try:
                return call_with_timeout(
                    lambda: self.inner.collect(instruction), self.timeout_seconds
                )
            except (TransientToolError, TimeoutError, ConnectionError) as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    # 退避时间依次为 base、2*base、4*base，避免故障时瞬间打满服务。
                    time.sleep(self.base_delay_seconds * (2 ** (attempt - 1)))
            except PermanentToolError:
                # 安全、权限、参数错误不重试，直接交给上层处理。
                raise

        # 所有尝试均失败后返回诚实的降级结果。
        fallback = self.fallback.collect(instruction)
        for item in fallback:
            item["warning"] = f"主工具重试耗尽，已降级：{type(last_error).__name__}"
        return fallback


class TavilySearchAdapter:
    """使用 Tavily 搜索公开资料，并保留标题、摘要和 URL。"""

    def __init__(self, api_key: str | None = None, max_results: int = 3) -> None:
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.max_results = max_results

    def collect(self, instruction: str) -> list[Evidence]:
        if not self.api_key:
            raise PermanentToolError("缺少 TAVILY_API_KEY")

        try:
            # 延迟导入：只运行 fake/SQL 分支时，即使未安装 Tavily 也能导入本文件。
            from tavily import TavilyClient

            response = TavilyClient(api_key=self.api_key).search(
                instruction, max_results=self.max_results, timeout=8
            )
        except ImportError as exc:
            raise PermanentToolError("缺少 tavily-python") from exc
        except Exception as exc:
            # Tavily SDK 的具体异常类型可能随版本变化，统一归类为临时工具错误。
            raise TransientToolError("Tavily 搜索失败") from exc

        return [
            {
                "source": "web",
                "title": str(row.get("title", "搜索结果")),
                # 限制单条证据长度，避免搜索摘要挤满上下文窗口。
                "content": str(row.get("content", ""))[:1200],
                "reference": str(row.get("url", "")),
            }
            for row in response.get("results", [])
        ]


# Text2SQL 只允许访问下列两张业务表。这个集合是确定性的安全边界，不交给模型。
SQL_DANGEROUS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "attach",
    "detach",
    "pragma",
    "vacuum",
    "reindex",
    "trigger",
}


def validate_readonly_sql(
    sql: str, allowed_tables: set[str], max_limit: int = 100
) -> str:
    """在执行模型生成的 SQL 之前，做一次确定性的只读校验。

    校验顺序体现了纵深防御：

    - 只接受 SELECT 或只读 CTE；
    - 只允许一条语句，禁止注释；
    - 禁止常见写操作和数据库管理关键字；
    - FROM/JOIN 的表必须在白名单中；
    - 强制 LIMIT，避免一次查询返回无限数据。
    """

    compact = " ".join(sql.strip().split())
    lowered = compact.lower()
    if not lowered.startswith(("select ", "with ")):
        raise PermanentToolError("只允许 SELECT/只读 CTE")
    if ";" in compact.rstrip(";") or "--" in compact or "/*" in compact:
        raise PermanentToolError("只允许单条且不带注释的 SQL")

    tokens = set(re.findall(r"\b[a-z_]+\b", lowered))
    dangerous = tokens & SQL_DANGEROUS
    if dangerous:
        raise PermanentToolError(f"SQL 含危险关键字：{sorted(dangerous)}")

    # 找出 FROM/JOIN 后的表名。别名形式的 CTE 会在下一步从真实表集合中排除。
    table_matches = re.findall(
        r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", lowered
    )
    cte_aliases = set(
        re.findall(r"(?:\bwith\b|,)\s*([a-zA-Z_]\w*)\s+as\s*\(", lowered)
    )
    tables = {name for name in table_matches if name not in cte_aliases}
    if not tables or not tables <= allowed_tables:
        raise PermanentToolError(f"SQL 表不在白名单：{sorted(tables - allowed_tables)}")

    limit = re.search(r"\blimit\s+(\d+)", lowered)
    if not limit:
        compact = f"{compact.rstrip(';')} LIMIT {max_limit}"
    elif int(limit.group(1)) > max_limit:
        compact = re.sub(
            r"\blimit\s+\d+", f"LIMIT {max_limit}", compact, flags=re.I
        )
    return compact


def init_car_database(path: Path) -> None:
    """创建数据库表结构，但不写入任何家庭或车型样例数据。

    这个函数可以安全地重复调用，因为使用了 ``IF NOT EXISTS``。数据库中的真实
    记录应由用户通过 ``profile``/``car`` 命令录入，或由自己的业务系统写入。
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS family_driving_profile (
                profile_id INTEGER PRIMARY KEY,
                family_name TEXT NOT NULL,
                purchase_budget_yuan REAL NOT NULL,
                available_cash_yuan REAL NOT NULL,
                monthly_payment_limit_yuan REAL NOT NULL,
                annual_mileage_km REAL NOT NULL,
                daily_commute_km REAL NOT NULL,
                passengers INTEGER NOT NULL,
                home_charger_available INTEGER NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(family_name)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate_cars (
                car_id INTEGER PRIMARY KEY,
                candidate_name TEXT NOT NULL,
                powertrain TEXT NOT NULL,
                guide_price_yuan REAL NOT NULL,
                energy_use_per_100km REAL NOT NULL,
                energy_unit TEXT NOT NULL,
                insurance_per_year_yuan REAL NOT NULL,
                maintenance_per_year_yuan REAL NOT NULL,
                resale_value_after_5y_yuan REAL NOT NULL,
                source_url TEXT NOT NULL,
                verified_at TEXT NOT NULL,
                UNIQUE(candidate_name)
            )
            """
        )


def upsert_family_profile(path: Path, values: dict[str, Any]) -> None:
    """保存或更新用户真实提供的家庭用车画像。

    ``?`` 占位符让 SQLite 负责绑定参数，避免把用户输入直接拼到 SQL 中。
    """

    init_car_database(path)
    columns = (
        "family_name",
        "purchase_budget_yuan",
        "available_cash_yuan",
        "monthly_payment_limit_yuan",
        "annual_mileage_km",
        "daily_commute_km",
        "passengers",
        "home_charger_available",
        "updated_at",
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"""
            INSERT INTO family_driving_profile ({', '.join(columns)})
            VALUES ({', '.join('?' for _ in columns)})
            ON CONFLICT(family_name) DO UPDATE SET
                purchase_budget_yuan=excluded.purchase_budget_yuan,
                available_cash_yuan=excluded.available_cash_yuan,
                monthly_payment_limit_yuan=excluded.monthly_payment_limit_yuan,
                annual_mileage_km=excluded.annual_mileage_km,
                daily_commute_km=excluded.daily_commute_km,
                passengers=excluded.passengers,
                home_charger_available=excluded.home_charger_available,
                updated_at=excluded.updated_at
            """,
            tuple(values[column] for column in columns),
        )


def upsert_candidate_car(path: Path, values: dict[str, Any]) -> None:
    """保存或更新一条已经带来源 URL、并经过人工核验的候选车型。"""

    init_car_database(path)
    columns = (
        "candidate_name",
        "powertrain",
        "guide_price_yuan",
        "energy_use_per_100km",
        "energy_unit",
        "insurance_per_year_yuan",
        "maintenance_per_year_yuan",
        "resale_value_after_5y_yuan",
        "source_url",
        "verified_at",
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"""
            INSERT INTO candidate_cars ({', '.join(columns)})
            VALUES ({', '.join('?' for _ in columns)})
            ON CONFLICT(candidate_name) DO UPDATE SET
                powertrain=excluded.powertrain,
                guide_price_yuan=excluded.guide_price_yuan,
                energy_use_per_100km=excluded.energy_use_per_100km,
                energy_unit=excluded.energy_unit,
                insurance_per_year_yuan=excluded.insurance_per_year_yuan,
                maintenance_per_year_yuan=excluded.maintenance_per_year_yuan,
                resale_value_after_5y_yuan=excluded.resale_value_after_5y_yuan,
                source_url=excluded.source_url,
                verified_at=excluded.verified_at
            """,
            tuple(values[column] for column in columns),
        )


class SqlGenerator(Protocol):
    """Text2SQL 模型所需的最小接口。"""

    def generate_sql(self, question: str, schema: str) -> str: ...


class SafeSqlAdapter:
    """生成 SQL → 确定性校验 → SQLite 只读连接 → 返回 rows 证据。"""

    # 只有这两张表可以暴露给模型生成 SQL。
    allowed_tables = {"family_driving_profile", "candidate_cars"}
    schema = (
        "family_driving_profile(family_name TEXT, purchase_budget_yuan REAL, "
        "available_cash_yuan REAL, monthly_payment_limit_yuan REAL, annual_mileage_km REAL, "
        "daily_commute_km REAL, passengers INTEGER, home_charger_available INTEGER, updated_at TEXT); "
        "candidate_cars(candidate_name TEXT, powertrain TEXT, guide_price_yuan REAL, "
        "energy_use_per_100km REAL, energy_unit TEXT, insurance_per_year_yuan REAL, "
        "maintenance_per_year_yuan REAL, resale_value_after_5y_yuan REAL, "
        "source_url TEXT, verified_at TEXT)"
    )

    def __init__(self, db_path: Path, generator: SqlGenerator) -> None:
        self.db_path = db_path.resolve()
        self.generator = generator

    def collect(self, instruction: str) -> list[Evidence]:
        # 先让模型提出 SQL，再把结果交给确定性安全门；模型本身不是安全边界。
        sql = validate_readonly_sql(
            self.generator.generate_sql(instruction, self.schema), self.allowed_tables
        )

        # mode=ro 防止这个查询连接在数据库不存在时偷偷创建数据库。
        uri = f"file:{self.db_path.as_posix()}?mode=ro"
        try:
            with sqlite3.connect(uri, uri=True, timeout=3) as conn:
                conn.row_factory = sqlite3.Row
                # 即使后面的代码出现疏漏，SQLite 连接层也拒绝写操作。
                conn.execute("PRAGMA query_only = ON")
                rows = [dict(row) for row in conn.execute(sql).fetchall()]
        except sqlite3.Error as exc:
            raise PermanentToolError("只读 SQL 执行失败") from exc

        evidence: Evidence = {
            "source": "sql",
            "title": "家庭画像与候选车只读查询结果",
            "content": json.dumps(rows, ensure_ascii=False),
            "reference": f"sql://car-decision?query={sql}",
        }
        if not rows:
            # 空结果也是有意义的证据：它说明系统没有找到已录入记录。
            evidence["warning"] = "查询未返回已核验记录；报告不得自行补全数字"
        return [evidence]


class MultiServerMcpAdapter:
    """连接一个或多个 MCP Server，并把 Tools/Resources/Prompts 变成证据。

    MCP 内部的 Tool 会交给一个独立的小 Agent 使用；主 Graph 只接收最终摘要，
    这就是 ``agent-as-tool``。服务器地址、鉴权信息等配置留在适配器层，不进入 Graph State。
    """

    def __init__(
        self,
        connections: dict[str, dict[str, Any]],
        *,
        resource_requests: list[tuple[str, str]] | None = None,
        prompt_requests: list[tuple[str, str, dict[str, str]]] | None = None,
    ) -> None:
        # MCP Server 连接配置；包含命令、URL、transport 和鉴权信息，只存在适配器层。
        self.connections = connections

        # 要读取的只读 Resource，元素为 (server_name, uri)。
        self.resource_requests = resource_requests or []

        # 要调用的服务端 Prompt，元素为 (server_name, prompt_name, arguments)。
        self.prompt_requests = prompt_requests or []

    async def _collect(self, instruction: str) -> list[Evidence]:
        try:
            from langchain.agents import create_agent
            from langchain_mcp_adapters.client import MultiServerMCPClient
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise PermanentToolError("缺少 mcp/langchain-mcp-adapters") from exc

        client = MultiServerMCPClient(self.connections)
        evidence: list[Evidence] = []

        # Tools：小 Agent 只拿到当前任务，不拿主 Graph 的完整状态。
        tools = await client.get_tools()
        if tools:
            llm = ChatOpenAI(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                temperature=0,
            )
            agent = create_agent(llm, tools)
            result = await agent.ainvoke({"messages": [("user", instruction)]})
            evidence.append(
                {
                    "source": "mcp",
                    "title": "MCP Tool/Agent 返回",
                    "content": str(result["messages"][-1].content),
                    "reference": "mcp://tools",
                }
            )

        # Resources：服务器提供的只读规则/配置。
        for server, uri in self.resource_requests:
            blobs = await client.get_resources(server, uris=uri)
            evidence.extend(
                {
                    "source": "mcp",
                    "title": f"MCP Resource {uri}",
                    "content": blob.as_string(),
                    "reference": uri,
                }
                for blob in blobs
            )

        # Prompts：服务器端维护的团队级任务模板。
        for server, name, arguments in self.prompt_requests:
            messages = await client.get_prompt(server, name, arguments=arguments)
            evidence.append(
                {
                    "source": "mcp",
                    "title": f"MCP Prompt {name}",
                    "content": "\n".join(str(message.content) for message in messages),
                    "reference": f"mcp://{server}/prompts/{name}",
                }
            )
        return evidence

    def collect(self, instruction: str) -> list[Evidence]:
        # 普通同步 Graph 可以用 asyncio.run；如果当前线程已经在事件循环中，
        # 应改用异步 Graph（agraph）或异步适配器，不能嵌套 asyncio.run。
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            try:
                return asyncio.run(self._collect(instruction))
            except PermanentToolError:
                raise
            except Exception as exc:
                raise TransientToolError("MCP 调用失败") from exc
        raise PermanentToolError(
            "同步 Graph 不能嵌套在事件循环中；Web 服务请使用异步适配器/agraph"
        )


class UnavailableAdapter:
    """诚实降级：数据源不可用时说明原因，不伪造结果。"""

    def __init__(self, source: Source) -> None:
        self.source = source

    def collect(self, instruction: str) -> list[Evidence]:
        return [
            {
                "source": self.source,
                "title": f"{self.source} 暂不可用",
                "content": f"未取得真实数据，不能据此下结论。原任务：{instruction}",
                "reference": f"unavailable://{self.source}",
                "warning": "degraded",
            }
        ]


# -----------------------------------------------------------------------------
# 二、MCP 计算工具
# -----------------------------------------------------------------------------
#
# 这些函数只做确定性数学运算，不做购买、贷款、付款等决定。它们原来位于
# car_mcp_server.py。函数本身不依赖 MCP SDK，因此初学者可以直接调用和测试；
# ``_run_mcp_server`` 会在需要时把它们注册成 MCP Tools。


def calculate_monthly_payment(
    vehicle_price_yuan: float,
    down_payment_yuan: float,
    annual_rate_percent: float,
    months: int,
) -> float:
    """按等额本息估算贷款月供；金额单位为元，年利率用百分数表示。"""

    principal = vehicle_price_yuan - down_payment_yuan
    if principal < 0 or months <= 0 or annual_rate_percent < 0:
        raise ValueError("价格、首付、利率或期数不合法")
    monthly_rate = annual_rate_percent / 100 / 12
    if monthly_rate == 0:
        return round(principal / months, 2)
    factor = (1 + monthly_rate) ** months
    return round(principal * monthly_rate * factor / (factor - 1), 2)


def calculate_annual_energy_cost(
    annual_mileage_km: float,
    energy_use_per_100km: float,
    energy_price_yuan: float,
) -> float:
    """估算一年油费或电费；单价是每升或每千瓦时价格。"""

    if min(annual_mileage_km, energy_use_per_100km, energy_price_yuan) < 0:
        raise ValueError("里程、能耗和能源单价不能为负数")
    return round(
        annual_mileage_km / 100 * energy_use_per_100km * energy_price_yuan, 2
    )


def calculate_five_year_tco(
    vehicle_price_yuan: float,
    annual_energy_cost_yuan: float,
    annual_insurance_yuan: float,
    annual_maintenance_yuan: float,
    resale_value_after_5y_yuan: float,
) -> float:
    """估算五年总持有成本：车价 + 五年使用成本 - 五年后残值。"""

    values = [
        vehicle_price_yuan,
        annual_energy_cost_yuan,
        annual_insurance_yuan,
        annual_maintenance_yuan,
        resale_value_after_5y_yuan,
    ]
    if min(values) < 0:
        raise ValueError("成本参数不能为负数")
    return round(
        vehicle_price_yuan
        + 5 * (annual_energy_cost_yuan + annual_insurance_yuan + annual_maintenance_yuan)
        - resale_value_after_5y_yuan,
        2,
    )


def calculate_budget_ratio(
    monthly_payment_yuan: float, monthly_budget_yuan: float
) -> float:
    """计算月供占家庭月供上限的百分比，用于识别预算压力。"""

    if monthly_payment_yuan < 0 or monthly_budget_yuan <= 0:
        raise ValueError("月供不能为负数，月度上限必须大于 0")
    return round(monthly_payment_yuan / monthly_budget_yuan * 100, 2)


def secure_ping() -> str:
    """验证 MCP 子进程收到的 DEMO_TOKEN 是否正确。"""

    if os.getenv("DEMO_TOKEN", "") != "secret-123":
        raise ValueError("未授权：DEMO_TOKEN 无效或缺失")
    return "pong（购车计算服务鉴权通过）"


def _run_mcp_server() -> None:
    """以 stdio 方式启动内嵌的 MCP Server。

    MCP 客户端会把本文件作为子进程重新启动，并传入 ``--mcp-server``。把
    ``mcp`` 相关导入放在函数内，可以让只学习 Graph/SQLite 的读者不必在导入
    主模块时立即初始化 MCP SDK。
    """

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("请安装 mcp 才能启动内嵌 MCP Server") from exc

    server = FastMCP("CarDecisionCalculator")

    # 把上面的纯 Python 函数注册为 MCP Tools。
    server.tool()(calculate_monthly_payment)
    server.tool()(calculate_annual_energy_cost)
    server.tool()(calculate_five_year_tco)
    server.tool()(calculate_budget_ratio)
    server.tool()(secure_ping)

    @server.resource("config://car-decision-rules")
    def car_decision_rules() -> str:
        """提供报告边界和成本口径等只读规则。"""

        return (
            "购车建议必须区分实时公开资料、家庭内部数据和估算结果；"
            "价格与政策注明查询时间；不得自动下单、申请贷款或付款。"
        )

    @server.prompt()
    def car_purchase_analysis(text: str) -> str:
        """提供服务器端维护的、可审计的成本分析任务模板。"""

        return (
            f"家庭购车任务：{text}\n"
            "先确认家庭里程、预算和候选车参数，再调用工具计算月供、年度能源费、"
            "五年总持有成本及预算占比；缺少参数时明确列出假设，不得伪造。"
        )

    # stdio 协议使用标准输入/输出通信，因此这里不要额外 print 日志。
    server.run(transport="stdio")


class ModelGateway(Protocol):
    """模型层的最小协议。

    ``DeepSeekGateway`` 是线上实现；测试可以提供同样方法名的 FakeModel。协议
    只约定接口，不负责真正发请求，这就是依赖倒置。
    """

    def route(self, question: str, history_view: str) -> RouteDecision: ...
    def plan(self, question: str, decision: RouteDecision) -> list[WorkItem]: ...
    def replan(self, question: str, feedback: str, next_group: int) -> list[WorkItem]: ...
    def generate(self, question: str, history_view: str, context: str, feedback: str) -> str: ...
    def review(self, question: str, context: str, draft: str) -> QualityDecision: ...
    def summarize_history(self, old_history: list[dict[str, str]], existing: str) -> str: ...
    def generate_sql(self, question: str, schema: str) -> str: ...


class DeepSeekGateway:
    """所有真实模型调用集中在这里，便于换模型、统计成本和做契约测试。

    这里使用 ``ChatOpenAI`` 的 OpenAI-compatible 接口连接 DeepSeek。路由、计划、
    SQL、草稿、审校和历史摘要都集中在同一个 gateway，Graph 节点因此不需要
    直接处理 API Key 或 SDK 细节。
    """

    def __init__(self) -> None:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("在线模式必须设置 DEEPSEEK_API_KEY")
        self.llm = ChatOpenAI(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"), api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            temperature=0, timeout=float(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
            max_retries=0,
        )

    def structured(self, schema: type[BaseModel], system: str, user: str):
        """调用模型，并把文本解析成指定的 Pydantic 对象。"""

        parser = PydanticOutputParser(pydantic_object=schema)
        raw = self.llm.invoke([
            SystemMessage(content=f"{system}\n\n{parser.get_format_instructions()}"),
            HumanMessage(content=user),
        ])
        return parser.parse(str(raw.content))

    def route(self, question: str, history_view: str) -> RouteDecision:
        """判断请求是否在业务范围内，以及需要哪些数据源。"""

        return self.structured(
            RouteDecision,
            "你是家庭购车决策 Copilot 的路由器。public_info 用 web 查询实时车型、价格口径、"
            "安全、质保与补能资料；family_data 用 sql 查询用户录入的家庭画像和已核验候选车数据；"
            "calculation 用 mcp 计算月供、能源费、五年总持有成本和预算占比；"
            "chitchat 可直接回答，sources 可多选。生成普通建议不代表下单；"
            "非购车问题设置 in_scope=false；如果当前请求缺少继续执行所必需的信息，"
            "把字段名写入 missing_information，不能自行假设；"
            "只有用户要求发布报告或执行申请、下单、贷款、付款时 requires_approval=true。",
            f"近期对话：{history_view or '无'}\n当前问题：{question}",
        )

    def plan(self, question: str, decision: RouteDecision) -> list[WorkItem]:
        """把一次请求拆成可并行或可顺序执行的任务清单。"""

        result: Plan = self.structured(
            Plan,
            "制定家庭购车取证计划。web 查带时间和 URL 的公开资料，sql 查家庭画像/候选车，"
            "mcp 只做确定性成本计算。每个 source 至少一个任务；公开资料与家庭数据可同组并行，"
            "依赖这些参数的成本计算放后续组。id 使用 task-1、task-2，不得越权增加数据源。",
            f"问题：{question}\n路由：{decision.model_dump_json()}",
        )
        allowed = set(decision.sources)
        return [item for item in result.items if item.source in allowed]

    def replan(self, question: str, feedback: str, next_group: int) -> list[WorkItem]:
        """质量门禁认为证据不足时，只补充少量新任务。"""

        result: Plan = self.structured(
            Plan,
            "购车报告审核认为证据不足。只补充 1-2 个公开资料或家庭数据任务，"
            "id 以 replan- 开头；缺计算参数时先补参数，禁止凭空估算。",
            f"问题：{question}\n审核反馈：{feedback}\nparallel_group 从 {next_group} 开始",
        )
        return [item.model_copy(update={"parallel_group": max(item.parallel_group, next_group)})
                for item in result.items]

    def generate(self, question: str, history_view: str, context: str, feedback: str) -> str:
        """根据问题、历史视图、统一证据和上轮反馈生成草稿。"""

        return str(self.llm.invoke([
            SystemMessage(content=(
                "你是证据驱动的家庭购车决策助理。报告按家庭需求、候选方案、成本对比、"
                "推荐与不推荐理由、风险和下一步核验来写。只能把给定证据当事实；"
                "关键事实和数字必须标 [1][2]；区分实时公开资料、用户录入数据与计算假设；"
                "证据不足明确说不知道。你只能给决策建议，不得声称已下单、申请贷款或付款。"
            )),
            HumanMessage(content=(
                f"近期对话：{history_view or '无'}\n问题：{question}\n\n"
                f"统一证据：\n{context or '无外部证据'}\n\n上一轮反馈：{feedback or '无，生成第一稿'}"
            )),
        ]).content)

    def review(self, question: str, context: str, draft: str) -> QualityDecision:
        """让独立审校模型判断草稿应通过、改写、补证据还是转人工。"""

        return self.structured(
            QualityDecision,
            "你是家庭购车报告的独立质量审校 Agent。检查预算、通勤、乘员、充电条件是否被考虑，"
            "月供/能源费/五年总成本是否有证据或计算依据，实时价格是否披露时间性，"
            "引用编号是否存在，不确定性是否披露。表达问题选 revise；缺证据选 replan；"
            "边界判断或临界分数选 human_review；全部合格才 pass。",
            f"问题：{question}\n证据：{context or '无'}\n草稿：{draft}",
        )

    def summarize_history(self, old_history: list[dict[str, str]], existing: str) -> str:
        """压缩较旧对话，但保留身份、决定、约束和未完成事项。"""

        return str(self.llm.invoke(
            "用中文更新对话摘要，务必保留身份、编号、决定、约束和未完成事项。"
            f"\n已有摘要：{existing or '无'}\n新增旧历史：{json.dumps(old_history, ensure_ascii=False)}"
        ).content)

    def generate_sql(self, question: str, schema: str) -> str:
        """根据固定 schema 生成候选 SQL；真正执行前仍要过安全校验。"""

        class SqlProposal(BaseModel):
            sql: str
        result: SqlProposal = self.structured(
            SqlProposal,
            "你是 Text2SQL 生成器。只生成单条 SELECT，只查询给定 schema，必须带 LIMIT <= 100。",
            f"schema：{schema}\n问题：{question}",
        )
        return result.sql


@dataclass
class ProductionServices:
    """Graph 所需的外部能力集合。

    把 model 和 adapters 放进一个对象后，``build_graph`` 就能接收 fake 实现，
    既方便单元测试，也方便初学者先用固定返回值理解图的控制流。
    """

    # 负责路由、计划、生成、审校和历史摘要的模型网关。
    model: ModelGateway

    # 按 Source 分派证据任务的适配器；每个适配器可自行封装超时、重试和降级。
    adapters: dict[Source, EvidenceAdapter]


def build_online_services() -> ProductionServices:
    """组装在线版服务：真实 LLM、Tavily、SQLite 和内嵌 MCP Server。

    这里是“依赖注入”的组合根（composition root）：前面的 Graph 不需要自己
    创建 SDK 客户端，只接收这里组装好的 ``ProductionServices``。
    """

    model = DeepSeekGateway()
    db_path = Path(os.getenv("DAY31_40_DB", str(DATA_DIR / "car_decision.db")))
    init_car_database(db_path)

    # Web 搜索：真实服务失败时，最多重试 3 次，再返回带 warning 的降级证据。
    search = ResilientAdapter(
        TavilySearchAdapter(), UnavailableAdapter("web"),
        timeout_seconds=float(os.getenv("SEARCH_TIMEOUT_SECONDS", "10")), max_attempts=3,
    )

    # SQL：真实服务失败时降级；SafeSqlAdapter 自己还会做只读校验。
    sql = ResilientAdapter(
        SafeSqlAdapter(db_path, model), UnavailableAdapter("sql"), timeout_seconds=8, max_attempts=2,
    )

    # 本地 MCP Server 使用同一个文件启动，只多传一个 --mcp-server 参数。
    # 因此 car_mcp_server.py 不再是主 Graph 的源码依赖。
    connections: dict[str, dict] = {
        "car_calculator": {
            "command": sys.executable,
            "args": [str(Path(__file__).resolve()), "--mcp-server"],
            "transport": "stdio",
            "env": {**os.environ, "DEMO_TOKEN": os.getenv("DEMO_TOKEN", "secret-123"),
                    "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        }
    }
    if os.getenv("MCP_CAR_REMOTE_URL"):
        connections["car_remote"] = {
            "url": os.environ["MCP_CAR_REMOTE_URL"], "transport": "streamable_http",
            "headers": {"Authorization": f"Bearer {os.getenv('MCP_AUTH_TOKEN', '')}"},
        }
    mcp = ResilientAdapter(
        MultiServerMcpAdapter(
            connections,
            resource_requests=[("car_calculator", "config://car-decision-rules")],
            prompt_requests=[("car_calculator", "car_purchase_analysis",
                              {"text": "基于家庭数据完成可审计的购车成本比较"})],
        ), UnavailableAdapter("mcp"), timeout_seconds=25, max_attempts=2,
    )
    return ProductionServices(model=model, adapters={"web": search, "sql": sql, "mcp": mcp})


# -----------------------------------------------------------------------------
# 三、确定性生产护栏：不把安全边界交给模型
# -----------------------------------------------------------------------------
INJECTION_PATTERNS = [
    r"ignore (all|previous) instructions", r"忽略(以上|之前|系统)指令",
    r"输出.*(system prompt|系统提示词)", r"泄露.*(密钥|token|api.?key)",
]


def sanitize_and_check(question: str) -> tuple[str, list[str], bool]:
    """在任何 LLM 调用之前做输入脱敏和提示注入检查。

    返回值依次是：脱敏后的问题、风险标签、是否应该拦截。把这一步放在
    ``route`` 之前，意味着可疑文本还没有机会影响路由模型或外部工具。
    """

    flags: list[str] = []
    sanitized = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "[PHONE]", question)
    sanitized = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", sanitized)
    if sanitized != question:
        flags.append("pii_redacted")
    if any(re.search(pattern, sanitized, re.I) for pattern in INJECTION_PATTERNS):
        flags.append("prompt_injection")
    return sanitized, flags, "prompt_injection" in flags


def _event(node: str, detail: str, started: float) -> list[TraceEvent]:
    """生成统一格式的节点轨迹。

    ``started`` 用 ``perf_counter`` 计算耗时，时间戳则用 wall-clock 时间，
    这样既适合测时，也方便把事件和外部日志对齐。
    """

    return [{"node": node, "detail": detail,
             "duration_ms": round((time.perf_counter() - started) * 1000),
             "at_ms": int(time.time() * 1000)}]


def _history_view(state: GraphState) -> str:
    """只给模型看“摘要 + 最近四轮”，但不丢失完整审计历史。"""

    return json.dumps({"summary": state.get("history_summary", ""),
                       "recent": state.get("recent_history", [])}, ensure_ascii=False)


def retry_transient_llm_error(exc: Exception) -> bool:
    """429、连接和超时值得重试；401、格式错误和安全拒绝必须快速失败。"""
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    try:
        from openai import APIConnectionError, APITimeoutError, RateLimitError
        return isinstance(exc, (APIConnectionError, APITimeoutError, RateLimitError))
    except ImportError:
        return False


# -----------------------------------------------------------------------------
# 四、构图：每个节点只做一件可测试的事
# -----------------------------------------------------------------------------
#
# 读图方式建议：先看下面每个节点的输入和输出，再看最后的 add_edge。
# 节点是“动作”，边是“控制流”，GraphState 是它们之间传递的共享白板。
def build_graph(services: ProductionServices | None = None, checkpointer=None):
    """创建并编译完整生产图。

    ``services`` 为空时使用真实在线服务；传入时则使用调用者提供的服务，
    例如测试中的 FakeModel 和内存 Adapter。``checkpointer`` 用来保存暂停点，
    让人工审批或下一轮对话可以从同一个 thread 恢复。
    """

    services = services or build_online_services()

    def intake(state: GraphState) -> dict:
        """入口校验：清理问题、检查租户，并准备请求级幂等键。"""

        started = time.perf_counter()
        question = " ".join(state.get("question", "").split())
        if not question or len(question) > 2000:
            raise ValueError("问题不能为空且不能超过 2000 字")
        tenant = state.get("tenant_id", "").strip()
        if not tenant:
            raise ValueError("必须提供 tenant_id，thread_id 也必须包含租户边界")
        key = state.get("idempotency_key") or state.get("request_id") or str(uuid.uuid4())
        duplicate = key in state.get("published_keys", [])
        return {"question": question, "request_id": state.get("request_id") or str(uuid.uuid4()),
                "idempotency_key": key, "duplicate_request": duplicate,
                "trace": _event("intake", f"tenant={tenant}, duplicate={duplicate}", started)}

    def manage_context(state: GraphState) -> dict:
        """管理多轮上下文：完整历史留在 state，旧历史只摘要一次。"""

        started = time.perf_counter()
        history = state.get("conversation_history", [])
        already = state.get("history_summarized_count", 0)
        cutoff = max(0, len(history) - 4)
        old, recent = history[already:cutoff], history[-4:]
        summary = state.get("history_summary", "")
        if old:
            summary = services.model.summarize_history(old, summary)
        return {"recent_history": recent, "history_summary": summary,
                "history_summarized_count": cutoff,
                "trace": _event("manage_context", f"完整 {len(history)} 轮，模型视图 {len(recent)} 轮", started)}

    def safety_gate(state: GraphState) -> dict:
        """调用确定性安全函数，决定是否拦截当前请求。"""

        started = time.perf_counter()
        sanitized, flags, blocked = sanitize_and_check(state["question"])
        return {"sanitized_question": sanitized, "risk_flags": flags, "blocked": blocked,
                "trace": _event("safety_gate", f"blocked={blocked}, flags={flags}", started)}

    def after_safety(state: GraphState) -> str:
        """安全门后的分支：风险请求和重复请求都不再访问外部服务。"""

        return "blocked" if state.get("blocked") or state.get("duplicate_request") else "route"

    def blocked_answer(state: GraphState) -> dict:
        """为被拦截或重复的请求生成可解释的结束语。"""

        started = time.perf_counter()
        answer = ("该请求包含提示注入或索取敏感配置的内容，已拒绝执行。" if state.get("blocked")
                  else "相同幂等键已经处理，本次不会重复执行或发布。")
        return {"draft": answer, "approval_status": "not_required",
                "trace": _event("blocked_answer", answer, started)}

    def route(state: GraphState) -> dict:
        """让模型输出结构化路由，而不是让 Python 用关键词猜意图。"""

        started = time.perf_counter()
        decision = services.model.route(state["sanitized_question"], _history_view(state))
        return {"route": decision.model_dump(),
                "approval_status": "pending" if decision.requires_approval else "not_required",
                "trace": _event("route", f"intent={decision.intent}, sources={decision.sources}", started)}

    def plan(state: GraphState) -> dict:
        """把路由结果转换成带稳定 ID 的可执行任务。"""

        started = time.perf_counter()
        decision = RouteDecision.model_validate(state["route"])
        items = services.model.plan(state["sanitized_question"], decision)
        prefix = state["request_id"][:8]
        seen: set[str] = set()
        unique = []
        for item in items:
            stable_id = f"{prefix}:{item.id}"
            if stable_id not in seen:
                seen.add(stable_id)
                unique.append(item.model_copy(update={"id": stable_id}))
        return {"work_items": [item.model_dump() for item in unique],
                "trace": _event("plan", f"生成 {len(unique)} 个任务", started)}

    def after_route(state: GraphState) -> str:
        """路由结果的确定性分支：越界、缺信息或进入计划执行。"""

        decision = RouteDecision.model_validate(state["route"])
        if not decision.in_scope:
            return "out_of_scope"
        if decision.missing_information:
            return "clarify"
        return "plan"

    def clarify(state: GraphState) -> dict:
        """信息不足时只追问必要字段，不启动任何外部工具。"""

        started = time.perf_counter()
        missing = RouteDecision.model_validate(state["route"]).missing_information
        draft = "继续购车分析前，请补充：" + "、".join(missing) + "。"
        return {"draft": draft, "approval_status": "not_required",
                "trace": _event("clarify", f"缺少 {len(missing)} 项必要信息", started)}

    def out_of_scope(state: GraphState) -> dict:
        """业务边界外的问题直接说明能力范围。"""

        started = time.perf_counter()
        draft = "当前 Copilot 只处理家庭购车调查、比较和成本测算问题。"
        return {"draft": draft, "approval_status": "not_required",
                "trace": _event("out_of_scope", "非购车请求", started)}

    def supervisor(state: GraphState) -> dict:
        """主管节点：检查任务完成情况和工具预算。"""

        started = time.perf_counter()
        step = state.get("supervisor_steps", 0) + 1
        work_ids = {x["id"] for x in state.get("work_items", [])}
        completed = set(state.get("completed_items", [])) & work_ids
        pending = [x for x in state.get("work_items", []) if x["id"] not in completed]
        budget_hit = step > state.get("max_supervisor_steps", 12) or len(completed) >= state.get("max_tool_calls", 8)
        updates: dict = {"supervisor_steps": step,
                         "trace": _event("supervisor", "预算护栏触发" if budget_hit else f"待执行 {len(pending)} 项", started)}
        if budget_hit:
            updates["errors"] = ["Supervisor/工具调用预算耗尽，停止继续委派"]
        return updates

    def dispatch(state: GraphState):
        """根据最小 parallel_group 动态 fan-out 专家任务。

        返回字符串表示全部完成；返回 ``Send`` 列表表示同组任务并行执行。
        ``Send`` 中只放当前任务和必要的前序证据，避免把完整主状态泄露给子 Agent。
        """

        work_ids = {x["id"] for x in state.get("work_items", [])}
        completed = set(state.get("completed_items", [])) & work_ids
        pending = [WorkItem.model_validate(x) for x in state.get("work_items", []) if x["id"] not in completed]
        budget_hit = (state.get("supervisor_steps", 0) > state.get("max_supervisor_steps", 12)
                      or len(completed) >= state.get("max_tool_calls", 8))
        if not pending or budget_hit:
            return "compose_context"
        group = min(item.parallel_group for item in pending)
        batch = [item for item in pending if item.parallel_group == group]
        remaining = max(0, state.get("max_tool_calls", 8) - len(completed))
        # 后续组只收到本次请求已取得的精简证据，不暴露租户、历史、审批等完整主 State。
        prerequisites = [
            f"({entry['source']}) {entry['title']}: {entry['content'][:800]}"
            for entry in state.get("evidence", [])
            if entry.get("request_id") == state["request_id"]
        ]
        dependency_context = "\n".join(prerequisites) if group > 0 else ""
        return [Send("specialist", {"item": item.model_dump(), "request_id": state["request_id"],
                                    "dependency_context": dependency_context})
                for item in batch[:remaining]]

    def specialist(worker_state: dict) -> dict:
        """执行一个专家任务。

        每个子 Agent 只有 instruction 和必要的依赖证据，上下文隔离；无论成功还是
        失败都标记 completed_items，让主管可以收敛，错误则通过 errors 回喂主图。
        """

        started = time.perf_counter()
        item = WorkItem.model_validate(worker_state["item"])
        try:
            instruction = item.instruction
            if worker_state.get("dependency_context"):
                instruction += ("\n\n仅可使用以下前序证据中的参数完成当前任务；缺参数要明确返回缺失项：\n"
                                + worker_state["dependency_context"])
            evidence = services.adapters[item.source].collect(instruction)
            evidence = [{**entry, "request_id": worker_state["request_id"]} for entry in evidence]
            return {"evidence": evidence, "completed_items": [item.id],
                    "trace": _event("specialist", f"{item.id}/{item.source} 返回 {len(evidence)} 条", started)}
        except Exception as exc:
            return {"completed_items": [item.id],
                    "errors": [f"{item.id}/{item.source}: {type(exc).__name__}"],
                    "trace": _event("specialist", f"{item.id}/{item.source} 失败并回喂主管", started)}

    def compose_context(state: GraphState) -> dict:
        """把 Web/SQL/MCP 的异构结果统一编号，供草稿引用。"""

        started = time.perf_counter()
        blocks = []
        current = [item for item in state.get("evidence", [])
                   if item.get("request_id") == state["request_id"]]
        for index, item in enumerate(current, 1):
            warning = f"\n警告：{item['warning']}" if item.get("warning") else ""
            blocks.append(f"[{index}] ({item['source']}) {item['title']}\n{item['content']}"
                          f"\n来源：{item['reference']}{warning}")
        return {"context": "\n\n".join(blocks),
                "trace": _event("compose_context", f"汇聚 {len(blocks)} 条证据", started)}

    def generate(state: GraphState) -> dict:
        """使用统一证据和最近反馈生成一版草稿。"""

        started = time.perf_counter()
        feedback = state.get("quality", {}).get("feedback", "")
        draft = services.model.generate(state["sanitized_question"], _history_view(state),
                                        state.get("context", ""), feedback)
        return {"draft": draft, "trace": _event("generate", f"生成 {len(draft)} 字草稿", started)}

    def quality_gate(state: GraphState) -> dict:
        """独立审校草稿，并执行一个不依赖模型的引用兜底检查。"""

        started = time.perf_counter()
        decision = services.model.review(state["sanitized_question"], state.get("context", ""), state["draft"])
        # 独立确定性校验：有证据却完全没有 [n] 引用时，不能只相信 Judge 模型说通过。
        if state.get("context") and not re.search(r"\[\d+\]", state["draft"]):
            decision = QualityDecision(
                action="revise", score=min(decision.score, 60),
                feedback="草稿使用了外部证据但没有 [n] 引用，请补齐可追溯引用。",
            )
        return {"quality": decision.model_dump(),
                "trace": _event("quality_gate", f"action={decision.action}, score={decision.score}", started)}

    def after_quality(state: GraphState) -> str:
        """质量结果决定：补证据、只改写，或进入审批。"""

        action = state["quality"]["action"]
        if action == "replan" and state.get("replan_count", 0) < state.get("max_replans", 1):
            return "replan"
        if action == "revise" and state.get("revision_count", 0) < state.get("max_revisions", 2):
            return "revise"
        return "approval"

    def replan(state: GraphState) -> dict:
        """补充一轮有限的新任务，避免反思循环无限扩大。"""

        started = time.perf_counter()
        next_group = 1 + max((x.get("parallel_group", 0) for x in state.get("work_items", [])), default=0)
        extra = services.model.replan(state["sanitized_question"], state["quality"]["feedback"], next_group)
        prefix = state["request_id"][:8]
        extra = [x.model_copy(update={"id": f"{prefix}:{x.id}"}) for x in extra]
        known_ids = {x["id"] for x in state.get("work_items", [])}
        extra = [x for x in extra if x.id not in known_ids]
        return {"work_items": state.get("work_items", []) + [x.model_dump() for x in extra],
                "replan_count": state.get("replan_count", 0) + 1,
                "trace": _event("replan", f"补充 {len(extra)} 个任务", started)}

    def revise(state: GraphState) -> dict:
        """记录一次改写次数；下一条边会回到 generate。"""

        started = time.perf_counter()
        count = state.get("revision_count", 0) + 1
        return {"revision_count": count, "trace": _event("revise", f"第 {count} 次修订", started)}

    def approval(state: GraphState) -> dict:
        """必要时暂停图，等待家庭成员通过 checkpoint 恢复。

        ``interrupt`` 不会忙等，它会把 payload 保存到 checkpoint，并把控制权交给
        调用方。调用方稍后用 ``Command(resume='approve'/'reject')`` 继续。
        """

        started = time.perf_counter()
        # 修订/补证据达到上限仍未 pass 时必须转人工，绝不能自动发布低质量结果。
        forced = state.get("quality", {}).get("action") != "pass"
        if state.get("approval_status") == "not_required" and not forced:
            return {"trace": _event("approval", "低风险且质量通过，自动放行", started)}
        decision = interrupt({"tenant_id": state["tenant_id"], "request_id": state["request_id"],
                              "draft": state["draft"], "quality": state.get("quality", {}),
                              "risk_flags": state.get("risk_flags", []),
                              "ask": "批准采用并发布这份购车建议报告？回复 approve 或 reject。"
                                     "该操作不会下单、贷款或付款。"})
        approved = str(decision).lower() == "approve"
        return {"approval_status": "approved" if approved else "rejected",
                "trace": _event("approval", "人工批准" if approved else "人工拒绝", started)}

    def publish(state: GraphState) -> dict:
        """最终发布：写入对话历史，并记录已经消费过的幂等键。"""

        started = time.perf_counter()
        rejected = state.get("approval_status") == "rejected"
        final = "（家庭成员拒绝，本次购车建议报告未发布）" if rejected else state["draft"]
        keys = [] if rejected or state.get("duplicate_request") else [state["idempotency_key"]]
        return {"final_answer": final,
                "conversation_history": [{"question": state["sanitized_question"], "answer": final}],
                "published_keys": keys,
                "trace": _event("publish", "拒绝发布" if rejected else "完成幂等发布", started)}

    # StateGraph 读取 GraphState 的字段定义，知道哪些字段需要 reducer 合并。
    graph = StateGraph(GraphState)

    # 只给可能遇到网络/限流问题的模型节点配置重试；安全判断和纯本地逻辑不重试。
    retry = RetryPolicy(max_attempts=3, retry_on=retry_transient_llm_error)

    # 注册节点：节点名就是后面连边时使用的字符串。
    graph.add_node("intake", intake)
    graph.add_node("manage_context", manage_context, retry_policy=retry)
    graph.add_node("safety_gate", safety_gate)
    graph.add_node("blocked_answer", blocked_answer)
    graph.add_node("route", route, retry_policy=retry)
    graph.add_node("clarify", clarify)
    graph.add_node("out_of_scope", out_of_scope)
    graph.add_node("plan", plan, retry_policy=retry)
    graph.add_node("supervisor", supervisor)
    graph.add_node("specialist", specialist)
    graph.add_node("compose_context", compose_context)
    graph.add_node("generate", generate, retry_policy=retry)
    graph.add_node("quality_gate", quality_gate, retry_policy=retry)
    graph.add_node("replan", replan, retry_policy=retry)
    graph.add_node("revise", revise)
    graph.add_node("approval", approval)
    graph.add_node("publish", publish)
    # 连接固定边。
    graph.add_edge(START, "intake")
    graph.add_edge("intake", "manage_context")
    graph.add_edge("manage_context", "safety_gate")
    # 条件边由函数返回值决定。例如 after_safety 返回 blocked，就走 blocked_answer。
    graph.add_conditional_edges("safety_gate", after_safety, {"blocked": "blocked_answer", "route": "route"})
    graph.add_edge("blocked_answer", "publish")
    graph.add_conditional_edges("route", after_route,
                                {"clarify": "clarify", "out_of_scope": "out_of_scope", "plan": "plan"})
    graph.add_edge("clarify", "publish")
    graph.add_edge("out_of_scope", "publish")
    graph.add_edge("plan", "supervisor")
    # dispatch 既可能返回 compose_context，也可能返回多个 Send("specialist", ...)。
    # 多个 Send 会并行运行，随后由 GraphState 中的 operator.add reducer 汇总。
    graph.add_conditional_edges("supervisor", dispatch, ["specialist", "compose_context"])
    graph.add_edge("specialist", "supervisor")
    graph.add_edge("compose_context", "generate")
    graph.add_edge("generate", "quality_gate")
    graph.add_conditional_edges("quality_gate", after_quality,
                                {"replan": "replan", "revise": "revise", "approval": "approval"})
    graph.add_edge("replan", "supervisor")
    graph.add_edge("revise", "generate")
    graph.add_edge("approval", "publish")
    graph.add_edge("publish", END)
    # 没有显式传入 checkpointer 时使用内存版本，适合教学和单次运行。
    # 需要跨进程/重启恢复时，请在调用方传入 open_checkpointer("sqlite") 或生产 Saver。
    return graph.compile(checkpointer=checkpointer or InMemorySaver())


def initial_state(question: str, *, tenant_id: str = "family-user",
                  idempotency_key: str | None = None, max_revisions: int = 2) -> GraphState:
    """创建第一轮对话的完整初始状态。

    显式填充空列表很重要：并行 reducer 需要列表作为初始值，后续 specialist
    才能把自己的结果追加进去。
    """

    return {
        "tenant_id": tenant_id, "request_id": str(uuid.uuid4()),
        "idempotency_key": idempotency_key or str(uuid.uuid4()), "question": question,
        "published_keys": [], "conversation_history": [], "completed_items": [], "evidence": [],
        "errors": [], "trace": [], "history_summary": "", "history_summarized_count": 0,
        "recent_history": [], "blocked": False,
        "risk_flags": [], "route": {}, "work_items": [], "supervisor_steps": 0,
        "max_supervisor_steps": 12, "max_tool_calls": 8, "context": "", "draft": "",
        "quality": {}, "revision_count": 0, "max_revisions": max_revisions,
        "replan_count": 0, "max_replans": 1, "approval_status": "not_required",
        "final_answer": "", "duplicate_request": False,
    }


def next_turn_input(question: str, *, tenant_id: str,
                    idempotency_key: str | None = None) -> GraphState:
    """构造同一 thread 的后续轮次输入。

    请求级字段会重置；``conversation_history``、摘要和已发布幂等键留给 checkpoint
    合并保留。这样既能继续聊天，又不会把上一轮的草稿误当成当前草稿。
    """
    return {
        "tenant_id": tenant_id, "request_id": str(uuid.uuid4()),
        "idempotency_key": idempotency_key or str(uuid.uuid4()), "question": question,
        "duplicate_request": False, "blocked": False, "risk_flags": [], "route": {},
        "work_items": [], "supervisor_steps": 0, "context": "", "draft": "", "quality": {},
        "revision_count": 0, "replan_count": 0, "approval_status": "not_required",
        "final_answer": "",
    }


@contextmanager
def open_checkpointer(kind: str = "memory", location: str = "day31_40/checkpoints.sqlite"):
    """打开状态保存器。

    ``memory`` 只在当前 Python 进程有效；``sqlite`` 可以在进程重启后恢复。
    多实例部署时，应由调用方注入合适的 PostgresSaver，而不是让多个实例共享
    一个本地 SQLite 文件。
    """
    if kind == "memory":
        yield InMemorySaver()
        return
    if kind == "sqlite":
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
        except ImportError as exc:
            raise RuntimeError("请安装 langgraph-checkpoint-sqlite") from exc
        path = Path(location)
        path.parent.mkdir(parents=True, exist_ok=True)
        with SqliteSaver.from_conn_string(str(path)) as saver:
            yield saver
        return
    raise ValueError("仅支持 memory/sqlite；多实例生产请注入 PostgresSaver")


def resume(app, config: dict, decision: Literal["approve", "reject"]) -> dict:
    """从 approval interrupt 恢复图的快捷函数。"""

    return app.invoke(Command(resume=decision), config)


# -----------------------------------------------------------------------------
# 五、在线运行、真实数据录入和命令行入口
# -----------------------------------------------------------------------------
#
# 原来的 run_online.py / configure_real_data.py 也合并到这里。
#
# 最简单的阅读/运行顺序：
#
# 1. 先用 FakeModel + fake adapter 调用 build_graph，理解图的控制流；
# 2. 配置 DEEPSEEK_API_KEY 和 TAVILY_API_KEY；
# 3. 用 profile/car 子命令写入自己的真实数据；
# 4. 用 run 子命令启动线上 Graph。
#
# 注意：在线模式会产生真实模型和搜索费用。数据库初始化只建表，不会自动填充
# 家庭或车型数据；缺少数据时，结果必须明确披露“没有已核验记录”。


def _safe_json(value: Any) -> str:
    """把流式事件转换为有限长度 JSON，避免日志无限增长。

    这里使用 ``default=str`` 兼容 LangGraph 的少量特殊对象；截断的是日志副本，
    不会改变 Graph checkpoint 中的真实 state。
    """

    text = json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= 4000 else text[:4000] + "…[truncated]"


def run_online(
    question: str,
    *,
    tenant_id: str,
    thread_id: str,
    stream_mode: str = "updates",
    checkpoint_kind: str = "memory",
    checkpoint_path: str = "day31_40/checkpoints.sqlite",
    trace_path: str = "reports/day31_40_online_trace.jsonl",
) -> dict:
    """运行一次线上 Graph，并在需要时交互式等待人工审批。

    ``thread_id`` 必须以 ``<tenant_id>:`` 开头。这个简单的命名约定不是完整的
    鉴权系统，但能防止调用方误把不同租户的 checkpoint 混在一起。
    """

    if not thread_id.startswith(f"{tenant_id}:"):
        raise ValueError("thread_id 必须以 '<tenant_id>:' 开头，防止跨租户串状态")

    # build_online_services 会在缺少 DEEPSEEK_API_KEY 时明确报错，不会偷偷切换 fake 模式。
    services = build_online_services()
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 40}
    trace = Path(trace_path)
    trace.parent.mkdir(parents=True, exist_ok=True)

    with open_checkpointer(checkpoint_kind, checkpoint_path) as saver:
        app = build_graph(services, checkpointer=saver)

        # JSONL 一行一个 Graph 事件，适合用文本工具追踪长流程。
        with trace.open("w", encoding="utf-8") as output:
            for chunk in app.stream(
                initial_state(question, tenant_id=tenant_id),
                config,
                stream_mode=stream_mode,
            ):
                line = _safe_json(chunk)
                output.write(line + "\n")
                print(line)

        # interrupt 后，checkpoint 仍然有 next 节点；没有 interrupt 时直接返回最终 state。
        state = app.get_state(config)
        if state.next:
            interrupts = state.interrupts
            if interrupts:
                payload = interrupts[0].value
                print("\n=== 图已暂停，等待人工审批 ===")
                print(
                    _safe_json(
                        {
                            "request_id": payload.get("request_id"),
                            "quality": payload.get("quality"),
                            "draft": payload.get("draft"),
                        }
                    )
                )
                while True:
                    decision = input("approve / reject > ").strip().lower()
                    if decision in {"approve", "reject"}:
                        break
                return resume(app, config, decision)
        return dict(state.values)


def _default_database_path() -> Path:
    """返回与在线 Graph 相同的默认数据库路径。"""

    return Path(os.getenv("DAY31_40_DB", str(DATA_DIR / "car_decision.db")))


def _run_cli(args: argparse.Namespace) -> None:
    """执行命令行解析后的动作。单独抽出便于阅读和测试。"""

    if args.command == "run":
        final = run_online(
            args.question,
            tenant_id=args.tenant,
            thread_id=args.thread,
            stream_mode=args.stream_mode,
            checkpoint_kind=args.checkpoint,
            checkpoint_path=args.checkpoint_path,
            trace_path=args.trace_path,
        )
        print("\n=== 最终答案 ===\n" + final.get("final_answer", ""))
        return

    db_path = args.db
    init_car_database(db_path)
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    if args.command == "profile":
        upsert_family_profile(
            db_path,
            {
                "family_name": args.family_name,
                "purchase_budget_yuan": args.purchase_budget,
                "available_cash_yuan": args.available_cash,
                "monthly_payment_limit_yuan": args.monthly_payment_limit,
                "annual_mileage_km": args.annual_mileage,
                "daily_commute_km": args.daily_commute,
                "passengers": args.passengers,
                "home_charger_available": int(args.home_charger == "yes"),
                "updated_at": now,
            },
        )
    elif args.command == "car":
        if not args.source_url.startswith(("https://", "http://")):
            raise ValueError("--source-url 必须是可追溯的 HTTP(S) URL")
        upsert_candidate_car(
            db_path,
            {
                "candidate_name": args.name,
                "powertrain": args.powertrain,
                "guide_price_yuan": args.price,
                "energy_use_per_100km": args.energy_use,
                "energy_unit": args.energy_unit,
                "insurance_per_year_yuan": args.insurance,
                "maintenance_per_year_yuan": args.maintenance,
                "resale_value_after_5y_yuan": args.resale_value_5y,
                "source_url": args.source_url,
                "verified_at": args.verified_at or now,
            },
        )
    else:
        raise ValueError(f"未知命令：{args.command}")

    print(f"已写入真实数据：{db_path.resolve()}")


def main() -> None:
    """命令行入口。

    ``--mcp-server`` 是给 MCP 客户端调用的内部模式；普通用户常用的是三个
    子命令：``profile`` 录入家庭画像、``car`` 录入候选车、``run`` 运行 Graph。
    """

    # MCP 子进程只传这个 flag，不需要解析其他参数。
    if "--mcp-server" in sys.argv[1:]:
        _run_mcp_server()
        return

    parser = argparse.ArgumentParser(
        description="Day31-Day40 家庭购车决策 Copilot（单文件版）"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=_default_database_path(),
        help="真实家庭/车型数据使用的 SQLite 文件",
    )
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="运行一次线上购车分析")
    run.add_argument("question", help="要分析的购车问题")
    run.add_argument("--tenant", default="family-user")
    run.add_argument("--thread", default="family-user:car-decision")
    run.add_argument(
        "--stream-mode",
        choices=["updates", "values", "messages", "debug"],
        default="updates",
    )
    run.add_argument("--checkpoint", choices=["memory", "sqlite"], default="memory")
    run.add_argument("--checkpoint-path", default="day31_40/checkpoints.sqlite")
    run.add_argument("--trace-path", default="reports/day31_40_online_trace.jsonl")

    profile = subparsers.add_parser("profile", help="录入或更新真实家庭用车画像")
    profile.add_argument("--family-name", required=True)
    profile.add_argument("--purchase-budget", type=float, required=True)
    profile.add_argument("--available-cash", type=float, required=True)
    profile.add_argument("--monthly-payment-limit", type=float, required=True)
    profile.add_argument("--annual-mileage", type=float, required=True)
    profile.add_argument("--daily-commute", type=float, required=True)
    profile.add_argument("--passengers", type=int, required=True)
    profile.add_argument("--home-charger", choices=["yes", "no"], required=True)

    car = subparsers.add_parser("car", help="录入或更新已核验的真实候选车型")
    car.add_argument("--name", required=True)
    car.add_argument("--powertrain", choices=["fuel", "bev", "phev"], required=True)
    car.add_argument("--price", type=float, required=True)
    car.add_argument("--energy-use", type=float, required=True)
    car.add_argument("--energy-unit", choices=["L", "kWh", "L-equivalent"], required=True)
    car.add_argument("--insurance", type=float, required=True)
    car.add_argument("--maintenance", type=float, required=True)
    car.add_argument("--resale-value-5y", type=float, required=True)
    car.add_argument("--source-url", required=True)
    car.add_argument("--verified-at", help="ISO 时间；默认当前本地时间")

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    _run_cli(args)


if __name__ == "__main__":
    main()
