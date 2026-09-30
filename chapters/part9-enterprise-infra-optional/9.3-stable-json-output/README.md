# 9.3 稳定 JSON 边界：解析失败也有明确出口

[全书目录](../../README.md) · [上一章 9.2](../9.2-slot-filling/README.md) · [下一章 9.4](../9.4-intent-workflow/README.md)

- **目标**：模型返回的 JSON 不能直接 `json.loads()` 后使用：只接受对象、声明字段和正确类型；格式错误最多受控修复一次，仍失败就显式降级。
- **前置**：9.2（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.3-stable-json-output`，进入 `.build/enterprise/9.3-stable-json-output/enterprise-support` 后运行 `python -m pytest -q`

## 问题

模型有时把 JSON 包在代码块里，有时增加解释文字。应用不能在解析失败时继续猜字段，需要规定能接受的形式及有限修复行为。

## 概念

JsonSchema 规定字段与类型；解析获取对象；校验判断合法性；受控修复只在允许范围内执行。结构有效仍不等于字段内容符合业务事实。

## 流程

1. 识别允许的 JSON 形式。
2. 提取对象。
3. validate_json 检查字段。
4. 原输出校验失败时才调用一次修复，修复结果再校验一遍。
5. 仍失败则返回显式错误。

## 本章交付

- `structured_json.py`：提取 fenced JSON、schema 校验和一次修复策略。
- `tests/test_structured_json.py`：覆盖有效 JSON、额外字段、修复耗尽、不允许的前后废话，以及合法输出不触发修复。

## 代码导读

structured_json.py 先读 JsonSchema 和 StructuredOutputError，再读 _object_from_text、validate_json 与 parse_model_json。

实现文件：

- [structured_json.py](src/enterprise_support/structured_json.py)

## 练习

准备多余字段、错误类型和代码块三种输出，预测哪些能接受；让修复仍失败，检查是否停止而不是无限调用。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.3-stable-json-output
cd .build/enterprise/9.3-stable-json-output/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

离线校验不验证具体提供方的结构化接口，模型接入需要另行确认。

修复器也是一次模型调用，必须计入成本、trace 和失败率；不能写无限“重试直到能解析”。
