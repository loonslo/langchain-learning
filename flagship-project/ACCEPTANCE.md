# Flagship 29 步 · 总验收清单

项目步骤不设单独 gate；每一步以该步 `README.md` 的产出与验收说明为准。勾选时必须附证据路径（命令输出、报告、截图或提交），不能只写“已完成”。

## 使用方式

1. 按里程碑顺序做，前置未过不跳步。
2. 每步完成后，在 `stepN` 目录留下可定位证据；在本表写证据链接。
3. 环境/外部服务不可用时写“未验证”，不要勾选。
4. 最后用 `python -m capstone.milestones --strict-evidence` 与 CI 门禁复核。

## 验收表

| 步骤 | 教程 | 证据 | 完成 |
|---|---|---|---|
| m1-rag-mvp/step1 | [README](m1-rag-mvp/step1/README.md) | 待填 | [ ] |
| m1-rag-mvp/step2 | [README](m1-rag-mvp/step2/README.md) | 待填 | [ ] |
| m1-rag-mvp/step3 | [README](m1-rag-mvp/step3/README.md) | 待填 | [ ] |
| m1-rag-mvp/step4 | [README](m1-rag-mvp/step4/README.md) | 待填 | [ ] |
| m2-session-langgraph/step1 | [README](m2-session-langgraph/step1/README.md) | 待填 | [ ] |
| m2-session-langgraph/step2 | [README](m2-session-langgraph/step2/README.md) | 待填 | [ ] |
| m3-order-tool-reliability/step1 | [README](m3-order-tool-reliability/step1/README.md) | 待填 | [ ] |
| m3-order-tool-reliability/step2 | [README](m3-order-tool-reliability/step2/README.md) | 待填 | [ ] |
| m3-order-tool-reliability/step3 | [README](m3-order-tool-reliability/step3/README.md) | 待填 | [ ] |
| m3-order-tool-reliability/step4 | [README](m3-order-tool-reliability/step4/README.md) | 待填 | [ ] |
| m4-api-identity-security/step1 | [README](m4-api-identity-security/step1/README.md) | 待填 | [ ] |
| m4-api-identity-security/step2 | [README](m4-api-identity-security/step2/README.md) | 待填 | [ ] |
| m4-api-identity-security/step3 | [README](m4-api-identity-security/step3/README.md) | 待填 | [ ] |
| m4-api-identity-security/step4 | [README](m4-api-identity-security/step4/README.md) | 待填 | [ ] |
| m5-injection-pii-observability/step1 | [README](m5-injection-pii-observability/step1/README.md) | 待填 | [ ] |
| m5-injection-pii-observability/step2 | [README](m5-injection-pii-observability/step2/README.md) | 待填 | [ ] |
| m5-injection-pii-observability/step3 | [README](m5-injection-pii-observability/step3/README.md) | 待填 | [ ] |
| m5-injection-pii-observability/step4 | [README](m5-injection-pii-observability/step4/README.md) | 待填 | [ ] |
| m6-quality-gate-container/step1 | [README](m6-quality-gate-container/step1/README.md) | 待填 | [ ] |
| m6-quality-gate-container/step2 | [README](m6-quality-gate-container/step2/README.md) | 待填 | [ ] |
| m7-capacity-feedback-recovery/step1 | [README](m7-capacity-feedback-recovery/step1/README.md) | 待填 | [ ] |
| m7-capacity-feedback-recovery/step2 | [README](m7-capacity-feedback-recovery/step2/README.md) | 待填 | [ ] |
| m7-capacity-feedback-recovery/step3 | [README](m7-capacity-feedback-recovery/step3/README.md) | 待填 | [ ] |
| m7-capacity-feedback-recovery/step4 | [README](m7-capacity-feedback-recovery/step4/README.md) | 待填 | [ ] |
| m7-capacity-feedback-recovery/step5 | [README](m7-capacity-feedback-recovery/step5/README.md) | 待填 | [ ] |
| m7-capacity-feedback-recovery/step6 | [README](m7-capacity-feedback-recovery/step6/README.md) | 待填 | [ ] |
| m8-evidence-final-frontend/step1 | [README](m8-evidence-final-frontend/step1/README.md) | 待填 | [ ] |
| m8-evidence-final-frontend/step2 | [README](m8-evidence-final-frontend/step2/README.md) | 待填 | [ ] |
| m8-evidence-final-frontend/step3 | [README](m8-evidence-final-frontend/step3/README.md) | 待填 | [ ] |

## 里程碑出口

- m1：可检索、可引用、可拒答的最小 RAG。
- m2：带会话与状态图的 Agent。
- m3：工具白名单、重试、幂等与人工审批。
- m4：身份、租户、权限边界与安全 API。
- m5：注入/PII/可观测性证据。
- m6：质量门禁与容器化交付。
- m7：容量、反馈闭环、恢复演练。
- m8：最终证据包、前端与面试材料。

## 边界

- 本表是课件验收模板，不是完成证明。
- 外部服务（模型、DB、Docker、GPU、云）不可用时必须写“未验证”。
