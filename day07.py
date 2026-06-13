import os
import tempfile
import streamlit as st

from day06_2 import build_retriever, build_rag_chain

st.title("个人知识库问答")

uploaded_file = st.file_uploader("上传文件（.txt 或 .pdf）", type=["txt", "pdf"])

if uploaded_file is not None:
    # 换了新文件才重新建索引，否则复用 session_state 里的 rag_chain
    if st.session_state.get("file_name") != uploaded_file.name:
        suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        with st.spinner("正在建立索引..."):
            retriever = build_retriever(tmp_path)
            st.session_state["rag_chain"] = build_rag_chain(retriever)
            st.session_state["file_name"] = uploaded_file.name

    st.success(f"已加载：{uploaded_file.name}")

    question = st.text_input("输入问题")
    if question:
        with st.spinner("思考中..."):
            answer = st.session_state["rag_chain"].invoke(question)
        st.write(answer)