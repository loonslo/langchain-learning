"""
capstone/app_streamlit.py · 简易 Web 界面（演示用）
==========================================================
整合给"非技术用户"看的入口：上传文档 + 提问 + 看答案。
依赖：pip install streamlit
运行：streamlit run capstone/app_streamlit.py
==========================================================
"""

import streamlit as st
import config as C
from knowledge_base import KnowledgeBase

st.set_page_config(page_title="企业知识库 Agent", page_icon="📚")
st.title("📚 企业知识库 Agent")


@st.cache_resource
def load_kb():
    return KnowledgeBase().build()


# 上传文档（存进 docs/，重建库）
up = st.file_uploader("上传文档（txt/md/pdf）", type=["txt", "md", "pdf"])
if up:
    (C.DOCS_DIR / up.name).write_bytes(up.getbuffer())
    st.success(f"已保存 {up.name}，点下方重建知识库")
    if st.button("重建知识库"):
        KnowledgeBase().build(rebuild=True)
        st.cache_resource.clear()
        st.success("已重建")

kb = load_kb()
q = st.text_input("问点什么：")
if q:
    with st.spinner("检索 + 生成中…"):
        st.write(kb.answer(q))
