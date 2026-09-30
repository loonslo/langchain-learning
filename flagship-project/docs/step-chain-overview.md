# 里程碑 7.1 的四步衔接

| 步骤 | 新增能力 | 仍需检查的旧链路 |
|---|---|---|
| step1 | 单份 FAQ、拒答、真实来源 | app → bootstrap → assistant → knowledge |
| step2 | 多文档摄取与稳定片段标识 | 旧 assistant 接口和来源展示 |
| step3 | 产品链离线评测与样本 | 评测调用正式 assistant，而非平行 Demo |
| step4 | 语义与关键词融合检索 | 无证据拒答、引用和此前全部测试 |

先用 `python tools/materialize.py flagship m1-rag-mvp/step4` 还原，再在还原项目内运行累计测试。变更报告使用同一命令加 `--diff`。每一步的新增、修改和继承文件见相应 [学习入口](../README.md)。
