"""
Day 11 · LLM 原理认知（固本收尾）
==========================================================
测试工程师转 AI 应用开发

前 9 天都在"用"模型。这节补一层认知：模型内部大致怎么回事。
不深究数学，只要能在面试里讲清这几个概念、知道幻觉为什么发生就够了。

知识点（都是【了解】级，能讲清即可，不用自己实现）：
1. token：模型处理文本的最小单位（关系到成本和上下文长度）
2. embedding：为什么向量能算"语义相似"
3. attention：一句话理解模型怎么"关注"上下文
4. 为什么会幻觉：模型本质是"预测下一个最可能的 token"，不是查数据库

下面用几个小演示帮助理解，不是要你手写模型。
==========================================================
"""

import numpy as np
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()
MODEL_PATH = r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-small-zh-v1___5"


# ---------- 1. token：文本是按 token 处理的，不是按字 ----------
# 模型按 token 计费、上下文长度也按 token 算。粗略地说，1 个中文字≈1-2 token。
# 真实分词依赖各模型的 tokenizer，这里只给直观感受。
text = "RAG 是检索增强生成"
print(f"文本：{text}")
print(f"字符数：{len(text)}，粗略 token 估算：约 {int(len(text) * 1.5)} 个\n")


# ---------- 2. embedding：为什么向量能算语义 ----------
# 把词变成向量，算余弦相似度：语义越近，值越高。这就是 RAG 检索的底层原理（Day8 用过）。
emb = HuggingFaceEmbeddings(model_name=MODEL_PATH)

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
# 小结（面试能讲清就够，不用动手实现）：
# - token 是计费和上下文长度的单位；embedding 让"语义相似"可计算
# - attention 让模型按相关性关注上下文；幻觉源于"预测下一个 token"的本质
# - 这些都是【了解】层：知道是什么、为什么，别陷进数学细节
#
# 到这里"固本"收尾，下一步进入 RAG 进阶（Day11 起）。
# ----------------------------------------------------------
