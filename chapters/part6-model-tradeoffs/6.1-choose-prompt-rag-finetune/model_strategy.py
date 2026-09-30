"""
章节 6.1 · 从需求约束选择 Prompt / RAG / 微调
==========================================================
三者不是互斥的产品，也没有固定的成本排序：

- Prompt 定义当前任务、边界和输出契约，但不会可靠地补齐模型不知道的私有知识。
- RAG 在推理时注入外部知识，适合知识会变化、需要引用或需要按权限取数的场景。
- 微调主要改变稳定的行为、格式或领域模式；它不是动态知识库，也不天然提供引用。

生产选型从可验证的业务目标开始：质量、时延、吞吐、权限、更新频率和总拥有成本；
再用离线评测与线上观测决定是否增加 RAG 或微调，而不是套一句固定口诀。

本文件把这些判断写成一个小的规则函数 decide()：输入需求约束，输出起始方案、理由和上线前检查项。
它只给"起始方案"，不是对任何模型或业务的性能承诺。

前置：2.3（RAG）、1.3（结构化输出）
运行：python tools/run_chapter.py 6.1（离线，不调用模型）
输出：三个场景的方案建议，以及大模型输出能力的四个可组合维度
==========================================================
"""

from dataclasses import dataclass
from enum import Enum


class Strategy(str, Enum):
    PROMPT = "Prompt"
    RAG = "RAG"
    FINE_TUNING = "微调"
    RAG_AND_FINE_TUNING = "RAG + 微调"


@dataclass(frozen=True)
class Decision:
    """可记录、可评审的技术选型结果：选了什么、为什么、上线前要检查什么。"""

    strategy: Strategy
    reasons: tuple[str, ...]
    production_checks: tuple[str, ...]

    def summary(self) -> str:
        return f"{self.strategy.value}：{'；'.join(self.reasons)}"


def decide(
    *,
    knowledge_updates_often: bool,          # 知识经常变化
    need_citation: bool,                    # 答案需要给出可核对的来源
    model_lacks_required_knowledge: bool,   # 模型本身不掌握所需的知识（如私有资料）
    need_fixed_behavior: bool,              # 需要固定的风格、格式或行为
    enough_training_examples: bool,         # 有足够的高质量训练样本
    training_is_feasible: bool,             # 预算、算力和数据许可允许训练
) -> Decision:
    """根据需求约束给出起始方案；最终结论仍须由评测数据验证。"""
    # 知识类需求（变化、引用、模型不掌握）靠 RAG：微调不是动态知识库，也没有引用
    needs_retrieval = (
        knowledge_updates_often
        or need_citation
        or model_lacks_required_knowledge
    )
    # 行为类需求（固定风格或格式）才值得微调，且样本和训练条件必须同时满足
    can_fine_tune = (
        need_fixed_behavior and enough_training_examples and training_is_feasible
    )

    if needs_retrieval and can_fine_tune:
        strategy = Strategy.RAG_AND_FINE_TUNING
        reasons = ("外部知识需在推理时更新/溯源", "有足够样本固化稳定行为")
    elif needs_retrieval:
        strategy = Strategy.RAG
        reasons = ("答案依赖模型外部知识、更新或引用",)
    elif can_fine_tune:
        strategy = Strategy.FINE_TUNING
        reasons = ("目标是稳定行为且已有足够高质量训练样本",)
    else:
        # 两类需求都不明显时，先用 Prompt 建立最小的可评测基线，再决定要不要加机制
        strategy = Strategy.PROMPT
        reasons = ("暂不需要外部知识或训练，先建立最小可评测基线",)

    # 不管选哪个方案，上线前都要验证这几项；微调另加基座对照、数据许可和回滚
    checks = [
        "用代表性评测集比较质量、拒答和引用正确率",
        "测量 p95 时延、吞吐和单次请求总成本",
        "私有知识在检索前执行租户与文档权限过滤",
    ]
    if can_fine_tune:
        checks.append("保留基座模型对照组，并验证数据许可、漂移与回滚")
    return Decision(strategy, reasons, tuple(checks))


def recommend(
    knowledge_updates_often: bool,
    need_citation: bool,
    need_fixed_style: bool,
    budget_for_training: bool,
    enough_training_examples: bool = False,
) -> str:
    """简化入口：用位置参数快速试问，返回一句话结论。

    预算和高质量训练样本是两项独立前提，缺一都不能微调。
    这里假设"知识经常变化"就意味着"模型不掌握所需知识"，需要区分时请直接调用 decide()。
    """
    decision = decide(
        knowledge_updates_often=knowledge_updates_often,
        need_citation=need_citation,
        model_lacks_required_knowledge=knowledge_updates_often,
        need_fixed_behavior=need_fixed_style,
        enough_training_examples=enough_training_examples,
        training_is_feasible=budget_for_training,
    )
    return decision.summary()


# 大模型的输出能力是可组合的维度，不是五个互斥的类别
OUTPUT_DIMENSIONS = (
    ("内容", "文本、图片、音频等模态"),
    ("传输", "一次性响应或流式传输"),
    ("契约", "自由文本或经 schema 校验的结构化数据"),
    ("动作", "只返回内容，或提出需由应用校验并执行的工具调用"),
)


def show_output_modes() -> None:
    for name, description in OUTPUT_DIMENSIONS:
        print(f"  - {name}：{description}")


if __name__ == "__main__":
    print("===== 方案决策示例 =====")
    print("企业知识库问答（知识常更新、要溯源）：")
    print("  →", recommend(True, True, False, False))
    print("客服要统一品牌口吻（知识静态、有预算且有高质量样本）：")
    print("  →", recommend(False, False, True, True, True))
    print("把回答改成更口语（需求简单）：")
    print("  →", recommend(False, False, False, False))
    print("\n===== 大模型输出的可组合维度 =====")
    show_output_modes()
