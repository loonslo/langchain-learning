import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# 1. 加载 + 切割（沿用 Day 8 的方式）
with open("test_doc.txt", encoding="utf-8") as f:
    text = f.read()

docs = [Document(page_content=text, metadata={"source": "test_doc.txt"})]

splitter = RecursiveCharacterTextSplitter(
    chunk_size=50,
    chunk_overlap=10,
    separators=["\n\n", "\n", "。", "，", " ", ""]
)
chunks = splitter.split_documents(docs)
print(f"切割后共 {len(chunks)} 块\n")

# 2. 加载 embedding 模型（首次运行自动下载，约100MB）
embeddings = HuggingFaceEmbeddings(model_name=r"C:\Users\so\.cache\modelscope\hub\models\BAAI\bge-small-zh-v1___5")# 看看一段文字变成什么样的向量
vec = embeddings.embed_query(chunks[0].page_content)
print(f"向量维度：{len(vec)}")
print(f"前5个数字：{vec[:5]}\n")

# 3. 所有 chunk 转向量，存入 FAISS
vectorstore = FAISS.from_documents(chunks, embeddings)


query = "为这个句子生成表示以用于检索相关文章：RAG 是什么"
# 4. 语义检索：输入问题，找最相关的 chunk
for query in ["RAG 是什么", "LangGraph 有什么用", "怎么存储向量"]:
    print(f"\n========== 查询：{query} ==========")
    results = vectorstore.similarity_search(query, k=4)
    for i, doc in enumerate(results):
        print(f"[{i + 1}] {doc.page_content}")
