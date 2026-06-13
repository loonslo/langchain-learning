from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 加载文档
loader = TextLoader("test_doc.txt", encoding="utf-8")
docs = loader.load()

print(f"加载了 {len(docs)} 个文档")
print(f"文档内容预览：{docs[0].page_content[:100]}")
print(f"文档元数据：{docs[0].metadata}")

# 2. 切割文档
splitter = RecursiveCharacterTextSplitter(
    chunk_size=20,
    chunk_overlap=10,
    separators=["\n\n", "\n", "。", "，", " ", ""]
)

chunks = splitter.split_documents(docs)

print(f"\n切成了 {len(chunks)} 块\n")
for i, chunk in enumerate(chunks):
    print(f"--- 块 {i+1} (长度{len(chunk.page_content)}) ---")
    print(chunk.page_content)
    print()