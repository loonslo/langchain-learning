# Day92 · 大模型稳定输出 JSON

“提示模型返回 JSON”不等于可以直接 `json.loads()`。今天建立输出边界：只接受对象、
只接受声明字段、类型正确才进入业务；格式错误时最多调用一次受控修复，失败就显式降级。

## 今日交付

- `structured_json.py`：提取 fenced JSON、schema 校验和一次修复策略。
- `tests/test_structured_json.py`：覆盖有效 JSON、额外字段、修复耗尽和不允许的前后废话。

## 今日边界

修复器也是一次模型调用，必须计入成本、trace 和失败率；不能写无限“重试直到能解析”。
