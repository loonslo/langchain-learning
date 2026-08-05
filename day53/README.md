# Day53 · 把业务预期变成可重复执行的评测

Day52 结束时，你只能手工列出“问题、期望答案、期望来源”。代码一旦变化，没有程序自动重跑并比较这些业务预期。

今天实现的准确范围是：

> 用 JSON 保存业务问题及验收条件；评测器调用 Assistant.ask，并分别判断答案、引用和最终通过状态。

今天的单元测试使用 FakeAssistant，重点验证评测规则本身。它没有证明真实 embedding 和真实 LLM 已在所有用例上通过。

## 1. 先复现手工检查的局限

先完成 [workbook.md](workbook.md) 第 0 节：

- 昨天手工判断了哪些结果？
- 这些判断是否被 pytest 自动保存和重跑？
- 答案对但引用错应该怎样算？

只有先明确这个缺口，data/eval_cases.json 才不会看起来像“又多写了一份配置”。

## 2. 今天新增的文件

| 项目路径 | 变更 | 今天承担的职责 |
|---|---|---|
| data/eval_cases.json | 新增 | 保存问题、答案要点、期望来源和拒答要求 |
| src/customer_support/evaluation.py | 新增 | 加载用例并分层判断结果 |
| tests/test_evaluation.py | 新增 | 证明正确答案配错误引用仍然失败 |

Day53 结束后的完整结构：

~~~text
.env.example                         # 继承 Day51
data/eval_cases.json                 # 本日新增
data/knowledge/customer_faq.md       # 继承 Day51
data/knowledge/refund.md             # 继承 Day52
data/knowledge/shipping.md           # 继承 Day52
pyproject.toml                       # 继承 Day51
src/customer_support/__init__.py     # 继承 Day51
src/customer_support/assistant.py    # 继承 Day51
src/customer_support/bootstrap.py    # 继承 Day51
src/customer_support/cli.py          # 继承 Day51
src/customer_support/evaluation.py   # 本日新增
src/customer_support/ingestion.py    # 继承 Day52
src/customer_support/knowledge.py    # 继承 Day51
src/customer_support/settings.py     # 继承 Day51
tests/test_assistant.py              # 继承 Day51
tests/test_evaluation.py             # 本日新增
tests/test_ingestion.py              # 继承 Day52
tests/test_knowledge.py              # 继承 Day51
~~~

## 3. 先把 JSON 翻译成产品要求

打开 [eval_cases.json](data/eval_cases.json)，不要马上打开 evaluation.py。

每条记录回答五个问题：

| 字段 | 产品含义 |
|---|---|
| id | 哪条用例失败了 |
| question | 用户怎样提问 |
| keywords | 非拒答时答案必须包含哪些最低要点 |
| sources | 必须返回哪些来源 |
| refuse | 这道题是否应该拒答 |

先在 workbook.md 第 1 节预测两种结果：正确文字配错误引用，以及正确拒答配错误来源。预测后再读实现。

## 4. 跟踪一条评测用例

打开 [evaluation.py](src/customer_support/evaluation.py)，按下面的顺序跟踪：

~~~text
JSON
  → load_cases
  → list[EvalCase]
  → evaluate
  → assistant.ask(question)
  → answer_ok
  → citation_ok
  → passed = answer_ok and citation_ok
~~~

Assistant 是 Protocol，只要求对象有 ask 方法。因此真实客服助手和测试 FakeAssistant 都可以交给 evaluate。

这里特意把 answer_ok 与 citation_ok 分开。否则报告只显示“失败”，你无法判断应该检查生成内容还是来源链路。

## 5. 用一个反例理解评测器

阅读 [test_evaluation.py](tests/test_evaluation.py)：

- FakeAssistant 返回的答案含有 3–5。
- 测试用例期望 wrong.md。
- FakeAssistant 实际返回 refund.md。

先手算 answer_ok、citation_ok 和 passed，再运行测试。

还原 Day53 并运行累计测试：

~~~powershell
cd D:\workspace\langchain-learning
.\.venv\Scripts\python.exe tools\materialize_day.py 53
cd .build\day53\customer-support
$env:PYTHONDONTWRITEBYTECODE="1"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
..\..\..\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=.pytest-tmp -q
~~~

然后按 workbook.md 第 3 节暂时让 passed 只依赖 answer_ok。测试应该阻止这种错误规则。恢复后重新跑绿。

## 6. 今天的真实调用关系

当前主要关系是：

~~~text
test_evaluation.py
  ├──创建 FakeAssistant
  └──调用 evaluate

CLI ──没有自动调用──> evaluate
~~~

这意味着今天证明了“评测规则可执行”，没有证明“真实客服助手已经通过整个数据集”。如果没有真实运行证据，不要把后者写进项目介绍。

## 7. 评测集不是答案真理

当前 keywords 只是最低限度的字符串检查：

- 包含关键词不代表整句话没有错误。
- 没包含完全相同的文字，也不一定代表语义错误。
- 两条用例远远不能代表真实用户分布。

所以今天能证明分层评测机制的行为，不能证明完整语义质量。

## 8. 在结束前发现 Day54 的问题

完成 workbook.md 第 5 节，区分两个阶段：

~~~text
检索阶段：哪些 Document 被找到，排名怎样
回答阶段：最终文字和来源是否符合要求
~~~

当前 evaluate 只接收最终 SupportAnswer，不报告正确文档排在第几名。对于精确政策名、业务缩写或商品编号，语义排序也不保证一定把包含精确词的资料排在最前。

Day54 将学习一个更小、更准确的能力：当你已经有两路文档排名时，如何把它们融合。这个观察不等于已经证明真实向量检索失败，也不等于已经有关键词检索器。

## 9. 今天能证明与不能证明的事

能证明：

- 业务问题可以保存为结构化用例。
- 答案与引用可以分开判断。
- 正确文字配错误引用不会通过。

不能证明：

- keywords 等于完整语义评测。
- 当前真实模型通过全部用例。
- 检索排名本身是正确的。

## 10. 完成标准

完成 workbook.md，并能解释：

1. Day52 的手工检查为什么无法防止回归？
2. EvalCase 五个字段分别表达什么？
3. answer_ok 与 citation_ok 为什么分开？
4. FakeAssistant 帮助测试了什么，又没有测试什么？
5. 最终答案评测为什么不能代替检索排名分析？
