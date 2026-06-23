"""
Day 19 · 造评测集（上）：定 schema + 写第一批样本
==========================================================
测试工程师转 AI 应用开发  ★护城河★

Day17/18 已经会"算指标"了，但评测集只有示范几条。这节正式把评测集当一个
"数据资产"来造：先定一个稳定的 schema（结构固定，后面 day17/18/RAGAS/pytest
都直接吃它），再写第一批 15+ 条——本节聚焦两类最基础的题：
  - 事实问答：答案就在某一句里，考"检索得准 + 答得对"
  - 跨段落问答：答案要拼好几处，考"召回全 + 会整合"
拒答题和引用准确性放 Day20 补齐，合并后 25 条（目标可扩到 30-50）。

评测集是测试工程师的核心产物：它就是 RAG 的"自动化回归用例库"。

知识点：
1. 评测集 schema：每条 = id + 问题 + 标准答案 + 关键词 + 应命中来源 + 类型 + 是否应拒答
2. 为什么要存成 JSON（与代码解耦、可版本管理、跨工具复用）
3. 怎么按"题型"覆盖，而不是随手写几条

注：keywords 字段是给 day17"关键词命中率"这种零成本指标用的（必须出现的核心词）；
    reference 给 day18 的 LLM-as-judge 做参照。两套指标共用这一份评测集。
==========================================================
"""

import json
from pathlib import Path

# ---------- 1. 评测集 schema（一条样本的字段约定）----------
# id          唯一编号，方便定位失败 case
# question    用户问题
# reference   标准答案（人写的"应该长这样"，给正确性裁判做参照）
# keywords    答案里必须出现的核心词（给 day17 关键词命中率用；拒答题留空 []）
# expect_source  应该命中的来源/章节（检索命中率用它判断召回对不对）
# type        题型：fact(事实) / multi_hop(跨段落) / refuse(拒答，Day20 加) / citation(引用)
# should_refuse  文档里没有、应当拒答 → True（Day20 大量补）
SCHEMA_FIELDS = ["id", "question", "reference", "keywords", "expect_source", "type", "should_refuse"]

# ---------- 2. 第一批样本：事实 + 跨段落（基于 test_doc.txt 内容）----------
EVAL_SET = [
    # —— 事实问答（答案在单句内）——
    {"id": "f01", "question": "LangChain 是什么？",
     "reference": "用于开发大语言模型应用的框架", "keywords": ["框架"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    {"id": "f02", "question": "RAG 的全称是什么？",
     "reference": "检索增强生成", "keywords": ["检索", "生成"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    {"id": "f03", "question": "Chain 是做什么的？",
     "reference": "把多个步骤串联起来的流程", "keywords": ["步骤"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    {"id": "f04", "question": "Agent 的作用是什么？",
     "reference": "让模型自主决定调用哪些工具来完成任务", "keywords": ["工具"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    {"id": "f05", "question": "LangGraph 是谁推出的？",
     "reference": "LangChain 团队", "keywords": ["LangChain"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    {"id": "f06", "question": "LangGraph 用什么结构描述执行流程？",
     "reference": "图结构，节点代表操作、边代表流转方向", "keywords": ["图"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    {"id": "f07", "question": "常见的向量数据库有哪些？",
     "reference": "FAISS、Chroma、Pinecone", "keywords": ["FAISS"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    {"id": "f08", "question": "向量数据库的作用是什么？",
     "reference": "把文本转成向量存储，并支持相似度检索", "keywords": ["向量", "检索"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    {"id": "f09", "question": "LangChain 的三大核心概念是什么？",
     "reference": "Chain、Agent、RAG", "keywords": ["Chain", "Agent", "RAG"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    {"id": "f10", "question": "LangGraph 支持哪两种控制流？",
     "reference": "条件分支和循环", "keywords": ["循环"],
     "expect_source": "test_doc.txt", "type": "fact", "should_refuse": False},
    # —— 跨段落问答（要拼接多处信息）——
    {"id": "m01", "question": "RAG 为什么能减少幻觉？",
     "reference": "因为先检索相关文档片段，再让模型基于这些片段回答，而不是凭空生成",
     "keywords": ["检索"], "expect_source": "test_doc.txt", "type": "multi_hop", "should_refuse": False},
    {"id": "m02", "question": "RAG 和向量数据库是什么关系？",
     "reference": "向量数据库是 RAG 的核心组件，负责存向量并做相似度检索，供 RAG 检索阶段使用",
     "keywords": ["向量"], "expect_source": "test_doc.txt", "type": "multi_hop", "should_refuse": False},
    {"id": "m03", "question": "LangGraph 和 LangChain 是什么关系，前者解决什么？",
     "reference": "LangGraph 是 LangChain 团队的扩展框架，用图结构构建有状态、可循环的 Agent 流程",
     "keywords": ["图"], "expect_source": "test_doc.txt", "type": "multi_hop", "should_refuse": False},
    {"id": "m04", "question": "一个 RAG 系统回答问题大致经过哪几步？",
     "reference": "先把文本向量化存进向量库，提问时检索相关片段，再让模型基于片段生成回答",
     "keywords": ["检索"], "expect_source": "test_doc.txt", "type": "multi_hop", "should_refuse": False},
    {"id": "m05", "question": "Agent 和 Chain 有什么区别？",
     "reference": "Chain 是固定串联的步骤流程；Agent 能自主决定调用哪些工具，更灵活",
     "keywords": ["工具"], "expect_source": "test_doc.txt", "type": "multi_hop", "should_refuse": False},
]

OUT = Path("eval_set.json")


def validate(dataset: list[dict]):
    """跑前先校验：字段齐不齐、id 有没有重复。评测集脏了，后面全白测。"""
    ids = set()
    for row in dataset:
        missing = [k for k in SCHEMA_FIELDS if k not in row]
        assert not missing, f"{row.get('id','?')} 缺字段：{missing}"
        assert row["id"] not in ids, f"id 重复：{row['id']}"
        ids.add(row["id"])
    return True


if __name__ == "__main__":
    validate(EVAL_SET)
    OUT.write_text(json.dumps(EVAL_SET, ensure_ascii=False, indent=2), encoding="utf-8")

    n_fact = sum(r["type"] == "fact" for r in EVAL_SET)
    n_multi = sum(r["type"] == "multi_hop" for r in EVAL_SET)
    print(f"已写入 {OUT}，共 {len(EVAL_SET)} 条：事实 {n_fact} / 跨段落 {n_multi}")
    print("✅ schema 校验通过。Day20 继续补拒答 + 引用题，合并到 25 条后接 RAGAS。")

# ----------------------------------------------------------
# 小结：
# - 评测集 = RAG 的回归用例库，schema 一旦定好就别乱改（下游全靠它）。
# - 存 JSON 而不是写死在代码里：能版本管理、能被 day17/18/RAGAS/pytest 共用。
# - 造题要"按题型覆盖"：事实题测基本盘，跨段落题测召回全不全 + 会不会整合。
#
# 动手练习：再加 5 条"问法刁钻"的（同义换词、口语化、含错别字），
#          看检索还稳不稳——这些最能暴露召回短板。
# ----------------------------------------------------------
