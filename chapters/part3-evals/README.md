# 第 3 篇：评测方法论

从失败过程与小题集出发，理解规则、模型评委、数据工程和回归对比，把分数转成有证据的改动。

先修：第 2 篇（尤其 2.4、2.6）。

- [3.1 失败分析：先找到最早出错的环节](3.1-error-analysis/README.md)（离线）
- [3.2 基础评测：把预期拆成可以判断的项](3.2-eval-basics/README.md)（真实模型）
- [3.3 LLM 评委：让语义判断也能被复查](3.3-llm-judge/README.md)（真实模型）
- [3.4 评测数据建设：把业务覆盖写成样本](3.4-eval-dataset-build/README.md)（离线）
- [3.5 Ragas 评测：理解指标实际需要的证据](3.5-eval-dataset-ragas/README.md)（合并离线，RAGAS 需真实模型）
- [3.6 LangSmith 追踪：让一次调用可以回放](3.6-langsmith-eval/README.md)（真实模型，LangSmith 可选）
- [3.7 回归曲线：看见改动带来的收益与退化](3.7-eval-regression-curve/README.md)（真实模型）
- [3.8 提示词 A/B 对比：用固定问题检验修改](3.8-prompt-ab-judge/README.md)（真实模型 + LangSmith）
- [3.9 Agent 轨迹评测：结果正确还不够](3.9-agent-trajectory-eval/README.md)（离线）
- [3.10 失败诊断：把结果转成下一次改动](3.10-eval-report-failures/README.md)（离线，live 模式需真实模型）

[返回全书目录](../README.md)
