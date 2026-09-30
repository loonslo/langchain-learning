"""
章节 1.7 · LLM 原理认知
==========================================================
前面几章都在"用"模型。本章补一层认知：模型内部大致是怎么回事。
不深究数学，能讲清下面几个概念、知道幻觉为什么发生即可。

知识点（了解即可，不要求自己实现）：
1. token：模型处理文本的最小单位（关系到成本和上下文长度）
2. embedding：为什么向量能算"语义相似"
3. attention：一句话理解模型怎么"关注"上下文
4. 为什么会幻觉：模型本质是"预测下一个最可能的 token"，不是查数据库

下面用几个小演示帮助理解，不需要手写模型。

前置：本地 embedding 模型（下载方法见根目录 README"准备本地 embedding 模型"）
运行：python tools/run_chapter.py 1.7（不调用聊天模型，不需要密钥）
输出：字符数与 token 估算、两组词的相似度，以及 attention 与幻觉的文字说明
==========================================================
"""

import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings

from common import EMBED_MODEL_PATH   # 本地 embedding 模型路径，可用环境变量 EMBED_MODEL_PATH 覆盖


# ---------- 1. token：文本是按 token 处理的，不是按字 ----------
# 模型按 token 计费、上下文长度也按 token 算。粗略地说，1 个中文字≈1-2 token。
# 真实分词依赖各模型的 tokenizer，这里只给直观感受。
text = "RAG 是检索增强生成"
print(f"文本：{text}")
print(f"字符数：{len(text)}，粗略 token 估算：约 {int(len(text) * 1.5)} 个\n")


# ---------- 2. embedding：为什么向量能算语义 ----------
# 把词变成向量，算余弦相似度：语义越近，值越高。这就是 RAG 检索的底层原理（2.2 会正式使用）。
emb = HuggingFaceEmbeddings(model_name=EMBED_MODEL_PATH)

# 余弦相似度, 取值范围 [0, 1], 越接近 1，越相似
def cosine(a, b):
    a, b = np.array(a), np.array(b)
    return a @ b / (np.linalg.norm(a) * np.linalg.norm(b))


v_dog, v_puppy, v_stock = emb.embed_query("狗"), emb.embed_query("小狗"), emb.embed_query("股票")
print(f"'狗' vs '小狗' 相似度：{cosine(v_dog, v_puppy):.3f}（语义近 → 高）")
print(f"'狗' vs '股票' 相似度：{cosine(v_dog, v_stock):.3f}（语义远 → 低）\n")


# ---------- 3. attention（一句话）----------
print("attention：模型生成每个词时，会按相关性'关注'前文里不同的词，"
      "这让它能结合上下文，而不是孤立地看每个词。\n")


# ---------- 4. 为什么会幻觉 ----------
print("幻觉：模型本质是在'预测下一个最可能的 token'，不是查数据库。"
      "没见过准确信息时，它仍会'流畅地编'一个看起来合理的答案——"
      "这正是 RAG（喂真实上下文）和评测（量化幻觉率）重要的原因。")


# ----------------------------------------------------------
# 小结：
# - token 是计费和上下文长度的单位；embedding 让"语义相似"可计算
# - attention 让模型按相关性关注上下文；幻觉源于"预测下一个 token"的本质
# - 这些是认知层内容：知道是什么、为什么，不必陷进数学细节
#
# 下一章 1.8 把前面学的拼成一个小应用；之后进入第 2 篇 RAG，2.2 会正式使用 embedding。
# ----------------------------------------------------------
