"""
Day 77 · 提示工程进阶：zero-shot / few-shot / CoT 对比
==========================================================
测试工程师转 AI 应用开发  ← 1-33 补充包（补阶段0 缺口：提示工程进阶）

同一个任务，怎么"问"直接决定答得好不好。三种基本提示法，面试常被要求对比：

【zero-shot】直接问，不给例子。简单任务够用、最省 token。
【few-shot】 给几个示范例子，模型照葫芦画瓢——要控【输出格式/风格/边界】时，
    给例子比写一堆规则更有效。
【CoT 思维链】让模型"一步步想"，把推理过程显式化。多步推理/算术/逻辑题正确率更高，
    而且推理可见——错在哪一步能看出来（正好呼应测试背景的可观测）。

本文件设计成【没配 API key 也能看懂】：核心是把三种 prompt 怎么拼【打印出来】对比；
配了 DEEPSEEK_API_KEY 则再真跑一遍看输出差异。

衔接：Day1 学了 prompt 模板；这里补"同一任务的三种问法与取舍"；
      few-shot 的"给例子约束输出"和 Day3 结构化输出是一对好搭档。
==========================================================
"""

import os
from dotenv import load_dotenv

load_dotenv()   # 读 .env 里的 DEEPSEEK_API_KEY


# —— 内联 LLM 工厂：本文件自包含，不依赖 common.py，方便单独阅读 ——
def get_llm(temperature: float = 0.0, model: str = "deepseek-chat", **kwargs):
    """DeepSeek 对话模型（OpenAI 兼容）。temperature=0 → 输出可复现。"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
        temperature=temperature,
        **kwargs,
    )


HAS_KEY = bool(os.getenv("DEEPSEEK_API_KEY"))


def ask(prompt: str) -> str:
    """有 key 就真调模型，没 key 返回占位说明（保证无 key 也能跑完）。"""
    if not HAS_KEY:
        return "（未配 DEEPSEEK_API_KEY，跳过真实调用——上面的 prompt 构造已能看清差异）"
    return get_llm(temperature=0).invoke(prompt).content


# ============================================================
# 【一】zero-shot vs few-shot：用例子约束"输出格式"
# ============================================================
def demo_zero_vs_few():
    sentence = "本季度蓝海科技净利润达 380 万元。"
    task = "从句子中抽取【公司】和【金额】，只输出一行 JSON。"

    # zero-shot：直接问，不给例子——模型可能自由发挥格式
    zero_prompt = f"{task}\n句子：{sentence}"

    # few-shot：给 2 个示范，用例子把"确切格式"传达给模型
    few_prompt = (
        f"{task}\n"
        '例1：句子：示例科技2025Q2营收1510万元。 → {"company":"示例科技","amount":"1510万元"}\n'
        '例2：句子：远山制造本季亏损200万元。 → {"company":"远山制造","amount":"-200万元"}\n'
        f"句子：{sentence} →"
    )

    print("  [zero-shot] prompt：")
    print("   ", zero_prompt.replace("\n", "\n    "))
    print("   → 模型答：", ask(zero_prompt))
    print("\n  [few-shot] prompt（多了 2 个例子约束格式）：")
    print("   ", few_prompt.replace("\n", "\n    "))
    print("   → 模型答：", ask(few_prompt))
    print("\n  要点：要固定输出格式/风格/边界，给例子（few-shot）比写一堆规则更稳。")


# ============================================================
# 【二】CoT 思维链：多步推理让模型"一步步想"
# ============================================================
def demo_cot():
    q = "仓库有 120 箱货，先发走了 1/3，随后又进货 45 箱，现在有多少箱？"

    # 直接问：模型可能跳步算错，且看不到推理
    direct_prompt = f"{q}\n直接给出最终数字。"
    # CoT：要求一步步推理——正确率更高，且每一步可检查
    cot_prompt = f"{q}\n请一步步推理（先算发走多少、再算剩多少、再加进货），最后一行给出答案。"

    print("  [直接问] →", ask(direct_prompt))
    print("\n  [CoT 一步步想] →")
    ans = ask(cot_prompt)
    print("   ", str(ans).replace("\n", "\n    "))
    print("\n  正确答案：120 - 40 + 45 = 125。CoT 的价值：正确率更高，且错在哪一步看得见。")


# ============================================================
# 【三】few-shot + CoT：例子里也示范"怎么想"
# ============================================================
def demo_few_shot_cot():
    # 例子里带推理过程，模型会模仿"先想再答"的方式
    prompt = (
        "按示例的推理方式解题。\n"
        "例：小明有5个苹果，给了2个，又买了3个，还剩几个？\n"
        "想：5-2=3，3+3=6。答：6。\n"
        "题：书架有8本书，拿走3本，又放回5本，现在几本？\n"
        "想："
    )
    print("  [few-shot CoT] prompt：")
    print("   ", prompt.replace("\n", "\n    "))
    print("   → 模型答：", ask(prompt))
    print("\n  要点：例子里示范推理过程，模型会照着'先想后答'——格式+推理一起约束。")


if __name__ == "__main__":
    print("===== 【一】zero-shot vs few-shot（用例子约束格式）=====")
    demo_zero_vs_few()
    print("\n===== 【二】CoT 思维链（多步推理）=====")
    demo_cot()
    print("\n===== 【三】few-shot + CoT 结合 =====")
    demo_few_shot_cot()
    if not HAS_KEY:
        print("\n（提示：配置 DEEPSEEK_API_KEY 后重跑，可看到三种问法的真实输出差异）")


# ----------------------------------------------------------
# 小结：
# - zero-shot：直接问，简单任务够用、最省 token。
# - few-shot：给例子，要控输出格式/风格/边界时最有效——例子胜过一堆文字规则。
# - CoT：让模型一步步想，多步推理/算术正确率更高，且推理可见、错步可查。
# - few-shot + CoT：例子里示范推理，格式与推理一起约束。
# - 取舍：few-shot / CoT 更费 token、更慢，用评测集（Day18）权衡"效果涨多少 vs 成本"。
#
# 面试话术：
#   "提示我分三档用：简单任务 zero-shot 省 token；要控输出格式或处理边界，few-shot
#    给例子比写规则管用；多步推理/算术上 CoT 让模型一步步想，正确率更高、还能看出
#    错在哪一步。代价是更费 token，我用评测集量化'效果涨多少、成本涨多少'再决定。"
#
# 动手练习：给同一个抽取任务，分别用 zero/few-shot 各跑 10 条，用 Day18 的关键词命中率
#          量化 few-shot 到底提升了多少格式正确率——把"感觉更好"变成带分母的数字。
# ----------------------------------------------------------
