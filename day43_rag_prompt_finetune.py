"""
Day 43 · 认知层：RAG / Prompt / 微调 怎么选 + 大模型 5 类输出
==========================================================
测试工程师转 AI 应用开发  ← M9 认知层（以【了解】为主，别陷进去）

面试常问"这个需求你用 RAG、prompt 还是微调？"。这不是技术活，是判断力。
本节把决策标准写成一个小函数（讲清逻辑），再速览大模型的 5 类输出方式。

核心口诀：
- 知识常更新、要溯源、成本敏感 → RAG
- 只是想调输出风格/格式、需求简单 → 先试 Prompt（最便宜）
- 要固定风格/术语/领域口吻，且知识相对静态、预算够 → 才考虑微调
一句话：能 Prompt 不 RAG，能 RAG 不微调——从便宜的开始试。
==========================================================
"""


def recommend(knowledge_updates_often: bool, need_citation: bool,
              need_fixed_style: bool, budget_for_training: bool) -> str:
    """根据几个关键问题给出建议方案（决策逻辑，不是标准答案）。"""
    if knowledge_updates_often or need_citation:
        # 知识会变 / 要给出处 → 微调搞不定（训完知识就固化了），用 RAG
        base = "RAG：知识可随时更新、答案可溯源、成本低"
    elif need_fixed_style and budget_for_training:
        base = "微调：要稳定的风格/术语/领域口吻，且能承担训练成本与维护"
    else:
        base = "Prompt 工程：需求不复杂时最便宜最快，先把它榨干再说"
    return base


# 三者也常组合：用 RAG 供知识 + 微调定风格 + 好 prompt 收口。
COMBO_NOTE = "实战常组合：RAG 管'知道什么' + 微调管'怎么说' + Prompt 管'这次怎么答'"


def show_output_modes():
    """大模型 5 类输出/交互方式（你前面都动过手，这里成体系记一遍）。"""
    modes = [
        ("普通文本", "直接返回字符串", "day01"),
        ("流式 stream", "边生成边吐字，改善等待体验", "day02/day29"),
        ("结构化 JSON", "with_structured_output 拿到可解析对象", "day03"),
        ("函数调用 tool-calling", "模型决定调用哪个工具", "day05/day25"),
        ("多模态", "图片/音频等非文本输入", "day16"),
    ]
    for name, desc, where in modes:
        print(f"  - {name}：{desc}（见 {where}）")


if __name__ == "__main__":
    print("===== 方案决策示例 =====")
    print("企业知识库问答（知识常更新、要溯源）：")
    print("  →", recommend(True, True, False, False))
    print("客服要统一品牌口吻（知识静态、有预算）：")
    print("  →", recommend(False, False, True, True))
    print("把回答改成更口语（需求简单）：")
    print("  →", recommend(False, False, False, False))
    print("\n", COMBO_NOTE)

    print("\n===== 大模型 5 类输出方式 =====")
    show_output_modes()


# ----------------------------------------------------------
# 小结：
# - 选型从便宜到贵：Prompt → RAG → 微调；越往后越贵、越难维护，能不用就不用。
# - RAG vs 微调最硬的分水岭：知识要不要常更新、要不要溯源——要，就 RAG。
# - 这是【了解】级判断题，面试能讲清逻辑即可，别真去训一堆模型（那是另一个岗位）。
#
# 面试话术：
#   "我默认先 Prompt，搞不定上 RAG，只有需要稳定风格且知识静态才考虑微调；
#    企业知识库这种知识常变又要溯源的，必然 RAG，微调反而帮倒忙。"
# ----------------------------------------------------------
