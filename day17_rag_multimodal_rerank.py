"""
Day 17 · 多模态读图 + reranker 重排（RAG 进阶收尾）
==========================================================
测试工程师转 AI 应用开发

阶段 1 收尾，补两块真实场景常用、面试也常问的能力：
1. 多模态：用户的资料常是图片/扫描件 PDF（截图、拍照合同），纯文本 loader 读不了，
   要用"视觉模型"把图看懂——要么 OCR 出文字，要么直接理解图意。
2. reranker：向量检索为了召回率会多召回（如 top8），但塞给模型太多块=噪声+费 token。
   reranker 是个更准（也更慢）的小模型，对召回的候选两两精排，只留最相关的 top3。
   套路："向量粗召回（快、广）→ reranker 精排（准、窄）"，是工业级 RAG 的标配。

知识点：
1. 视觉模型的调用方式（把图片转 base64，按多模态 message 传给支持视觉的模型）
2. ContextualCompressionRetriever + CrossEncoderReranker：召回后重排
3. 为什么要"粗召回 + 精排"两段式

依赖：reranker 用 bge-reranker（魔搭下：snapshot_download('BAAI/bge-reranker-base')）
注意（langchain 1.x）：
  - ContextualCompressionRetriever / CrossEncoderReranker 迁到 langchain_classic.retrievers
  - HuggingFaceCrossEncoder 在 langchain_community.cross_encoders
==========================================================
"""

import os
import base64
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from common import get_embeddings, RERANKER_MODEL_PATH, ZH_SEPARATORS


# ============ 第一部分：多模态读图 ============
def ask_image(image_path: str, question: str) -> str:
    """把一张图片连同问题发给视觉模型，返回模型对图的理解/OCR 结果。

    注意：deepseek-chat 不支持图片。需换一个视觉模型，例如：
      - 阿里 qwen-vl-max（base_url=https://dashscope.aliyuncs.com/compatible-mode/v1）
      - 或任意 OpenAI 兼容的视觉模型
    这里用环境变量配置，跑不通就先看下面 reranker 部分。"""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    vlm = ChatOpenAI(
        model=os.getenv("VLM_MODEL", "qwen-vl-max"),
        api_key=os.getenv("VLM_API_KEY", os.getenv("DEEPSEEK_API_KEY")),
        base_url=os.getenv("VLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    )
    # 多模态 message：一条 human 消息里同时带 文字 + 图片(data URL)
    msg = [{"role": "user", "content": [
        {"type": "text", "text": question},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
    ]}]
    return vlm.invoke(msg).content


# ============ 第二部分：召回 + reranker 精排 ============
def build_rerank_retriever():
    """先建普通向量检索器（粗召回 k=8），再套一层 reranker 精排到 top3。"""
    from langchain_community.cross_encoders import HuggingFaceCrossEncoder
    from langchain_classic.retrievers import ContextualCompressionRetriever
    from langchain_classic.retrievers.document_compressors import CrossEncoderReranker

    with open("test_doc.txt", encoding="utf-8") as f:
        text = f.read()
    docs = [Document(page_content=text, metadata={"source": "test_doc.txt"})]
    # chunk_size 取 160：太碎（如 80）会把跨句答案切散，reranker 也救不回来
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=160, chunk_overlap=30, separators=ZH_SEPARATORS,
    ).split_documents(docs)

    embeddings = get_embeddings()
    vs = FAISS.from_documents(chunks, embeddings)
    base = vs.as_retriever(search_kwargs={"k": 8})        # 粗召回：宁多勿漏

    cross_encoder = HuggingFaceCrossEncoder(model_name=RERANKER_MODEL_PATH)
    compressor = CrossEncoderReranker(model=cross_encoder, top_n=3)  # 精排留 top3
    return base, ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=base)


if __name__ == "__main__":
    query = "向量数据库在 RAG 里干嘛"

    print("===== reranker 重排对比 =====")
    try:
        base, rerank_ret = build_rerank_retriever()
        print(f"\n问题：{query}")
        print("\n【纯向量粗召回 top8】")
        for d in base.invoke(query):
            print(" -", d.page_content.strip()[:40])
        print("\n【reranker 精排后 top3】（更相关的排前面、砍掉噪声）")
        for d in rerank_ret.invoke(query):
            print(" -", d.page_content.strip()[:40])
    except Exception as e:
        print(f"(reranker 模型没下好就会报错，先 snapshot_download bge-reranker-base) {e}")

    print("\n===== 多模态读图（需配视觉模型）=====")
    img = "sample_scan.png"   # 放一张截图/扫描件到目录里
    if os.path.exists(img):
        print(ask_image(img, "这张图里写了什么？请提取关键信息"))
    else:
        print(f"(没找到 {img}，放一张图片再跑这部分)")

# ----------------------------------------------------------
# 小结：
# - 多模态：本质是"把图片编码进 message 一起发给会看图的模型"，纯文本模型不行。
#   场景：扫描件合同、报表截图、手写票据——文本 loader 读不了的，交给视觉模型。
# - reranker：粗召回(向量, 快但糙) + 精排(cross-encoder, 准但慢) 两段式。
#   何时需要：候选多、对精度要求高、token 预算紧时；小库简单问答可以不上。
#
# 阶段 1 验收（自己口述一遍）：
#   "RAG 答错，先分是【检索没召回相关内容】还是【召回了但生成乱编】——
#    前者调 chunk/混合检索/查询改写/reranker，后者调 prompt/换模型/加忠实度约束。"
#
# 动手练习：把 reranker 的 top_n 从 3 调到 1，看召回是否漏掉跨段落答案。
# ----------------------------------------------------------
