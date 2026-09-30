# 6.2 LoRA 微调选修：训练、验证与重新加载

[全书目录](../../README.md) · [上一章 6.1](../6.1-choose-prompt-rag-finetune/README.md) · [进入旗舰项目](../../../flagship-project/README.md)

- **目标**：亲手跑通一次 LoRA 微调，并按生产口径加上回归门禁，建立对流程的体感；同时了解量化、蒸馏等概念。
- **前置**：6.1。
- **环境**：选做。需要 `torch`、`transformers`、`peft`、`datasets`、`accelerate`；真训需要下载 `Qwen2.5-0.5B-Instruct`，有 GPU 几十秒，纯 CPU 大约几分钟；`--smoke` 只用几 MB 的迷你模型验证流程。
- **命令**：`python tools/run_chapter.py 6.2 --smoke`

## 问题

LoRA 微调网上有很多 20 行的 demo，能跑，但离“生产可用”差得很远。做一次微调，重点不是让 loss 下降，而是能证明它学会了什么、比基座好在哪、产物能不能复用。

## 概念

**LoRA**：不动原模型的几十亿参数，只在旁边加一小撮可训练的低秩矩阵，训练这一小撮就能让模型学到新的风格或任务。省显存、省时间，产物只有几 MB。

“跑通”与“生产可用”之间差 5 件事：

1. **只对答案算 loss**：把“问 + 答”整段喂进去算 loss，模型连怎么提问也一起学，推理时会自问自答。要把 prompt 部分的 label 置为 -100 屏蔽掉。
2. **走 chat template**：训练时的分隔符要和推理时一模一样，否则上线格式对不上。
3. **留 held-out 验证集**：只看 train loss 下降，只知道它背下来了，不知道它学会了。
4. **超参不是默认值**：`Trainer` 默认的学习率是给全参微调的；LoRA 要 1e-4～2e-4，差一个量级。同时固定 seed，保证可复现。
5. **回归门禁**：拿同一套 held-out 用例，让基座和“基座 + 适配器”各答一遍并打分对比；没比基座更好就以退出码 1 拦住，不发版。适配器存盘后重新加载回来，也必须复现同样的行为。

## 流程

`run()` 分四步：训练 → 打分（基座 vs 适配器）→ 门禁（`gate`：适配器得分不低于 0.75，且比基座至少高 0.25）→ 重载验证（`verify_reload`）。数据是 12 条客服话术样本，教会模型固定口径“【小南客服】……（如需人工，请回复 0）”；held-out 用例是训练里没出现过的问题。退出码 0 表示门禁通过，1 表示微调后没比基座更好。

另外两个入口：`--export-llamafactory` 只导出等价的 LLaMA-Factory 数据集和 YAML（不训练）；文件末尾用 `CONCEPTS` 一句话介绍量化、QLoRA、蒸馏、灾难性遗忘、Flash Attention、Scaling Laws。

## 代码导读

文件较长（约 550 行），按编号读：【0】运行环境（设备与精度）→【1】数据与编码（屏蔽 prompt 的 label）→【2】训练（`train_lora`）→【3】回归门禁（`score`、`gate`）→ `verify_reload` →【4】LLaMA-Factory 导出 →【5】主流程 `run`。

## 练习

1. 先用 `--smoke` 验证流程，再决定是否真训。
2. 真训后看输出：`eval_loss` 不降只有 `train_loss` 降意味着什么？
3. 用 `--export-llamafactory` 导出配置，对照手写代码里每个参数在 YAML 里的位置。
4. 阅读结果：口径命中率从 0 到 1，但答案内容基本是编的。微调教会了“怎么说”，“说什么”仍要交给 RAG。

## 运行与边界

- 依赖很重，本仓库的 `.venv` 不必安装；缺依赖时脚本会跳过训练并提示，不会报错退出。
- 12 条玩具样本只用来建立体感，得分不代表任何真实业务效果。
- 输出目录 `output/lora_adapter/` 相对当前工作目录（用 run_chapter 运行时在本章目录），已被 `.gitignore` 忽略。
- 国内拉不动 HuggingFace 时，设 `HF_ENDPOINT=https://hf-mirror.com`，或先用 ModelScope 下载模型，再用 `--base` 指向本地目录。
