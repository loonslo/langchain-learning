"""Day51–78 单项目里程碑目录与证据入口。"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent
Status = Literal["integrated", "partial"]


@dataclass(frozen=True)
class Milestone:
    day: int
    title: str
    status: Status
    story: str
    evidence: tuple[str, ...]
    acceptance: tuple[str, ...]


MILESTONES = (
    Milestone(
        51,
        "客服知识库 v0.1",
        "integrated",
        "用已学 LangChain 组件完成第一个可用客服 RAG",
        (
            "day51/README.md",
            "day51/src/customer_support/assistant.py",
            "day51/data/knowledge/customer_faq.md",
            "day51/tests/test_assistant.py",
        ),
        ("cd day51 && pytest -q",),
    ),
    Milestone(
        52,
        "最小知识问答",
        "integrated",
        "真实语料进入 RAG 与统一服务",
        ("capstone/knowledge_base.py", "capstone/service.py"),
        ("python -m capstone.main build",),
    ),
    Milestone(
        53,
        "质量基线",
        "partial",
        "检索、生成、引用和结构化输出分层评测",
        ("capstone/evaluation.py", "capstone/data/eval_set.json"),
        ("python -m capstone.main eval",),
    ),
    Milestone(
        54,
        "增量摄取",
        "integrated",
        "正文、ACL 和管线配置共同形成知识版本",
        ("capstone/connector.py", "capstone/knowledge_base.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        55,
        "授权边界",
        "integrated",
        "查询前 ACL、默认拒绝和租户隔离",
        ("capstone/permissions.py", "capstone/test_production.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        56,
        "可信身份",
        "integrated",
        "JWT、多租户、角色和共享限流",
        ("capstone/auth.py", "capstone/api_enterprise.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        57,
        "上下文工程",
        "integrated",
        "ACL 前置、预算和不可信资料封装进入 RAG",
        ("capstone/context.py", "capstone/knowledge_base.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        58,
        "统一服务与可靠性",
        "integrated",
        "API、CLI、评测共享 AssistantService",
        ("capstone/service.py", "capstone/api_enterprise.py", "capstone/evaluation.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        59,
        "分层 CI",
        "partial",
        "离线、真实模型和发布门禁分层",
        (".github/workflows/eval-gate.yml", "capstone/ci_gate.py"),
        ("python -m capstone.ci_gate",),
    ),
    Milestone(
        60,
        "改进实验",
        "partial",
        "从 bad case 到候选方案推广决策",
        ("capstone/improvement_loop.py", "capstone/data/failures.json", "reports/"),
        ("python -m capstone.improvement_loop",),
    ),
    Milestone(
        61,
        "受控业务查询",
        "integrated",
        "query_id、可信身份、只读连接和超时",
        ("capstone/query_catalog.py",),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        62,
        "受控工具编排",
        "partial",
        "结构化模式、工具白名单和显式能力契约",
        ("capstone/contracts.py", "capstone/service.py", "capstone/query_catalog.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        63,
        "持久化审批",
        "integrated",
        "租户隔离、过期和一次性决策",
        ("capstone/approval.py", "capstone/api_enterprise.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        64,
        "长期记忆",
        "integrated",
        "显式设置、查看、删除和隔离偏好",
        ("capstone/memory.py", "capstone/service.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        65,
        "内容安全",
        "integrated",
        "输入输出审核、失败关闭和无明文审计",
        ("capstone/content_safety.py", "capstone/api_enterprise.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        66,
        "Provider 契约",
        "partial",
        "统一工厂和保守能力声明",
        ("common.py", "capstone/provider_contract.py"),
        ("python -m capstone.provider_contract",),
    ),
    Milestone(
        67,
        "可观测与告警",
        "partial",
        "租户指标、样本门槛和告警退出码",
        ("capstone/monitoring.py", "capstone/monitoring_cli.py"),
        ("python -m capstone.monitoring_cli --demo",),
    ),
    Milestone(
        68,
        "向量存储迁移",
        "partial",
        "pgvector 迁移、幂等和 ACL",
        ("capstone/vector_store_pg.py",),
        ("python -m capstone.vector_store_pg migration",),
    ),
    Milestone(
        69,
        "容量验证",
        "partial",
        "认证 API 的 fake/real 压测与 SLO",
        ("capstone/load_test.py",),
        ("python -m capstone.load_test --fake --users 2 --time 5s",),
    ),
    Milestone(
        70,
        "交付制品",
        "partial",
        "容器、非 root 和启动检查",
        ("Dockerfile", ".dockerignore", "capstone/deployment_check.py"),
        ("python -m capstone.deployment_check",),
    ),
    Milestone(
        71,
        "Staging 发布",
        "partial",
        "部署、smoke、灰度和回滚",
        ("capstone/DEPLOY.md", "capstone/docs/runbooks/release.md"),
        ("python -m capstone.deployment_check --base-url <url>",),
    ),
    Milestone(
        72,
        "备份恢复",
        "partial",
        "恢复后重新验证权限与质量",
        ("capstone/docs/runbooks/backup_restore.md",),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        73,
        "事故演练",
        "partial",
        "故障注入、runbook 和 postmortem",
        ("capstone/docs/runbooks/incident_acl_leak.md",),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        74,
        "上线评审",
        "partial",
        "Production Readiness Review",
        ("capstone/docs/production_readiness.md",),
        ("python -m capstone.milestones 74",),
    ),
    Milestone(
        75,
        "项目交接",
        "partial",
        "README、ADR、运行手册和证据审计",
        (
            "capstone/README.md",
            "capstone/docs/adr/001-modular-monolith.md",
            "capstone/evidence_audit.py",
        ),
        ("python -m capstone.evidence_audit",),
    ),
    Milestone(
        76,
        "简历证据",
        "integrated",
        "只引用仓库和报告能证明的事实",
        (
            "capstone/docs/portfolio/resume_evidence.md",
            "capstone/interview_evidence.py",
        ),
        ("python -m capstone.interview_evidence --strict-evidence",),
    ),
    Milestone(
        77,
        "技术讲解",
        "integrated",
        "RAG、Agent、工程问答和项目 pitch",
        (
            "capstone/docs/portfolio/rag_agent_interview.md",
            "capstone/docs/portfolio/enterprise_interview.md",
            "capstone/docs/portfolio/project_pitch.md",
        ),
        ("python -m capstone.milestones 77",),
    ),
    Milestone(
        78,
        "最终验收",
        "integrated",
        "模拟面试、复盘和下一版本路线",
        ("capstone/docs/portfolio/final_review.md",),
        ("python -m capstone.milestones 78",),
    ),
)

DAILY_FILES = {
    path.name.split("_", 1)[0]: path.name
    for path in ROOT.glob("day*.py")
    if path.name[:5].removeprefix("day").isdigit()
    and 51 <= int(path.name[3:5]) <= 78
}
for _day in range(51, 79):
    if (ROOT / f"day{_day}" / "README.md").is_file():
        DAILY_FILES[f"day{_day}"] = f"day{_day}/README.md"


def _status(milestone: Milestone) -> dict[str, object]:
    task_file = DAILY_FILES.get(f"day{milestone.day}", "")
    evidence_paths = ((task_file,) if task_file else ()) + milestone.evidence
    evidence = {
        path: (ROOT / path.rstrip("/")).exists() for path in evidence_paths
    }
    return {
        **asdict(milestone),
        "task_file": task_file,
        "evidence_status": evidence,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("day", nargs="?", type=int)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict-evidence", action="store_true")
    args = parser.parse_args(argv)
    selected = [item for item in MILESTONES if args.day in {None, item.day}]
    if not selected:
        parser.error("day 必须在 51-78")
    payload = [_status(item) for item in selected]
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for item, status in zip(selected, payload):
            print(f"Day{item.day} [{item.status}] {item.title}")
            print(f"  项目事件：{item.story}")
            print("  验收：" + "；".join(item.acceptance))
            for path, exists in status["evidence_status"].items():
                print(f"  {'OK' if exists else 'MISSING'} {path}")
    missing = [
        path
        for item in payload
        for path, exists in item["evidence_status"].items()
        if not exists
    ]
    return 1 if args.strict_evidence and missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
