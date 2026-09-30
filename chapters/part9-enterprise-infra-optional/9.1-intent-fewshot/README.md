# 9.1 Few-shot 意图识别：先统一业务类别

[全书目录](../../README.md) · [上一章 8.10](../../part8-ai-quality-optional/8.10-production-feedback-loop/README.md) · [下一章 9.2](../9.2-slot-filling/README.md)

- **目标**：分类必须落在有限的意图枚举里：用 few-shot 示例引导模型，用严格校验兜底；模型无法判断时输出 `unknown`，不猜业务动作。
- **前置**：8.10（其累积代码）。
- **环境**：离线测试，真实服务另验；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py enterprise 9.1-intent-fewshot`，进入 `.build/enterprise/9.1-intent-fewshot/enterprise-support` 后运行 `python -m pytest -q`

## 问题

客服系统需要知道用户是在问政策还是查订单。给模型几个例子有助于表达任务，但程序还需要有限类别和严格校验，未知请求应保留未知状态。

## 概念

Few-shot 是少量示例；Intent 是允许意图的枚举；IntentDecision 固定分类结果。分类表示理解用户目标，业务授权还在后续层。

## 流程

1. 构建带示例的分类提示。
2. 取得分类输出。
3. parse_intent_payload 校验字段与类别。
4. 模型无法判断时输出 `unknown`，由工作流转人工；枚举之外的类别（如 `make_payment`）会被 `parse_intent_payload` 拒绝并抛出 `ValueError`，不进入任何业务分支。

## 本章交付

- `intent.py`：few-shot prompt 与模型输出的 JSON 契约校验。
- `contracts.py`：后续工作流共用的意图、槽位和响应类型。
- `tests/test_intent.py`：验证合法意图、未知意图和字段缺失都被正确处理。

## 代码导读

intent.py 先读 build_intent_prompt，再读 parse_intent_payload；contracts.py 提供后续共享的类型。

实现文件：

- [contracts.py](src/enterprise_support/contracts.py)
- [intent.py](src/enterprise_support/intent.py)

## 练习

准备一个订单问题、一个政策问题和一个类别之外的问题，先人工预测，再核对解析器是否允许模型随意添加类别。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py enterprise 9.1-intent-fewshot
cd .build/enterprise/9.1-intent-fewshot/enterprise-support
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

离线测试验证分类契约，未测真实模型的分类准确率；示例不足时应补充评测覆盖。

few-shot 是改善分类一致性的上下文示例，不是训练，也不能替代评测集。
