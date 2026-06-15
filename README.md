# LangChain 学习记录

> 从零基础转型 AI 应用开发的每日代码记录。每个文件 = 某一天学到的一个核心概念。
> 配套计划与笔记在 `daily-notebook` vault：完整大纲 / 每日任务清单 / 学习笔记。

## 环境

```bash
pip install langchain langchain-openai langchain-community python-dotenv \
            langchain-text-splitters faiss-cpu pypdf langchain-huggingface streamlit
```

`.env` 里配置（用 DeepSeek，兼容 OpenAI 格式）：

```
DEEPSEEK_API_KEY=你的key
```

## 按顺序读（每天加一个概念）

> "学到什么" 一列留给自己填——用一句话说清这天的收获，说不清的就是还没学透。

| 顺序 | 文件 | 概念 | 一句话学到什么（✍️ 自己填） |
|------|------|------|------------------------------|
| Day 1 | `day01-1.py` | 基础调用 + Prompt + LCEL 管道 | |
| Day 1 | `day01-2.py` | argparse 做命令行工具（翻译/解释） | |
| Day 2 | `day02_translator.py` | 翻译器（system/human 角色） | |
| Day 2 | `day02_code_explainer.py` | 代码解释器 | |
| Day 2 | `day02-1.py` | 结构化输出（with_structured_output + Pydantic） | |
| Day 2 | `day02-2.py` | 对话记忆（RunnableWithMessageHistory） | |
| Day 3 | `day03-1.py` | 工具调用基础（bind_tools + tool_calls） | |
| Day 3 | `day03-2.py` | 多角色对话 + 记忆 + 历史落盘 | |
| Day 4 | `day04.py` | 工具 + 记忆结合进同一对话循环 | |
| Day 5 | `day05-1.py` | 文档加载 + 切割（RecursiveCharacterTextSplitter） | |
| Day 5 | `day05-2.py` | Embedding + FAISS 向量检索 | |
| Day 6 | `day06-1.py` | 完整 RAG 链（inline 版） | |
| Day 6 | `day06_2.py` | RAG 模块化（支持 txt/pdf） | |
| Day 7 | `day07.py` | Streamlit 知识库问答（Web 界面） | |

## 辅助文件（非学习内容）

- `tess.py` — 一次性脚本：下载 embedding 模型（bge-small-zh）
- `test_doc.txt` — RAG 用的测试文档

## 学习原则

- 代码按天保留，不合并——保留学习时间线，每个文件可单独跑。
- 重点不是"代码干净"，是"每行为什么这么写说得清"。
