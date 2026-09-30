# 2.1 文档加载与切分：资料如何进入系统

[全书目录](../../README.md) · [上一章 1.8](../../part1-foundations/1.8-cli-chatbot/README.md) · [下一章 2.2](../2.2-embed-retrieve/README.md)

- **目标**：把文件读成 Document，再切成适合检索的片段。
- **前置**：无。
- **环境**：离线，不调用模型。
- **命令**：`python tools/run_chapter.py 2.1 load_split.py`

## 问题

知识问答的第一步不是问模型，而是把资料整理成程序能处理的片段。整篇塞进请求会增加成本，关键事实容易被淹没；切得不好又会切断条件，让片段失去意义。

## 概念

- **Document**：`page_content` 是正文，`metadata` 保存来源、页码、标题等。元数据要一直保留到回答引用。
- **加载器**：按文件格式把文件读成 Document。txt 用 `open()` 即可，PDF、CSV 等用对应的 loader。
- **切分器**：把长正文切成片段。`chunk_size` 是片段最大长度；`chunk_overlap` 让相邻片段共享交界内容，避免边界处的事实被截断，重叠过大则产生重复。
- **递归切分**：按分隔符优先级（段落 > 换行 > 句号 > 逗号 > 空格 > 单字）逐级尝试，尽量在自然边界切开。

## 流程

1. 读取长文章 `chapters/shared-data/long_article.txt`（约 8.7KB，2.7、2.8 也用它）。
2. 包成 Document，记录来源。
3. 用递归切分器切成片段（`chunk_size=120`，`chunk_overlap=20`）。
4. 打印每个片段的序号、字数和内容，检查边界与来源。

## 代码导读

| 文件 | 内容 |
|---|---|
| [load_split.py](load_split.py) | 最短路径：`open` → Document → 递归切分 → 打印。先读它。 |
| [load_split_formats.py](load_split_formats.py) | `load_and_split(path)`：按扩展名选加载器（pdf、docx、csv、json、md、html、代码），先按结构切，再统一细切。 |

## 练习

1. 运行 `load_split.py`，先预测片段数量。再把 `chunk_size` 改为 60、300，`chunk_overlap` 改为 0、60，观察数量、重复内容和片段完整度。
2. 在文章里找一个横跨两个片段的事实（条件在前一片段末尾，结论在下一片段开头），判断切分后单个片段是否还能回答它。
3. 运行 `python tools/run_chapter.py 2.1 load_split_formats.py`，对比 txt 与 md 的切分：md 片段的 `metadata` 带有所属标题。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与边界

- 文章路径由 `common.LONG_DOC` 提供，与工作目录无关。第 2 篇后面的问答类章节改用短文档 `test_doc.txt`（评测集的问题基于它），见 [shared-data](../../shared-data/README.md)。
- PDF、Word 等格式有各自依赖；读取成功不代表扫描件文字被识别，无文字层的 PDF 得到的是空文本。
- 片段数量和边界只反映当前参数。切得好不好，要靠后续的检索评测（2.4、第 3 篇）判断。
