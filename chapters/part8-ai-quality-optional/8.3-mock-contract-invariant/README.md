# 8.3 Mock、契约与不变量：不同测试保护不同边界

[全书目录](../../README.md) · [上一章 8.2](../8.2-eval-data-engineering/README.md) · [下一章 8.4](../8.4-rag-layered-testing/README.md)

- **目标**：替身验证行为，契约和不变量验证边界。
- **前置**：8.2（其累积代码）。
- **环境**：离线测试；累积项目，先还原再运行。
- **命令**：`python tools/materialize.py quality 8.3-mock-contract-invariant`，进入 `.build/quality/8.3-mock-contract-invariant/ai-testing` 后运行 `python -m pytest -q`

## 问题

模型替身让测试便宜而稳定，但替身永远返回自己预设的字段，可能掩盖接口漂移。我们在行为替身之外，再检查响应契约与不应被破坏的规则。

## 概念

Mock 替换外部依赖；契约固定边界的字段与类型；不变量描述始终应成立的业务关系，例如拒答时不应伪造证据。

## 流程

1. 取得真实形状的响应。
2. validate_chat_response 校验结构。
3. assert_invariants 校验业务关系。
4. 把失败归到结构或行为边界。

```text
旗舰后端 ChatResponse（7.8 / step2）→ validate_chat_response → assert_invariants → 测试结果
```

## 衔接与新增

章节 8.2 产出结构化评测输入；章节 8.3 给旗舰后端（7.8 / step2）的 `/chat` 响应建立稳定契约，后续 RAG 评测和 E2E 测试复用它。

**本章新增**

| 文件 | 状态 | 作用 |
|---|---|---|
| `src/ai_testing/contracts.py` | 新增 | 校验字段结构与拒答/工单不变量 |
| `tests/test_contracts.py` | 新增 | 验证正常、坏结构和业务冲突 |

## 代码导读

contracts.py 先读允许字段和响应校验，再读不变量规则，最后看对应失败测试为何构造这些响应。

实现文件：

- [contracts.py](src/ai_testing/contracts.py)

## 练习

构造字段完整但业务矛盾的响应，再构造内容合理但缺字段的响应，分别说明哪种检查应该失败。

在 [学习记录](workbook.md) 写下预测，运行后补实际结果，并记录一次失败或边界情形。

## 运行与验收

```bash
python tools/materialize.py quality 8.3-mock-contract-invariant
cd .build/quality/8.3-mock-contract-invariant/ai-testing
python -m pytest -q
```

本章是累积项目，先还原完整状态再运行测试，不要把本章新增文件当作独立应用。

## 边界

离线替身测试不验证模型提供方的真实协议；外部接口需用受控样本另行做连接与契约验证。

契约测试不能证明模型回答正确；它只保证接口形状和关键业务不变量不会被 Mock 掩盖。
