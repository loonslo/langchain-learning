"""旗舰项目后端步骤与 capstone 能力证据入口（仅检查文件存在）。"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from tools.course_catalog import step_label

ROOT = Path(__file__).resolve().parent.parent
Status = Literal["integrated", "partial"]


@dataclass(frozen=True)
class Milestone:
    step: str
    title: str
    status: Status
    story: str
    evidence: tuple[str, ...]
    acceptance: tuple[str, ...]


MILESTONES = (
    Milestone(
        "m1-rag-mvp/step1",
        "客服知识库 v0.1",
        "integrated",
        "用已学 LangChain 组件完成第一个可用客服 RAG",
        (
            "flagship-project/m1-rag-mvp/step1/README.md",
            "flagship-project/m1-rag-mvp/step1/src/customer_support/assistant.py",
            "flagship-project/m1-rag-mvp/step1/data/knowledge/customer_faq.md",
            "flagship-project/m1-rag-mvp/step1/tests/test_assistant.py",
        ),
        (
            "python -m pytest -c flagship-project/m1-rag-mvp/step1/pyproject.toml flagship-project/m1-rag-mvp/step1/tests -q",
        ),
    ),
    Milestone(
        "m1-rag-mvp/step2",
        "最小知识问答",
        "integrated",
        "真实语料进入 RAG 与统一服务",
        ("capstone/knowledge_base.py", "capstone/service.py"),
        ("python -m capstone.main build",),
    ),
    Milestone(
        "m1-rag-mvp/step3",
        "质量基线",
        "partial",
        "检索、生成、引用和结构化输出分层评测",
        ("capstone/evaluation.py", "capstone/data/eval_set.json"),
        ("python -m capstone.main eval",),
    ),
    Milestone(
        "m1-rag-mvp/step4",
        "增量摄取",
        "integrated",
        "正文、ACL 和管线配置共同形成知识版本",
        ("capstone/connector.py", "capstone/knowledge_base.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m2-session-langgraph/step1",
        "授权边界",
        "integrated",
        "查询前 ACL、默认拒绝和租户隔离",
        ("capstone/permissions.py", "capstone/test_production.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m2-session-langgraph/step2",
        "可信身份",
        "integrated",
        "JWT、多租户、角色和共享限流",
        ("capstone/auth.py", "capstone/api_enterprise.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m3-order-tool-reliability/step1",
        "上下文工程",
        "integrated",
        "ACL 前置、预算和不可信资料封装进入 RAG",
        ("capstone/context.py", "capstone/knowledge_base.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m3-order-tool-reliability/step2",
        "统一服务与可靠性",
        "integrated",
        "API、CLI、评测共享 AssistantService",
        ("capstone/service.py", "capstone/api_enterprise.py", "capstone/evaluation.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m3-order-tool-reliability/step3",
        "分层 CI",
        "partial",
        "离线、真实模型和发布门禁分层",
        (".github/workflows/eval-gate.yml", "capstone/ci_gate.py"),
        ("python -m capstone.ci_gate",),
    ),
    Milestone(
        "m3-order-tool-reliability/step4",
        "改进实验",
        "partial",
        "从 bad case 到候选方案推广决策",
        ("capstone/improvement_loop.py", "capstone/data/failures.json", "reports/"),
        ("python -m capstone.improvement_loop",),
    ),
    Milestone(
        "m4-api-identity-security/step1",
        "受控业务查询",
        "integrated",
        "query_id、可信身份、只读连接和超时",
        ("capstone/query_catalog.py",),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m4-api-identity-security/step2",
        "受控工具编排",
        "partial",
        "结构化模式、工具白名单和显式能力契约",
        ("capstone/contracts.py", "capstone/service.py", "capstone/query_catalog.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m4-api-identity-security/step3",
        "持久化审批",
        "integrated",
        "租户隔离、过期和一次性决策",
        ("capstone/approval.py", "capstone/api_enterprise.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m4-api-identity-security/step4",
        "长期记忆",
        "integrated",
        "显式设置、查看、删除和隔离偏好",
        ("capstone/memory.py", "capstone/service.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m5-injection-pii-observability/step1",
        "内容安全",
        "integrated",
        "输入输出审核、失败关闭和无明文审计",
        ("capstone/content_safety.py", "capstone/api_enterprise.py"),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m5-injection-pii-observability/step2",
        "Provider 契约",
        "partial",
        "统一工厂和保守能力声明",
        ("common.py", "capstone/provider_contract.py"),
        ("python -m capstone.provider_contract",),
    ),
    Milestone(
        "m5-injection-pii-observability/step3",
        "可观测与告警",
        "partial",
        "租户指标、样本门槛和告警退出码",
        ("capstone/monitoring.py", "capstone/monitoring_cli.py"),
        ("python -m capstone.monitoring_cli --demo",),
    ),
    Milestone(
        "m5-injection-pii-observability/step4",
        "向量存储迁移",
        "partial",
        "pgvector 迁移、幂等和 ACL",
        ("capstone/vector_store_pg.py",),
        ("python -m capstone.vector_store_pg migration",),
    ),
    Milestone(
        "m6-quality-gate-container/step1",
        "容量验证",
        "partial",
        "认证 API 的 fake/real 压测与 SLO",
        ("capstone/load_test.py",),
        ("python -m capstone.load_test --fake --users 2 --time 5s",),
    ),
    Milestone(
        "m6-quality-gate-container/step2",
        "交付制品",
        "partial",
        "容器、非 root 和启动检查",
        ("Dockerfile", ".dockerignore", "capstone/deployment_check.py"),
        ("python -m capstone.deployment_check",),
    ),
    Milestone(
        "m7-capacity-feedback-recovery/step1",
        "Staging 发布",
        "partial",
        "部署、smoke、灰度和回滚",
        ("capstone/DEPLOY.md", "capstone/docs/runbooks/release.md"),
        ("python -m capstone.deployment_check --base-url <url>",),
    ),
    Milestone(
        "m7-capacity-feedback-recovery/step2",
        "备份恢复",
        "partial",
        "恢复后重新验证权限与质量",
        ("capstone/docs/runbooks/backup_restore.md",),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m7-capacity-feedback-recovery/step3",
        "事故演练",
        "partial",
        "故障注入、runbook 和 postmortem",
        ("capstone/docs/runbooks/incident_acl_leak.md",),
        ("pytest capstone/test_production.py -q",),
    ),
    Milestone(
        "m7-capacity-feedback-recovery/step4",
        "上线评审",
        "partial",
        "Production Readiness Review",
        ("capstone/docs/production_readiness.md",),
        ("python -m capstone.milestones m7-capacity-feedback-recovery/step4",),
    ),
    Milestone(
        "m7-capacity-feedback-recovery/step5",
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
        "m7-capacity-feedback-recovery/step6",
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
        "m8-evidence-final-frontend/step1",
        "技术讲解",
        "integrated",
        "RAG、Agent、工程问答和项目 pitch",
        (
            "capstone/docs/portfolio/rag_agent_interview.md",
            "capstone/docs/portfolio/enterprise_interview.md",
            "capstone/docs/portfolio/project_pitch.md",
        ),
        ("python -m capstone.milestones m8-evidence-final-frontend/step1",),
    ),
    Milestone(
        "m8-evidence-final-frontend/step2",
        "最终验收",
        "integrated",
        "模拟面试、复盘和下一版本路线",
        ("capstone/docs/portfolio/final_review.md",),
        ("python -m capstone.milestones m8-evidence-final-frontend/step2",),
    ),
)


def _status(milestone: Milestone) -> dict[str, object]:
    task_file = "flagship-project/" + milestone.step + "/README.md"
    evidence_paths = ((task_file,) if task_file else ()) + milestone.evidence
    evidence = {path: (ROOT / path.rstrip("/")).exists() for path in evidence_paths}
    return {
        **asdict(milestone),
        "label": step_label(milestone.step),
        "task_file": task_file,
        "evidence_status": evidence,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "target",
        nargs="?",
        help="例如 m3-order-tool-reliability/step2 或 m3-order-tool-reliability",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict-evidence", action="store_true")
    args = parser.parse_args(argv)
    selected = [
        item
        for item in MILESTONES
        if args.target is None
        or item.step == args.target
        or item.step.split("/")[0] == args.target
    ]
    if not selected:
        parser.error("请选择旗舰项目中存在的后端里程碑/步骤（step3 前端见章节总地图）")
    payload = [_status(item) for item in selected]
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "以下为教学步骤与历史 capstone 能力记录的对照；文件存在不代表运行验收通过。"
        )
        for item, status in zip(selected, payload):
            print(
                f"{step_label(item.step)} | capstone 能力 [{item.status}] {item.title}"
            )
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
