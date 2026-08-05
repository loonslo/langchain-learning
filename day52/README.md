# Day52 · 让多份资料进入统一摄取流程

Day52 不先告诉你“昨天的问题答案”。先回到 Day51 的运行证据：当前配置指向一个文件，load_chunks 一次处理一个文件，数据检查只展示一个来源。

今天实现的准确范围是：

> 给定一个知识库目录，按稳定顺序读取其中所有 Markdown，为每个 chunk 保存可追踪的 source_id 和可重复的 chunk_id。

注意：今天新增的是多文档摄取组件。它尚未替换 bootstrap.py 中 Day51 的真实检索链，因此不能说 CLI 已经使用多文档问答。

## 1. 先复现问题，再看新代码

先完成 [workbook.md](workbook.md) 第 0 节。如果 Day51 没有留下记录，就先还原并检查 Day51：

~~~powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 51
~~~

然后比较三份业务资料：

- customer_faq.md
- refund.md
- shipping.md

思考的不是“文件多了”，而是：

- 不同政策能否由不同负责人独立维护？
- 一个 chunk 能否指出自己来自哪个业务来源？
- 同一资料重复摄取后，系统能否认出它仍是同一块内容？

## 2. 今天新增的文件

| 项目路径 | 变更 | 今天承担的职责 |
|---|---|---|
| data/knowledge/refund.md | 新增 | 独立退款政策 |
| data/knowledge/shipping.md | 新增 | 独立配送政策 |
| src/customer_support/ingestion.py | 新增 | 扫描目录、复用单文件切块、补充稳定身份 |
| tests/test_ingestion.py | 新增 | 验证多来源和稳定 ID |

Day52 结束后的完整项目结构：

~~~text
.env.example                         # 继承 Day51
data/knowledge/customer_faq.md       # 继承 Day51
data/knowledge/refund.md             # 本日新增
data/knowledge/shipping.md           # 本日新增
pyproject.toml                       # 继承 Day51
src/customer_support/__init__.py     # 继承 Day51
src/customer_support/assistant.py    # 继承 Day51
src/customer_support/bootstrap.py    # 继承 Day51
src/customer_support/cli.py          # 继承 Day51
src/customer_support/ingestion.py    # 本日新增
src/customer_support/knowledge.py    # 继承 Day51
src/customer_support/settings.py     # 继承 Day51
tests/test_assistant.py              # 继承 Day51
tests/test_ingestion.py              # 本日新增
tests/test_knowledge.py              # 继承 Day51
~~~

## 3. 先预测输出结构

在看 ingestion.py 之前，填写 workbook.md 第 1 节。

每个 Document 已经有 page_content 和 source。多文档管理还需要：

- source_id：表明属于哪个业务文件。
- chunk_id：表明是该来源中的哪块稳定内容。

稳定不是指“永远不变”。相同文件名和相同正文再次摄取时 ID 相同；正文变化时 ID 应随之变化。

## 4. 跟踪 ingest_directory

打开 [ingestion.py](src/customer_support/ingestion.py)，只跟踪一条数据流：

~~~text
目录
  → 找到并按文件名排序所有 Markdown
  → 每个文件复用 Day51 的 load_chunks
  → 添加 source_id
  → 根据来源和正文计算 chunk_id
  → 返回 list[Document]
~~~

这里复用 load_chunks 很重要：Day52 没有复制文件读取与切块逻辑。

空目录立即抛错也是产品行为。空知识库如果静默启动，系统可能把“配置错误”伪装成“所有用户问题都没有答案”。

## 5. 先读测试意图，再运行

打开 [test_ingestion.py](tests/test_ingestion.py)，先预测两个断言：

1. 为什么 source_id 集合至少包含 refund 和 shipping？
2. 为什么连续摄取两次得到的 chunk_id 列表应完全相同？

然后还原 Day52 并运行累计测试：

~~~powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 52
cd .build\day52\customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
..\..\..\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
~~~

累计测试同时覆盖 Day51 的旧规则和 Day52 的新增能力。

## 6. 主动破坏 source_id

按照 workbook.md 第 3 节，临时把 ingestion.py 中的 source_id 固定成 unknown：

1. 运行前预测哪个断言失败。
2. 运行测试并对比实际结果。
3. 恢复代码。
4. 再次运行累计测试。

这个实验模拟的真实问题是：资料虽然被加载了，却失去业务来源身份，后续无法可靠引用、更新或排错。

## 7. 今天的真实调用关系

今天必须主动搜索谁调用 ingest_directory。

当前结论是：

~~~text
test_ingestion.py ──调用──> ingest_directory

bootstrap.py ──仍调用──> Day51 build_retriever(单文件路径)
~~~

因此今天能证明多文档摄取函数可用，但不能证明 CLI 已经检索 refund.md 和 shipping.md。把这个边界写入 workbook.md 第 4 节。

## 8. 在结束前发现 Day53 的问题

完成 workbook.md 第 5 节，手工列出两道业务问题的期望答案和来源，然后问自己：

- 下周改了代码，怎样自动重跑同一批问题？
- 50 道题还能否靠记忆比较？
- 答案正确但来源错误算不算通过？

如果当前 pytest 没有保存并执行这张业务问题表，你就已经得到 Day53 的起点：现在有组件测试，但还没有可重复的业务质量检查。

## 9. 今天能证明与不能证明的事

能证明：

- 目录中的多份 Markdown 可以统一产生 chunks。
- 每个 chunk 有来源身份。
- 相同资料重复摄取时 chunk_id 稳定。

不能证明：

- 真实 CLI 已使用多文档检索。
- 某道用户问题一定找到正确资料。
- 后续改动不会让历史问题质量退步。

## 10. 完成标准

完成 workbook.md，并能解释：

1. Day51 的哪个代码事实限制了多文档？
2. source_id 和 chunk_id 分别解决什么问题？
3. 为什么空目录应该失败？
4. 当前 ingest_directory 的真实调用方是谁？
5. 为什么今天还不能宣称“多文档问答已完成”？
