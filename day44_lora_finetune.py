"""
Day 44 · 认知层：跑一次 LoRA + 量化/蒸馏等概念扫盲
==========================================================
测试工程师转 AI 应用开发  ← M9，【动手·一次性】建立体感即可

部分 JD 要"RAG + 微调 + Agent"三件套，零微调经验会吃亏。所以亲手跑通一次
LoRA 微调，建立体感、能讲清流程就够——不深究推理加速/kernel 那些（另一个岗位）。

LoRA 是什么（一句话）：不动原模型的几十亿参数，只在旁边加一小撮可训练的低秩
矩阵，训练这一小撮就能让模型学到新风格/任务。省显存、省时间、产物只有几 MB。

⚠️ 真跑需要 GPU（或 Colab 免费 GPU）+ pip install peft transformers datasets accelerate。
   本机没装/没卡时，下面会跳过实际训练，只打印流程，不报错。
==========================================================
"""


def lora_demo():
    """LoRA 微调的最小骨架（结构对、参数小，重在跑通流程）。"""
    try:
        import torch
        from transformers import (AutoModelForCausalLM, AutoTokenizer,
                                   TrainingArguments, Trainer, DataCollatorForLanguageModeling)
        from peft import LoraConfig, get_peft_model
        from datasets import Dataset
    except Exception as e:
        print(f"(缺依赖/环境，跳过实际训练：pip install peft transformers datasets accelerate) {type(e).__name__}")
        print("  流程仍照下面 6 步走，有 GPU 时即可真训。")
        _print_steps()
        return

    base = "Qwen/Qwen2.5-0.5B"   # 用小模型建体感；显存够可换大的
    tok = AutoTokenizer.from_pretrained(base)
    model = AutoModelForCausalLM.from_pretrained(base)

    # 关键：LoRA 配置——只训练注意力里的低秩适配器，原参数冻结
    lora = LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                      target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM")
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()   # 会看到可训练参数只占极小比例

    # 造几条玩具数据（真实场景是你的领域语料）
    samples = [{"text": "问：什么是RAG？答：检索增强生成。"}] * 20
    ds = Dataset.from_list(samples).map(lambda x: tok(x["text"], truncation=True, max_length=64))

    args = TrainingArguments(output_dir="lora_out", num_train_epochs=1,
                             per_device_train_batch_size=2, logging_steps=5, report_to=[])
    Trainer(model=model, args=args, train_dataset=ds,
            data_collator=DataCollatorForLanguageModeling(tok, mlm=False)).train()
    model.save_pretrained("lora_adapter")   # 产物只有适配器，几 MB
    print("LoRA 训练完成，适配器存到 lora_adapter/")


def _print_steps():
    for i, s in enumerate([
        "选基座模型 + 冻结原参数",
        "配 LoraConfig（r/alpha/target_modules）",
        "get_peft_model 套上 LoRA 适配器",
        "准备领域数据集（tokenize）",
        "Trainer 训练（只更新适配器）",
        "保存适配器（几 MB），推理时加载到基座上",
    ], 1):
        print(f"  {i}. {s}")


# ---------- 概念扫盲：只记一句话定义，不学原理 ----------
CONCEPTS = {
    "量化(Quantization)": "把模型权重精度降低（如 16bit→4bit），让大模型能在小显卡跑，省显存换一点精度",
    "蒸馏(Distillation)": "用大模型当老师教小模型，让小模型学到接近大模型的能力，部署更便宜",
    "Flash Attention": "一种更省显存、更快的注意力计算实现，加速训练/推理，不改变结果",
    "Scaling Laws": "模型越大、数据越多、算力越足，效果通常越好的经验规律",
}


if __name__ == "__main__":
    print("===== LoRA 微调（有 GPU 才真训，否则只看流程）=====")
    lora_demo()
    print("\n===== 概念扫盲（一句话定义，面试能聊即可）=====")
    for k, v in CONCEPTS.items():
        print(f"  - {k}：{v}")


# ----------------------------------------------------------
# 小结：
# - LoRA：冻结原模型，只训练旁挂的低秩适配器——省显存省时间，产物几 MB。
# - 量化/蒸馏/Flash Attention/Scaling Laws：只需一句话定义，不深究（那是算法/infra 岗）。
# - 你的定位是"用模型"，微调建立体感 + 能讲清取舍即可，别在这条线上和科班拼深度。
#
# 面试话术：
#   "我跑通过 LoRA，知道它冻结主干只训适配器、产物很小；但我的主场是 RAG+评测+工程，
#    微调对我是'会用、能判断何时用'，不是核心。"
# ----------------------------------------------------------
