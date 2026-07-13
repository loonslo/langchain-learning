"""
Day 24 · LangSmith prompt A/B 对比 + judge 一致性校验
==========================================================
测试工程师转 AI 应用开发 · 阶段2 评测做深（护城河）

学习目标（给初学者）：
1. 为什么做 prompt A/B？
   同一批问题，用两版 prompt 分别回答，看指标（关键词、来源、拒答、judge 分数）。
   选 prompt 不靠"我觉得顺眼"，而靠数据。
2. 什么是 LLM-as-judge？
   用另一个 LLM 给答案打分。它也会犯错，所以要和人工标注做一致性校验。
3. 什么是 LangSmith experiment / dataset？
   - dataset：评测集，包含问题 + 参考答案 + 人工评分。
   - experiment：在 dataset 上跑一遍模型，生成指标。
   同一 dataset 跑两次 experiment，就能在 LangSmith 里直观对比 A/B。

这一天是独立可运行模块，不依赖 common.py、evals/ 或其他 day 文件。

真实结果在 LangSmith experiments；本地只落一个 experiment 链接摘要：
reports/prompt_ab_judge_agreement.json。

运行前置：
  .env 配置 LANGSMITH_API_KEY 和 DEEPSEEK_API_KEY
==========================================================
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# 加载 .env 中的 API key，避免把密钥写进代码。
load_dotenv()

# --------------------------- 常量与路径 ---------------------------
ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"

# LangSmith 中的 dataset 名字。dataset 是"考题本"，可以反复用来跑 experiment。
DATASET_NAME = "day24-prompt-ab-langsmith"

# LangSmith project 名字，所有 trace 会归到这个项目下。
LANGSMITH_PROJECT = "day24-prompt-ab-judge"

# 知识库来源标识，答案里出现这个字符串才算"标注了来源"。
SOURCE_NAME = "day24_embedded_notes"

# 判断"拒答"时用到的关键词。只要答案里出现任意一个，就认为模型选择了拒答。
REFUSE_HINTS = ["没有提到", "信息不足", "无法回答", "不知道", "无相关"]

# --------------------------- 知识库 ---------------------------
# 这里用一个小型硬编码知识库模拟 RAG 检索结果。
# 真实项目里，这段通常来自向量数据库（Chroma/FAISS）或 Elasticsearch。
KNOWLEDGE_BASE = [
    {
        "source": SOURCE_NAME,
        "keywords": ["rag", "检索", "生成", "知识库", "上下文"],
        "content": (
            "RAG 是检索增强生成：先从知识库检索相关内容，再把检索到的上下文交给模型生成答案。"
            "它适合知识常更新、需要溯源、不能只靠模型记忆回答的场景。"
        ),
    },
    {
        "source": SOURCE_NAME,
        "keywords": ["prompt", "a/b", "ab", "评测", "指标", "选择"],
        "content": (
            "prompt A/B 的核心是在同一份评测集上比较两版 prompt 的指标，"
            "例如关键词命中、引用正确性、拒答一致性和 LLM-as-judge 分数。"
            "这样选 prompt 靠数据，不靠主观感觉。"
        ),
    },
    {
        "source": SOURCE_NAME,
        "keywords": ["judge", "裁判", "人工", "一致性", "可信"],
        "content": (
            "LLM-as-judge 会有偏差，所以需要拿人工抽样标注做一致性检查。"
            "如果 judge 通过/不通过的判断和人工标签一致率太低，就不能直接相信它的分数。"
        ),
    },
    {
        "source": SOURCE_NAME,
        "keywords": ["成本", "质量", "优化", "下降", "验证"],
        "content": (
            "成本优化不能只看便宜，还要验证质量没有明显下降。"
            "常见做法是记录成本、延迟、通过率和失败用例，确保省钱没有破坏核心效果。"
        ),
    },
    {
        "source": SOURCE_NAME,
        "keywords": ["回归", "曲线", "退化", "指标", "变化"],
        "content": (
            "回归曲线展示每次改动后的指标变化，帮助发现质量退化。"
            "失败用例库则把问题沉淀成可重复验证的资产。"
        ),
    },
    {
        "source": SOURCE_NAME,
        "keywords": ["上下文不足", "不足", "拒答", "不知道", "无法回答"],
        "content": (
            "当上下文不足时，RAG 助手应该明确说明信息不足或无法回答，"
            "而不是补常识、猜测或编造没有依据的内容。"
        ),
    },
]

# --------------------------- A/B 评测用例 ---------------------------
# 每个用例包含：
#   question        : 用户问题
#   reference       : 参考答案（给 judge 看的"标准答案"）
#   keywords        : 机器可量化的关键词，答案里要出现
#   expected_sources: 答案里应该出现的来源标识
#   should_refuse   : 这道题是否期望模型拒答
#   manual_score    : 人工打分（1-5），用于校验 judge 一致性
#   expected_winner : （注释）说明这题理论上哪个 prompt 更占优，帮助初学者理解 A/B 差异
PROMPT_AB_CASES = [
    # --- 用例 1：要求"一句话"简短回答，strict prompt 更占优 ---
    {
        "id": "ab_046",
        "type": "prompt_ab",
        "question": "用一句话说明 RAG 是什么。",
        "reference": "RAG 是检索增强生成，先检索相关内容，再交给模型生成答案。",
        "keywords": ["检索", "生成", "来源"],
        "expected_sources": [SOURCE_NAME],
        "should_refuse": False,
        "manual_score": 5,
        "expected_winner": "strict",
    },
    # --- 用例 2：要求"详细说明"，helpful prompt 更占优 ---
    # strict 会因为"答案必须简洁"而漏掉"溯源"等关键词，helpful 更容易拿满分。
    {
        "id": "ab_047",
        "type": "prompt_ab",
        "question": "RAG 适合哪些场景？请结合上下文详细说明。",
        "reference": "适合知识常更新、需要溯源、不能只靠模型记忆的场景。",
        "keywords": ["知识更新", "溯源", "模型记忆", "来源"],
        "expected_sources": [SOURCE_NAME],
        "should_refuse": False,
        "manual_score": 5,
        "expected_winner": "helpful",
    },
    # --- 用例 3：拒答规范（元问题）---
    # 问题问的是"应该怎么回答"，所以不应拒答，而要给出规范说明。
    {
        "id": "ab_048",
        "type": "prompt_ab",
        "question": "上下文不足时应该怎么回答？",
        "reference": "应拒答或说明信息不足，不能编造。",
        "keywords": ["不足", "无法回答", "编造"],
        "expected_sources": [SOURCE_NAME],
        "should_refuse": False,
        "manual_score": 5,
        "expected_winner": "tie",
    },
    # --- 用例 4：需要完整解释原因，helpful prompt 更占优 ---
    {
        "id": "ab_049",
        "type": "prompt_ab",
        "question": "如何判断 judge 分数可信？请说明原因。",
        "reference": "应和人工抽样标注做一致性检查，一致率太低就不能信。",
        "keywords": ["人工", "一致性", "来源"],
        "expected_sources": [SOURCE_NAME],
        "should_refuse": False,
        "manual_score": 5,
        "expected_winner": "helpful",
    },
    # --- 用例 5：标准知识题，两版 prompt 都应答好 ---
    {
        "id": "ab_050",
        "type": "prompt_ab",
        "question": "如何用评测选择 prompt？",
        "reference": "应在同一评测集上 A/B 对比指标。",
        "keywords": ["A/B", "指标", "来源"],
        "expected_sources": [SOURCE_NAME],
        "should_refuse": False,
        "manual_score": 5,
        "expected_winner": "tie",
    },
    # --- 用例 6：需要解释"风险"，helpful prompt 更占优 ---
    {
        "id": "ab_051",
        "type": "prompt_ab",
        "question": "成本优化时如果只图便宜会有什么风险？",
        "reference": "可能导致质量下降，需要验证指标没有明显变差。",
        "keywords": ["成本", "质量", "验证", "来源"],
        "expected_sources": [SOURCE_NAME],
        "should_refuse": False,
        "manual_score": 5,
        "expected_winner": "helpful",
    },
    # --- 用例 7：简短事实题，strict prompt 更占优 ---
    {
        "id": "ab_052",
        "type": "prompt_ab",
        "question": "回归曲线能说明什么？",
        "reference": "回归曲线展示每次改动后指标变化，帮助发现退化。",
        "keywords": ["回归", "指标", "来源"],
        "expected_sources": [SOURCE_NAME],
        "should_refuse": False,
        "manual_score": 5,
        "expected_winner": "strict",
    },
    # --- 用例 8：上下文真正不足，测试拒答能力 ---
    # 知识库里没有"LangChain 0.3 新特性"，期望两版都拒答。
    # strict 会干脆回答"信息不足"；helpful 可能多解释一句为什么不足。
    {
        "id": "ab_053",
        "type": "prompt_ab",
        "question": "LangChain 0.3 版本有哪些新特性？",
        "reference": "上下文没有相关信息，应说明信息不足。",
        "keywords": ["信息不足", "无法回答"],
        "expected_sources": [],
        "should_refuse": True,
        "manual_score": 5,
        "expected_winner": "strict",
    },
    # --- 用例 9：需要展开论述，helpful prompt 更占优 ---
    {
        "id": "ab_054",
        "type": "prompt_ab",
        "question": "请详细解释 prompt A/B 测试为什么要在同一份评测集上比较。",
        "reference": "同一评测集能控制变量，保证公平对比，排除题目差异带来的干扰。",
        "keywords": ["同一份评测集", "公平", "变量", "来源"],
        "expected_sources": [SOURCE_NAME],
        "should_refuse": False,
        "manual_score": 5,
        "expected_winner": "helpful",
    },
    # --- 用例 10：边界模糊题，可能两版都漏关键词，看 judge 是否能识别 ---
    {
        "id": "ab_055",
        "type": "prompt_ab",
        "question": "RAG 评测里可以只依赖 judge 分数吗？",
        "reference": "不行，需要和人工标注做一致性校验，防止 judge 偏差。",
        "keywords": ["人工", "一致性", "judge", "来源"],
        "expected_sources": [SOURCE_NAME],
        "should_refuse": False,
        "manual_score": 4,
        "expected_winner": "tie",
    },
]

# --------------------------- LangSmith  tracing 初始化 ---------------------------
# 只有配置了 LANGSMITH_API_KEY 才开启 tracing，
# 这样本地没 key 时也不会报错（虽然 require_api_keys 会拦住）。
if os.getenv("LANGSMITH_API_KEY"):
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ.setdefault("LANGSMITH_PROJECT", LANGSMITH_PROJECT)


# --------------------------- 结构化 judge 输出 ---------------------------
class JudgeVerdict(BaseModel):
    """结构化 LLM-as-judge 输出。

    用 Pydantic 约束模型只能返回这三个字段，方便后续代码直接读取。
    """

    score: int = Field(description="1 到 5 分，5 分最好")
    passed: bool = Field(description="答案是否达到可接受质量")
    reason: str = Field(description="一句话说明主要依据")


def get_llm(temperature: float = 0.0, model: str = "deepseek-chat", **kwargs):
    """获取 DeepSeek LLM。

    参数:
        temperature: 0 表示稳定可复现，>0 会让输出更有变化。
        model      : DeepSeek 模型名，默认 deepseek-chat。
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        temperature=temperature,
        **kwargs,
    )


def require_api_keys() -> None:
    """运行前检查必要的 API key，缺少时给出明确提示。"""
    missing = [
        name
        for name in ("LANGSMITH_API_KEY", "DEEPSEEK_API_KEY")
        if not os.getenv(name)
    ]
    if missing:
        raise SystemExit(
            "Day24 需要先在 .env 配置 "
            + "、".join(missing)
            + "，然后重新运行 python day24_prompt_ab_judge.py。"
        )


def load_prompt_ab_cases() -> list[dict]:
    """加载 A/B 评测用例。"""
    return PROMPT_AB_CASES


def normalize(text: str) -> str:
    """把文本转小写并去掉所有空白，方便做简单的包含匹配。"""
    return re.sub(r"\s+", "", text.lower())


def retrieve_docs(question: str, top_k: int = 3) -> list[dict]:
    """基于关键词的简单检索器（模拟 RAG 的 retrieve 步骤）。

    思路：
    1. 把用户问题规范化。
    2. 遍历知识库，统计问题里命中了多少个文档关键词。
    3. 按命中数排序，取 top_k。

    真实项目里，这里通常是向量相似度检索 + BM25 混合排序。
    """
    query = normalize(question)
    ranked = []
    for doc in KNOWLEDGE_BASE:
        # 一个问题可能命中多个关键词，命中越多越相关。
        score = sum(1 for keyword in doc["keywords"] if normalize(keyword) in query)
        if score:
            ranked.append((score, doc))
    # 按相关分从高到低排序
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in ranked[:top_k]]


def format_docs(docs: list[dict]) -> str:
    """把检索到的文档格式化成字符串，喂给 LLM 当上下文。"""
    if not docs:
        return "没有检索到相关上下文。"
    parts = []
    for doc in docs:
        parts.append(f"[来源：{doc['source']}]\n{doc['content']}")
    return "\n\n".join(parts)


def build_prompt_chain(prompt_variant: str):
    """构建 prompt + LLM + 解析器的 chain。

    这里是 A/B 对比的核心：两版 prompt 的"系统人设"和"约束"差异要足够大，
    才能在指标上看出区别。

    prompt_variant 只能是 "strict" 或 "helpful"。
    """
    # strict 用 temperature=0 保证输出稳定；helpful 略高一点，让解释更自然。
    temperature = 0.0 if prompt_variant == "strict" else 0.2
    llm = get_llm(temperature=temperature)

    if prompt_variant == "strict":
        # strict 版：简短、必须带来源、不足时直接拒答、禁止补充常识。
        prompt = ChatPromptTemplate.from_template("""
            你是严格的知识库问答助手。必须遵守以下规则：
            1. 只依据【上下文】回答，禁止补充任何常识、例子或额外解释。
            2. 答案必须简洁，通常不超过 50 个字。
            3. 只要答案涉及文档内容，必须在句末标注【来源：<source>】。
            4. 如果上下文不足以回答问题，只回复："信息不足，无法回答。" 不要多说一个字。
            
            上下文：
            {context}
            
            问题：
            {question}
            """)
    elif prompt_variant == "helpful":
        # helpful 版：允许补充背景、解释更完整、信息不足时说明原因。
        prompt = ChatPromptTemplate.from_template("""
            你是乐于助人的知识库问答助手。必须遵守以下规则：
            1. 优先依据【上下文】回答，但可以用通俗易懂的方式补充背景，帮助用户理解。
            2. 如果上下文有相关内容，要在答案中标注来源，例如"根据 [来源：<source>]"。
            3. 如果上下文信息不足，要明确指出"信息不足"，并给出你可以提供的合理说明（但不能编造具体事实）。
            4. 回答可以适当详细，但要保持条理清晰。
            
            上下文：
            {context}
            
            问题：
            {question}
            """)
    else:
        raise ValueError(f"未知 prompt_variant：{prompt_variant}")

    # "|" 是 LangChain 的 chain 语法：prompt 输出传给 llm，llm 输出再传给解析器。
    return prompt | llm | StrOutputParser()


@lru_cache(maxsize=1)
def strict_chain():
    """缓存 strict 版 chain，避免重复创建。"""
    return build_prompt_chain("strict")


@lru_cache(maxsize=1)
def helpful_chain():
    """缓存 helpful 版 chain，避免重复创建。"""
    return build_prompt_chain("helpful")


def answer_with_variant(question: str, prompt_variant: str) -> str:
    """用指定 prompt 变体回答问题。

    流程：检索 -> 格式化上下文 -> 调用 chain -> 返回答案字符串。
    """
    context = format_docs(retrieve_docs(question))
    chain = strict_chain() if prompt_variant == "strict" else helpful_chain()
    return chain.invoke({"context": context, "question": question})


def strict_target(inputs: dict) -> dict:
    """LangSmith experiment 需要的 target 函数：strict 版。"""
    answer = answer_with_variant(inputs["question"], "strict")
    return {"answer": answer, "prompt_variant": "strict"}


def helpful_target(inputs: dict) -> dict:
    """LangSmith experiment 需要的 target 函数：helpful 版。"""
    answer = answer_with_variant(inputs["question"], "helpful")
    return {"answer": answer, "prompt_variant": "helpful"}


def looks_refused(answer: str) -> bool:
    """判断答案是否属于拒答（出现任意一个提示词即可）。"""
    return any(hint in answer for hint in REFUSE_HINTS)


# --------------------------- 评估器（evaluators） ---------------------------
# 每个 evaluator 接收 outputs（模型输出）和 reference_outputs（参考答案），
# 返回 {"key": 指标名, "score": 0~1 之间的分数}。
# LangSmith 会自动汇总这些指标。


def keyword_score(outputs: dict, reference_outputs: dict) -> dict:
    """关键词命中率。

    计算模型答案里包含了多少个预期关键词。
    如果关键词都没出现，得分就是 0。
    """
    answer = outputs["answer"].lower()
    keywords = reference_outputs.get("keywords", [])
    score = 1.0 if not keywords else sum(k.lower() in answer for k in keywords) / len(keywords)
    return {"key": "keyword_score", "score": score}


def citation_score(outputs: dict, reference_outputs: dict) -> dict:
    """来源引用命中率。

    检查模型答案里是否出现了期望的来源标识。
    如果 expected_sources 为空（如拒答题），默认给 1.0。
    """
    answer = outputs["answer"]
    sources = reference_outputs.get("expected_sources", [])
    score = 1.0 if not sources else sum(source in answer for source in sources) / len(sources)
    return {"key": "citation_score", "score": score}


def refusal_alignment(outputs: dict, reference_outputs: dict) -> dict:
    """拒答一致性。

    期望拒答（should_refuse=True）但模型没拒答，或反之，都得 0 分。
    """
    should_refuse = bool(reference_outputs.get("should_refuse"))
    refused = looks_refused(outputs["answer"])
    return {"key": "refusal_alignment", "score": 1.0 if refused == should_refuse else 0.0}


# --------------------------- LLM-as-judge ---------------------------
@lru_cache(maxsize=1)
def judge_llm():
    """初始化专门用来打分的 judge LLM，使用结构化输出。"""
    return get_llm(temperature=0).with_structured_output(JudgeVerdict, method="function_calling")


def judge_answer(inputs: dict, outputs: dict, reference_outputs: dict) -> JudgeVerdict:
    """让 judge LLM 对单个答案打分。

    输入包含问题、参考答案、关键词、期望来源、是否应拒答，以及模型答案。
    输出是结构化的 JudgeVerdict（score / passed / reason）。
    """
    prompt = """
        你是 RAG 评测裁判。请比较问题、参考答案和模型答案，判断模型答案是否可接受。
        
        评分标准：
        - 5 分：准确、覆盖参考答案要点、没有编造，来源/拒答要求也正确。
        - 4 分：基本正确，只有轻微遗漏。
        - 3 分：部分正确但有明显缺口。
        - 2 分：大部分不正确或没有遵守拒答/来源要求。
        - 1 分：错误、编造，或上下文不足时仍胡答。
        
        问题：{question}
        参考答案：{reference}
        关键词：{keywords}
        期望来源：{sources}
        是否应拒答：{should_refuse}
        模型答案：{answer}
        """
    return judge_llm().invoke(
        prompt.format(
            question=inputs["question"],
            reference=reference_outputs.get("reference", ""),
            keywords=reference_outputs.get("keywords", []),
            sources=reference_outputs.get("expected_sources", []),
            should_refuse=reference_outputs.get("should_refuse", False),
            answer=outputs["answer"],
        )
    )


def llm_judge(outputs: dict, reference_outputs: dict, inputs: dict) -> list[dict]:
    """LLM-as-judge evaluator。

    返回两个指标：
    - llm_judge_score : 1~5 分归一化到 0~1
    - llm_judge_pass  : 是否通过（passed=True 为 1.0）
    """
    verdict = judge_answer(inputs, outputs, reference_outputs)
    return [
        {"key": "llm_judge_score", "score": verdict.score / 5},
        {"key": "llm_judge_pass", "score": 1.0 if verdict.passed else 0.0},
    ]


# --------------------------- 汇总评估器（summary evaluators） ---------------------------
# summary evaluator 接收整个 experiment 的所有输入/输出，返回一个汇总指标。


def judge_human_agreement(inputs: list[dict], outputs: list[dict], reference_outputs: list[dict]) -> dict:
    """judge 与人工标注的一致率。

    对每条用例：
    - 人工分数 >= 4 认为"人工通过"。
    - judge 的 passed=True 认为"judge 通过"。
    两者相同即为一致。

    一致率太低，说明这个 judge prompt/模型不适合直接当裁判。
    """
    agree = 0
    for item_inputs, item_outputs, item_reference in zip(inputs, outputs, reference_outputs):
        verdict = judge_answer(item_inputs, item_outputs, item_reference)
        human_ok = item_reference.get("manual_score", 0) >= 4
        if verdict.passed == human_ok:
            agree += 1
    return {
        "key": "judge_human_agreement",
        "score": agree / len(outputs) if outputs else 0.0,
    }


def prompt_pass_rate(outputs: list[dict], reference_outputs: list[dict]) -> dict:
    """prompt 通过率。

    单条用例要同时满足：
    - 关键词命中率 >= 0.67
    - 来源引用命中率 >= 0.67
    - 拒答一致性 == 1.0
    才算通过。
    """
    passed = 0
    for item_outputs, item_reference in zip(outputs, reference_outputs):
        keyword = keyword_score(item_outputs, item_reference)["score"]
        citation = citation_score(item_outputs, item_reference)["score"]
        refusal = refusal_alignment(item_outputs, item_reference)["score"]
        if keyword >= 0.67 and citation >= 0.67 and refusal == 1.0:
            passed += 1
    return {
        "key": "prompt_pass_rate",
        "score": passed / len(outputs) if outputs else 0.0,
    }


# 普通 evaluator：对每条 example 运行一次。
EVALUATORS = [keyword_score, citation_score, refusal_alignment, llm_judge]

# summary evaluator：对整个 experiment 运行一次。
SUMMARY_EVALUATORS = [prompt_pass_rate, judge_human_agreement]


# --------------------------- LangSmith dataset / experiment ---------------------------
def ensure_langsmith_dataset(client, cases: list[dict]) -> None:
    """确保 LangSmith dataset 存在且包含所有用例。

    如果 dataset 已存在，只追加缺失的用例，避免重复创建。
    """
    if client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        existing_case_ids = {
            example.inputs.get("case_id")
            for example in client.list_examples(dataset_id=dataset.id)
        }
        missing_cases = [case for case in cases if case["id"] not in existing_case_ids]
    else:
        dataset = client.create_dataset(
            DATASET_NAME,
            description="Day24 self-contained prompt A/B dataset with references, checks, and manual scores.",
        )
        missing_cases = cases

    if not missing_cases:
        print(f"LangSmith dataset 已就绪：{DATASET_NAME}")
        return

    examples = []
    for case in missing_cases:
        examples.append({
            "inputs": {
                "case_id": case["id"],
                "question": case["question"],
            },
            "outputs": {
                "reference": case["reference"],
                "keywords": case.get("keywords", []),
                "expected_sources": case.get("expected_sources", []),
                "should_refuse": case.get("should_refuse", False),
                "manual_score": case.get("manual_score", 0),
            },
            "metadata": {
                "case_type": case["type"],
                "source_file": "day24_prompt_ab_judge.py",
                "expected_winner": case.get("expected_winner", "tie"),
            },
        })
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"已写入 LangSmith dataset：{DATASET_NAME}，新增 {len(examples)} 条 example")


def run_experiment(client, target: Callable[[dict], dict], prompt_variant: str):
    """在 LangSmith 上跑一次 experiment。

    target       : 接收 inputs，返回模型输出的函数。
    prompt_variant: 用于 experiment 前缀和 metadata，方便区分 A/B。
    """
    return client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=EVALUATORS,
        summary_evaluators=SUMMARY_EVALUATORS,
        experiment_prefix=f"day24-{prompt_variant}",
        description=f"Day24 self-contained prompt A/B experiment for {prompt_variant} prompt.",
        metadata={
            "day": 24,
            "prompt_variant": prompt_variant,
            "dataset": DATASET_NAME,
            "judge": "DeepSeek structured LLM-as-judge",
            "module": "day24_prompt_ab_judge.py",
        },
        max_concurrency=1,
    )


def write_langsmith_report(strict_results, helpful_results, case_count: int) -> Path:
    """把 experiment 链接和配置摘要写入本地 JSON，方便后续查看。"""
    REPORTS.mkdir(exist_ok=True)
    report = {
        "dataset": DATASET_NAME,
        "project": os.getenv("LANGSMITH_PROJECT", LANGSMITH_PROJECT),
        "cases": case_count,
        "module": "day24_prompt_ab_judge.py",
        "experiments": {
            "strict": {
                "name": strict_results.experiment_name,
                "id": str(strict_results.experiment_id),
                "url": strict_results.url,
            },
            "helpful": {
                "name": helpful_results.experiment_name,
                "id": str(helpful_results.experiment_id),
                "url": helpful_results.url,
            },
        },
        "metrics_in_langsmith": [
            "keyword_score",
            "citation_score",
            "refusal_alignment",
            "llm_judge_score",
            "llm_judge_pass",
            "prompt_pass_rate",
            "judge_human_agreement",
        ],
        "expected_winner_summary": {
            "strict": len([c for c in PROMPT_AB_CASES if c.get("expected_winner") == "strict"]),
            "helpful": len([c for c in PROMPT_AB_CASES if c.get("expected_winner") == "helpful"]),
            "tie": len([c for c in PROMPT_AB_CASES if c.get("expected_winner") == "tie"]),
        },
        "note": "真实结果在 LangSmith experiments 中查看；本文件只保存 experiment 链接和配置摘要。",
    }
    out = REPORTS / "prompt_ab_judge_agreement.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def print_legend() -> None:
    """打印指标说明，帮助初学者理解输出。"""
    print("""
        指标说明：
        - keyword_score        : 预期关键词在答案里出现了多少（0~1）
        - citation_score       : 预期来源标识在答案里出现了多少（0~1）
        - refusal_alignment    : 模型是否按要求拒答（1.0 表示一致）
        - llm_judge_score      : LLM 裁判给出的 1~5 分归一化到 0~1
        - llm_judge_pass       : LLM 裁判认为是否通过（1.0 表示通过）
        - prompt_pass_rate     : 同时满足 keyword/citation/refusal 门槛的用例比例
        - judge_human_agreement: judge 判断与人工标注的一致率（低于 0.7 要警惕）
        """)


def main() -> None:
    """主流程：检查 key -> 创建/更新 dataset -> 跑 strict experiment -> 跑 helpful experiment -> 写报告。"""
    require_api_keys()

    from langsmith import Client

    cases = load_prompt_ab_cases()
    client = Client()
    ensure_langsmith_dataset(client, cases)

    print_legend()

    print("\n===== LangSmith experiment: strict prompt =====")
    strict_results = run_experiment(client, strict_target, "strict")

    print("\n===== LangSmith experiment: helpful prompt =====")
    helpful_results = run_experiment(client, helpful_target, "helpful")

    out = write_langsmith_report(strict_results, helpful_results, len(cases))
    print("\nLangSmith A/B 评测已完成。")
    print(f"- strict:  {strict_results.url}")
    print(f"- helpful: {helpful_results.url}")
    print(f"- 本地摘要：{out}")
    print("在 LangSmith 里对比两个 experiment，重点看：")
    print("  1. prompt_pass_rate：哪版 prompt 通过率更高；")
    print("  2. judge_human_agreement：judge 和人工标注是否一致；")
    print("  3. 单条 example 的 keyword_score / citation_score / llm_judge_score 差异。")


if __name__ == "__main__":
    main()
