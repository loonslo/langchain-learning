# Day54 · 用 RRF 融合两路文档排名

Day53 能判断最终答案和来源，却看不到检索阶段的排名。今天不直接宣称“纯向量检索已经被修复”，而是先完成混合检索中的一个确定性核心：

> 输入两路或多路已经排好序的 Document 列表，使用 RRF 奖励多路共同命中的文档，输出统一、去重的排名。

当前项目尚未实现关键词检索器，也没有把 RRF 接进 bootstrap.py 和 CLI。今天测试证明的是融合函数，不是端到端检索质量提升。

## 1. 先从 Day53 的边界出发

完成 [workbook.md](workbook.md) 第 0 节，先确认：

- evaluate 接收的是最终 SupportAnswer，不是检索排名。
- 当前代码没有生成一条真实关键词排名。
- 今天 reciprocal_rank_fusion 的输入是排名列表，不是用户问题。

如果这三件事没有分清，容易误以为一个排序函数等于完整混合检索系统。

## 2. 今天新增的文件

| 项目路径 | 变更 | 今天承担的职责 |
|---|---|---|
| src/customer_support/retrieval.py | 新增 | 根据名次融合多路 Document 排名 |
| tests/test_retrieval.py | 新增 | 验证共同命中文档优先并去重 |

Day54 结束后的完整结构：

~~~text
.env.example                         # 继承 Day51
data/eval_cases.json                 # 继承 Day53
data/knowledge/customer_faq.md       # 继承 Day51
data/knowledge/refund.md             # 继承 Day52
data/knowledge/shipping.md           # 继承 Day52
pyproject.toml                       # 继承 Day51
src/customer_support/__init__.py     # 继承 Day51
src/customer_support/assistant.py    # 继承 Day51
src/customer_support/bootstrap.py    # 继承 Day51
src/customer_support/cli.py          # 继承 Day51
src/customer_support/evaluation.py   # 继承 Day53
src/customer_support/ingestion.py    # 继承 Day52
src/customer_support/knowledge.py    # 继承 Day51
src/customer_support/retrieval.py    # 本日新增
src/customer_support/settings.py     # 继承 Day51
tests/test_assistant.py              # 继承 Day51
tests/test_evaluation.py             # 继承 Day53
tests/test_ingestion.py              # 继承 Day52
tests/test_knowledge.py              # 继承 Day51
tests/test_retrieval.py              # 本日新增
~~~

## 3. 写代码前手算 RRF

先在 workbook.md 第 1 节计算：

~~~text
排名 A：[a, b]
排名 B：[b, c]
~~~

每个文档在每条排名中的贡献为：

~~~text
1 / (60 + 名次)
~~~

b 被两路找到，因此获得两次贡献；a 和 c 各获得一次。RRF 只使用名次，不直接相加向量相似度与关键词分数这两种不同量纲。

先预测最终顺序，再看测试答案。

## 4. 跟踪融合函数

打开 [retrieval.py](src/customer_support/retrieval.py)，跟踪：

~~~text
多路排名
  → 用 chunk_id 识别同一文档
  → 按每路名次累加贡献
  → 按总分降序排列
  → 相同分数用 key 保持确定性
  → 截取 limit
  → 返回去重后的 Documents
~~~

两个字典职责不同：

- scores 保存每个 chunk_id 的累计分数。
- documents 保存 chunk_id 对应的 Document 对象。

缺少 chunk_id 会直接失败，因为函数无法可靠判断两个 Document 是否代表同一块内容。这个 metadata 来自 Day52 的摄取组件。

## 5. 运行测试并验证预测

打开 [test_retrieval.py](tests/test_retrieval.py)，先写下期望顺序，然后运行累计测试：

~~~powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 54
cd .build\day54\customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
..\..\..\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
~~~

测试中的 b 同时出现在两路，最终只出现一次并排在第一。

## 6. 主动破坏“累加”

按照 workbook.md 第 3 节，暂时把：

~~~python
scores.get(key, 0.0) + 1 / (60 + rank)
~~~

改成只保留本次贡献：

~~~python
1 / (60 + rank)
~~~

先手算新结果，再运行测试。恢复代码后重新跑绿。

这个实验展示的不是某个框架语法，而是融合算法的核心业务规则：多路共同命中必须积累证据。

## 7. 今天的真实调用关系

当前关系是：

~~~text
test_retrieval.py ──调用──> reciprocal_rank_fusion

bootstrap.py ──仍调用──> Day51 单路 build_retriever
CLI          ──尚未调用──> reciprocal_rank_fusion
~~~

因此今天唯一能直接证明的结论是：

> 给定多路已排序文档，当前 RRF 函数能够奖励共同命中并输出去重排名。

以下结论都还不能证明：

- 已经实现关键词检索。
- 已经把语义与关键词检索接进真实问答。
- 真实评测集的分数已经提升。
- 混合检索对所有问题都有帮助。

## 8. 完整混合检索还缺什么

要把今天的函数变成产品能力，至少还需要：

~~~text
用户问题
  ├──语义检索──> 排名 A
  └──关键词检索──> 排名 B
                    │
                    ▼
                   RRF
                    │
                    ▼
             assistant / evaluation
~~~

之后还要用 Day53 的评测思想比较改动前后结果。没有这条端到端证据，就不能把“函数测试通过”说成“检索质量提升”。

## 9. 为下一天留下问题

今天结束前，把“那发货后呢？”单独交给当前 ask(question) 思考：

- 单独一句是否包含完整意图？
- ask 是否收到历史对话？
- 如果上一句是“我想修改地址”，系统需要保留什么？

把观察写进 workbook.md 第 6 节。这会自然引出后续的多轮会话，而不是第二天才突然宣布“系统没有记忆”。

## 10. 完成标准

完成 workbook.md，并能解释：

1. RRF 的输入为什么是排名列表而不是用户问题？
2. b 为什么排第一并且只出现一次？
3. chunk_id 在融合中有什么作用？
4. 为什么不同检索器的原始分数不直接相加？
5. 今天的函数与完整混合检索系统之间还差哪些组件和证据？
