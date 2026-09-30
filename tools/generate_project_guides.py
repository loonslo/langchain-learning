"""更新旗舰项目教程的实现参考，保留已编写的正文和学习记录。"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

try:
    from .materialize import snapshot, resolve_index
    from .course_catalog import step_label
except ImportError:
    from materialize import snapshot, resolve_index
    from course_catalog import step_label

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_HEADING = "## 实现与验证参考"
MANUAL_HEADING = "## 项目实现参考"   # 手写参考：内容不是机器生成的，生成器不得覆盖
TICK = chr(96)

META = {
    "m1-rag-mvp/step2": [
        "多文档知识库",
        "单一 FAQ 无法维护多类政策",
        "稳定来源与 chunk_id 是引用、更新和排错的基础",
        "尚未证明检索质量",
    ],
    "m1-rag-mvp/step3": [
        "第一份离线评测集",
        "手工试问无法阻止质量回归",
        "评测集是可执行的产品需求，答案和引用要分开判断",
        "关键词判断不等于完整语义评测",
    ],
    "m1-rag-mvp/step4": [
        "混合检索排序",
        "纯向量检索容易错过精确业务词",
        "语义与关键词排名用 RRF 融合后仍必须回到评测集验证",
        "融合算法不保证所有问题都提升",
    ],
    "m2-session-langgraph/step1": [
        "连续追问与会话隔离",
        "那发票呢无法独立检索",
        "上下文必须有 session 边界和长度上限",
        "短问题规则只是第一版追问识别",
    ],
    "m2-session-langgraph/step2": [
        "LangGraph 显式控制流",
        "校验、检索、拒答和生成分支开始变复杂",
        "只有出现状态与分支时才引入图",
        "用了 LangGraph 不等于自主 Agent",
    ],
    "m3-order-tool-reliability/step1": [
        "受控订单查询工具",
        "知识库不能回答我的订单状态",
        "工具读取业务数据前必须验证资源归属",
        "当前只有只读内存订单仓库",
    ],
    "m3-order-tool-reliability/step2": [
        "工具超时与有限重试",
        "真实上游会出现 503 和永久错误",
        "只对临时、只读失败有限重试",
        "写操作不能直接套用读重试",
    ],
    "m3-order-tool-reliability/step3": [
        "人工升级闭环",
        "只说请转人工并没有完成业务闭环",
        "证据不足要创建可追踪的 open 工单",
        "内存工单尚未幂等持久化",
    ],
    "m3-order-tool-reliability/step4": [
        "SQLite 会话持久化",
        "内存会话在重启后丢失",
        "租户、用户、线程共同构成读取边界",
        "SQLite 只代表本地单实例验证",
    ],
    "m4-api-identity-security/step1": [
        "FastAPI 服务边界",
        "命令行无法被前端或其他服务调用",
        "HTTP 层固定输入输出契约并复用业务入口",
        "API 尚未认证",
    ],
    "m4-api-identity-security/step2": [
        "写操作幂等",
        "客户端重试可能创建重复工单",
        "同一幂等键和请求只能执行一次",
        "内存实现尚未处理多实例并发",
    ],
    "m4-api-identity-security/step3": [
        "可信身份",
        "请求正文自报 user_id 会绕过授权",
        "认证后的 Identity 才能进入业务层",
        "本地共享 secret 不等于企业 SSO",
    ],
    "m4-api-identity-security/step4": [
        "增量知识同步",
        "全量重建昂贵且删除资料会残留",
        "内容哈希决定 upsert、delete 与跳过",
        "执行向量事务和失败恢复仍待实现",
    ],
    "m5-injection-pii-observability/step1": [
        "提示词注入防护",
        "用户和知识文档都可能携带恶意指令",
        "不可信内容要检查、隔离并审计",
        "关键词规则会漏报和误报",
    ],
    "m5-injection-pii-observability/step2": [
        "PII 脱敏",
        "客服问题可能把手机号身份证写入日志",
        "业务原文与日志脱敏副本必须分开",
        "正则无法覆盖所有个人信息",
    ],
    "m5-injection-pii-observability/step3": [
        "可观测性",
        "线上慢或错时没有证据定位",
        "成功失败都要留下不含原始问题的 trace",
        "内存记录器不是生产监控平台",
    ],
    "m5-injection-pii-observability/step4": [
        "安全缓存",
        "重复问答浪费模型调用",
        "缓存键必须包含租户和知识版本且有 TTL",
        "尚未实现多实例和击穿保护",
    ],
    "m6-quality-gate-container/step1": [
        "CI 质量门",
        "评测报告若只供阅读就无法阻止回归",
        "低于阈值或缺失指标都必须失败关闭",
        "门禁只覆盖已有评测集",
    ],
    "m6-quality-gate-container/step2": [
        "容器与启动检查",
        "能在作者机器运行不代表可交付",
        "镜像不带密钥、非 root 运行且启动前检查依赖",
        "尚未发布真实 staging",
    ],
    "m7-capacity-feedback-recovery/step1": [
        "向量库迁移契约",
        "Chroma 不能代表最终共享存储",
        "业务依赖 VectorStore 契约而非具体数据库",
        "schema 存在不等于已完成远端迁移",
    ],
    "m7-capacity-feedback-recovery/step2": [
        "容量与压测判定",
        "单次响应快不能说明容量",
        "p95 与错误率共同定义可接受负载",
        "假样本不代表真实容量",
    ],
    "m7-capacity-feedback-recovery/step3": [
        "用户反馈闭环",
        "bad case 需要进入可审查改进队列",
        "负反馈不能自动改生产 Prompt",
        "反馈可能有偏差且需人工复核",
    ],
    "m7-capacity-feedback-recovery/step4": [
        "模型供应商降级",
        "单一模型故障会中断服务",
        "只对临时错误使用契约一致的 fallback",
        "备用模型质量仍需独立评测",
    ],
    "m7-capacity-feedback-recovery/step5": [
        "备份与恢复验证",
        "有备份文件不代表能恢复",
        "恢复后必须做完整性和业务数据验证",
        "本地 SQLite 演练不等于云数据库灾备",
    ],
    "m7-capacity-feedback-recovery/step6": [
        "统一业务应用",
        "组件存在但没有形成一个请求链路",
        "安全、权限、缓存、工具、工单必须由统一入口编排",
        "仍是本地同步实现",
    ],
    "m8-evidence-final-frontend/step1": [
        "面试证据与项目讲解",
        "功能很多却无法清楚说明问题和证据",
        "简历和面试只陈述仓库可验证的结果",
        "不夸大未做的生产验证",
    ],
    "m8-evidence-final-frontend/step2": [
        "最终验收",
        "毕业不能只看 happy path 演示",
        "任一安全和闭环能力失败都不能验收",
        "本地毕业项目不等于已生产上线",
    ],
}

ROLES = {
    "app.py": "交互式用户入口",
    "assistant.py": "检索、拒答、生成与来源返回",
    "bootstrap.py": "创建真实依赖并接入正式主链",
    "knowledge.py": "摄取结果与检索器的装配点",
    "settings.py": "截至本节的运行路径与环境配置",
    "ingestion.py": "多文档加载和稳定 ID",
    "evaluation.py": "离线用例与分层判断",
    "retrieval.py": "RRF 排名融合",
    "conversation.py": "会话历史与追问改写",
    "workflow.py": "LangGraph 状态和分支",
    "orders.py": "订单归属查询",
    "tool_runner.py": "工具错误分类与重试",
    "tickets.py": "人工工单",
    "thread_store.py": "SQLite 会话",
    "api.py": "HTTP 契约",
    "idempotency.py": "写操作去重",
    "auth.py": "JWT 身份",
    "sync.py": "增量同步计划",
    "security.py": "注入检查",
    "privacy.py": "PII 脱敏",
    "observability.py": "trace 与延迟",
    "cache.py": "租户版本缓存",
    "quality_gate.py": "CI 阈值",
    "readiness.py": "启动检查",
    "vector_store.py": "存储协议",
    "capacity.py": "容量报告",
    "feedback.py": "反馈队列",
    "providers.py": "模型 fallback",
    "backup.py": "备份恢复",
    "application.py": "统一业务编排",
    "runtime.py": "真实依赖与最终 API 组合入口",
    "evidence.py": "证据核验",
    "acceptance.py": "最终验收",
}

CHAINS = {
    "m2-session-langgraph/step1": "app → bootstrap.build_application → SupportApplication → History → "
    "assistant",
    "m2-session-langgraph/step2": "app → bootstrap → SupportApplication → WorkflowAssistant/LangGraph "
    "→ assistant",
    "m3-order-tool-reliability/step1": "app → application.handle → 订单归属查询或 RAG 问答",
    "m3-order-tool-reliability/step2": "application.handle → call_read_only → OrderRepository → "
    "有限重试结果",
    "m3-order-tool-reliability/step3": "application.handle → assistant → escalate → TicketStore",
    "m3-order-tool-reliability/step4": "app/API → application → PersistentHistory → SQLiteThreadStore",
    "m4-api-identity-security/step1": "HTTP /chat → create_app → application.handle → 7.2–7.3 的累积主链",
    "m4-api-identity-security/step2": "Idempotency-Key → API → application → IdempotencyStore → "
    "TicketStore",
    "m4-api-identity-security/step3": "Bearer token → TokenVerifier → Identity → API → application",
    "m4-api-identity-security/step4": "HTTP /knowledge/sync-plan → SyncingApplication → scan/plan → "
    "knowledge_path",
    "m5-injection-pii-observability/step1": "API/CLI → SecuredApplication + 文档过滤 → workflow → "
    "assistant",
    "m5-injection-pii-observability/step2": "用户原文 → PrivacyApplication → 业务链；脱敏副本 → audit_log",
    "m5-injection-pii-observability/step3": "API/CLI → ObservedApplication → 安全/缓存/业务链 → Trace",
    "m5-injection-pii-observability/step4": "API/CLI → ObservedApplication → CachedApplication → 业务链",
    "m6-quality-gate-container/step1": "eval_cases → evaluate → metrics_from_results → "
    "quality_gate.check → 退出码",
    "m6-quality-gate-container/step2": "容器/CLI/API 启动 → bootstrap.build_application → ensure_ready → "
    "构建依赖",
    "m7-capacity-feedback-recovery/step1": "scan/plan → apply_plan → VectorStore.upsert/delete_source",
    "m7-capacity-feedback-recovery/step2": "配置检查 + 压测样本 → release_readiness → 发布判定",
    "m7-capacity-feedback-recovery/step3": "同一 FastAPI → /chat、/knowledge/sync-plan、/feedback → "
    "FeedbackStore",
    "m7-capacity-feedback-recovery/step4": "bootstrap → primary.invoke → 临时错误时 fallback.invoke → "
    "workflow",
    "m7-capacity-feedback-recovery/step5": "正式 thread_db_path → SQLiteThreadStore.backup_to → "
    "integrity_check",
    "m7-capacity-feedback-recovery/step6": "runtime → 认证 API → 同步/反馈/统一 application → 安全、缓存、工具、工单",
    "m8-evidence-final-frontend/step1": "项目陈述 → runtime.verify_project_evidence → 仓库真实文件",
    "m8-evidence-final-frontend/step2": "可执行 checks → run_acceptance → 任一能力失败则最终验收失败",
}


def classify(step: str) -> tuple[list[str], list[str], list[str], list[str]]:
    index = resolve_index("flagship", step)
    previous = snapshot("flagship", index - 1) if index else {}
    current = snapshot("flagship", index)
    modified = sorted(
        p for p in current.keys() & previous.keys() if current[p] != previous[p]
    )
    return (
        sorted(current.keys() - previous.keys()),
        modified,
        sorted(previous.keys() - current.keys()),
        sorted(current.keys() & previous.keys() - set(modified)),
    )


def role(path: str) -> str:
    name = Path(path).name
    if name.startswith("test_"):
        return "保护行为及失败边界的测试"
    if path.startswith("data/"):
        return "知识资料或评测数据"
    return ROLES.get(name, "配置、运行入口或交付证据")


def symbols(step: str, path: str) -> str:
    if not path.endswith(".py"):
        return "核对配置或数据内容"
    source = ROOT / "flagship-project" / step / path
    tree = ast.parse(source.read_text(encoding="utf-8"))
    names = [
        n.name
        for n in tree.body
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    return "、".join(f"{TICK}{n}{TICK}" for n in names) or "模块级配置与数据"


def render(step: str) -> None:
    """仅更新参考附录；正文与已有 workbook 均保留。"""
    if step not in META:
        raise ValueError(f"此步骤没有生成器元数据：{step}")
    title, problem, principle, boundary = META[step]
    folder = ROOT / "flagship-project" / step
    readme = folder / "README.md"
    existing = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if MANUAL_HEADING in existing:
        raise ValueError(f"{step} 的实现参考是手写的，不能自动生成：{MANUAL_HEADING}")
    introduction = existing.split(REFERENCE_HEADING, 1)[0].rstrip()
    if not introduction:
        introduction = f"# {step_label(step)} · {title}\n\n{problem}。本步围绕这个具体问题展开：{principle}。\n\n请先说明已有流程为什么不足，再对照实现观察新能力在哪里进入调用链。{boundary}。"
    added, modified, removed, unchanged = classify(step)
    rows = [
        f"| {TICK}{p}{TICK} | {state} | {role(p)} |"
        for paths, state in [(added, "新增"), (modified, "修改"), (removed, "删除")]
        for p in paths
    ]
    order = [p for p in modified + added if p.startswith(("src/", "tests/"))]
    reading = "\n".join(
        f"{i}. {TICK}{p}{TICK}：{symbols(step, p)}。" for i, p in enumerate(order, 1)
    )
    reference = f"""

{REFERENCE_HEADING}

快照包含此前步骤的累积实现；本步骤目录只保存变更集。

| 文件 | 变更 | 职责 |
|---|---|---|
{chr(10).join(rows)}

调用过程：{CHAINS[step]}。另有 {len(unchanged)} 个继承文件未修改，完整差异可用 --diff 查看。

### 阅读实现

{reading}

### 还原与累计验证

{TICK * 3}powershell
$python = (Resolve-Path .venv/Scripts/python.exe).Path
& $python tools/materialize.py flagship {step}
cd .build/flagship/{step}/customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
& $python -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
{TICK * 3}

这是离线测试路径，实际模型和远端服务需另行验证。{boundary}。运行结果写入本章 workbook.md。
"""
    readme.write_text(introduction + reference, encoding="utf-8")
    workbook = folder / "workbook.md"
    if not workbook.exists():
        workbook.write_text(
            f"# {step_label(step)} · 学习记录\n\n问题：{problem}。\n\n- 我的解释：待填写。\n- 实际命令与结果：待填写。\n- 失败路径与原因：待填写。\n- 尚未验证：{boundary}。\n",
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=list(META))
    render(parser.parse_args().step)


if __name__ == "__main__":
    main()
