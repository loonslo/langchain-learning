"""根据真实每日变更集生成 Day52–78 教程和工作簿。"""

from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = {
    52: (
        "多文档知识库",
        "单一 FAQ 无法维护多类政策",
        "稳定来源与 chunk_id 是引用、更新和排错的基础",
        "尚未证明检索质量",
    ),
    53: (
        "第一份离线评测集",
        "手工试问无法阻止质量回归",
        "评测集是可执行的产品需求，答案和引用要分开判断",
        "关键词判断不等于完整语义评测",
    ),
    54: (
        "混合检索排序",
        "纯向量检索容易错过精确业务词",
        "语义与关键词排名用 RRF 融合后仍必须回到评测集验证",
        "融合算法不保证所有问题都提升",
    ),
    55: (
        "连续追问与会话隔离",
        "那发票呢无法独立检索",
        "上下文必须有 session 边界和长度上限",
        "短问题规则只是第一版追问识别",
    ),
    56: (
        "LangGraph 显式控制流",
        "校验、检索、拒答和生成分支开始变复杂",
        "只有出现状态与分支时才引入图",
        "用了 LangGraph 不等于自主 Agent",
    ),
    57: (
        "受控订单查询工具",
        "知识库不能回答我的订单状态",
        "工具读取业务数据前必须验证资源归属",
        "当前只有只读内存订单仓库",
    ),
    58: (
        "工具超时与有限重试",
        "真实上游会出现 503 和永久错误",
        "只对临时、只读失败有限重试",
        "写操作不能直接套用读重试",
    ),
    59: (
        "人工升级闭环",
        "只说请转人工并没有完成业务闭环",
        "证据不足要创建可追踪的 open 工单",
        "内存工单尚未幂等持久化",
    ),
    60: (
        "SQLite 会话持久化",
        "内存会话在重启后丢失",
        "租户、用户、线程共同构成读取边界",
        "SQLite 只代表本地单实例验证",
    ),
    61: (
        "FastAPI 服务边界",
        "命令行无法被前端或其他服务调用",
        "HTTP 层固定输入输出契约并复用业务入口",
        "API 尚未认证",
    ),
    62: (
        "写操作幂等",
        "客户端重试可能创建重复工单",
        "同一幂等键和请求只能执行一次",
        "内存实现尚未处理多实例并发",
    ),
    63: (
        "可信身份",
        "请求正文自报 user_id 会绕过授权",
        "认证后的 Identity 才能进入业务层",
        "本地共享 secret 不等于企业 SSO",
    ),
    64: (
        "增量知识同步",
        "全量重建昂贵且删除资料会残留",
        "内容哈希决定 upsert、delete 与跳过",
        "执行向量事务和失败恢复仍待实现",
    ),
    65: (
        "提示词注入防护",
        "用户和知识文档都可能携带恶意指令",
        "不可信内容要检查、隔离并审计",
        "关键词规则会漏报和误报",
    ),
    66: (
        "PII 脱敏",
        "客服问题可能把手机号身份证写入日志",
        "业务原文与日志脱敏副本必须分开",
        "正则无法覆盖所有个人信息",
    ),
    67: (
        "可观测性",
        "线上慢或错时没有证据定位",
        "成功失败都要留下不含原始问题的 trace",
        "内存记录器不是生产监控平台",
    ),
    68: (
        "安全缓存",
        "重复问答浪费模型调用",
        "缓存键必须包含租户和知识版本且有 TTL",
        "尚未实现多实例和击穿保护",
    ),
    69: (
        "CI 质量门",
        "评测报告若只供阅读就无法阻止回归",
        "低于阈值或缺失指标都必须失败关闭",
        "门禁只覆盖已有评测集",
    ),
    70: (
        "容器与启动检查",
        "能在作者机器运行不代表可交付",
        "镜像不带密钥、非 root 运行且启动前检查依赖",
        "尚未发布真实 staging",
    ),
    71: (
        "向量库迁移契约",
        "Chroma 不能代表最终共享存储",
        "业务依赖 VectorStore 契约而非具体数据库",
        "schema 存在不等于已完成远端迁移",
    ),
    72: (
        "容量与压测判定",
        "单次响应快不能说明容量",
        "p95 与错误率共同定义可接受负载",
        "假样本不代表真实容量",
    ),
    73: (
        "用户反馈闭环",
        "bad case 需要进入可审查改进队列",
        "负反馈不能自动改生产 Prompt",
        "反馈可能有偏差且需人工复核",
    ),
    74: (
        "模型供应商降级",
        "单一模型故障会中断服务",
        "只对临时错误使用契约一致的 fallback",
        "备用模型质量仍需独立评测",
    ),
    75: (
        "备份与恢复验证",
        "有备份文件不代表能恢复",
        "恢复后必须做完整性和业务数据验证",
        "本地 SQLite 演练不等于云数据库灾备",
    ),
    76: (
        "统一业务应用",
        "组件存在但没有形成一个请求链路",
        "安全、权限、缓存、工具、工单必须由统一入口编排",
        "仍是本地同步实现",
    ),
    77: (
        "面试证据与项目讲解",
        "功能很多却无法清楚说明问题和证据",
        "简历和面试只陈述仓库可验证的结果",
        "不夸大未做的生产验证",
    ),
    78: (
        "最终验收",
        "毕业不能只看 happy path 演示",
        "任一安全和闭环能力失败都不能验收",
        "本地毕业项目不等于已生产上线",
    ),
}
ROLES = {
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
SKIP = {"README.md", "workbook.md"}
IGNORE = {"__pycache__", ".pytest_cache", ".ruff_cache", ".deepeval"}


def files(day):
    folder = ROOT / f"day{day}"
    return sorted(
        p.relative_to(folder).as_posix()
        for p in folder.rglob("*")
        if p.is_file() and p.name not in SKIP and not any(x in p.parts for x in IGNORE)
    )


def latest(day):
    result = {}
    for n in range(51, day + 1):
        for path in files(n):
            result[path] = n
    return result


def role(path):
    name = Path(path).name
    if name.startswith("test_"):
        return "验证今天新增能力的正向和失败路径"
    if path.startswith("data/"):
        return "项目真实输入资料或评测数据"
    if name == "pyproject.toml":
        return "截至今天的完整依赖与测试配置"
    if name == "Dockerfile":
        return "可复现运行镜像"
    return ROLES.get(name, "项目配置、文档或交付证据")


def symbols(day, path):
    """给初学者准确的搜索目标，避免只写一句泛泛的“阅读代码”。"""
    if not path.endswith(".py"):
        return "按文件从上到下核对配置或数据"
    tree = ast.parse((ROOT / f"day{day}" / path).read_text(encoding="utf-8"))
    names = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
            if isinstance(node, ast.ClassDef):
                names.extend(
                    f"{node.name}.{child.name}"
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not child.name.startswith("__")
                )
    return "搜索并跟踪：" + (
        "、".join(f"`{name}`" for name in names) if names else "模块级常量与数据"
    )


def render(day):
    title, problem, principle, boundary = META[day]
    changed = files(day)
    state = latest(day)
    rows = []
    for path in changed:
        previous = next((n for n in range(day - 1, 50, -1) if path in files(n)), None)
        rows.append(
            f"| `{path}` | {'修改（上一版 Day' + str(previous) + '）' if previous else '新增'} | {role(path)} |"
        )
    tree = "\n".join(
        f"{path}  # {'本日变更' if source == day else '继承 Day' + str(source)}"
        for path, source in sorted(state.items())
    )
    source_files = [p for p in changed if p.startswith("src/")]
    tests = [p for p in changed if p.startswith("tests/")]
    read_order = "\n".join(
        f"{i}. 打开 `{p}`：{symbols(day, p)}。写出输入、输出、调用方和失败分支。"
        for i, p in enumerate(source_files + tests, 1)
    )
    readme = f"""# Day{day} · {title}

> 今天解决：{problem}。
>
> 第一性原则：{principle}。

## 1. 与前一天的关系

先还原并跑通 Day{day - 1}，再开始今天。Day{day} 目录只保存今天新增或修改的完整文件；下方结构图中的“继承 DayNN”文件今天无需重复阅读。

## 2. 今天新增或修改

| 项目相对路径 | 变更 | 职责 |
|---|---|---|
{chr(10).join(rows)}

## 3. Day{day} 结束后的完整项目结构

```text
{tree}
```

## 4. 按顺序阅读和动手

{read_order}

动手时先写/修改测试，确认失败原因正确，再完成最小实现。不要读取本日未修改的继承文件，除非测试失败需要沿调用链排查。

## 5. 还原并验收

```powershell
cd D:\\workspace\\langchain-learning
.\\.venv\\Scripts\\python.exe tools\\materialize_day.py {day}
cd .build\\day{day}\\customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
..\\..\\..\\.venv\\Scripts\\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
```

验收不是只看新增测试：还原后的项目会同时运行 Day51 到今天积累的全部测试，这才证明新改动没有破坏旧能力。

## 6. 今天不能夸大的边界

{boundary}。把实际运行结果写入 `workbook.md`。
"""
    workbook = f"""# Day{day} 工作簿 · {title}

1. 前一天暴露的真实问题是什么？{problem}（请用自己的话重写）
2. 今天每个变更文件的输入、输出和调用方分别是什么？待填写。
3. 哪条测试保护 happy path，哪条保护失败或安全边界？待填写。
4. 从完整结构图中找出三个继承文件，说明为什么今天不重复复制它们。
5. 运行 `materialize_day.py {day}`，记录累计测试数量和结果。
6. 删除或改错今天的一行关键保护，观察哪条测试失败，然后恢复。
7. 今天仍不能证明什么？{boundary}（补充你的判断）
8. 用 60 秒面试表达说明：问题 → 方案 → 测试证据 → 边界。
"""
    (ROOT / f"day{day}" / "README.md").write_text(readme, encoding="utf-8")
    (ROOT / f"day{day}" / "workbook.md").write_text(workbook, encoding="utf-8")


if __name__ == "__main__":
    for day in range(52, 79):
        render(day)
