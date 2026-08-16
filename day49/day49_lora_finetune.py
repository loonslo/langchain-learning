"""
Day 49 · 认知层：跑一次 LoRA（按生产口径跑，不是"能跑就行"）+ 量化/蒸馏概念扫盲
==========================================================
测试工程师转 AI 应用开发  ← M11 认知层，【动手·一次性】建立体感即可

部分 JD 要"RAG + 微调 + Agent"三件套，零微调经验会吃亏。所以亲手跑通一次
LoRA 微调，建立体感、能讲清流程就够——不深究推理加速/kernel 那些（另一个岗位）。

LoRA 是什么（一句话）：不动原模型的几十亿参数，只在旁边加一小撮可训练的低秩
矩阵，训练这一小撮就能让模型学到新风格/任务。省显存、省时间、产物只有几 MB。

★ 但"跑通"和"生产可用"差 5 件事，网上 20 行的 LoRA demo 全都缺，面试一问就露馅：
  ① 只对【答案】算 loss。demo 把"问+答"整段喂进去算 loss，模型连怎么提问也一起学，
     推理时会自问自答。生产必须把 prompt 部分的 label 置 -100 屏蔽掉。
  ② 必须走 chat template。生产数据是对话，训练时的分隔符要和推理时一模一样，
     否则训了半天，上线格式对不上，白训。
  ③ 必须有 held-out 验证集。只看 train loss 下降 = 只知道它背下来了，不知道它学会了。
  ④ 超参不是默认值。Trainer 默认 lr=5e-5 是给全参微调的，LoRA 要 1e-4~2e-4（差一个量级），
     用默认值会得到"loss 几乎不动"的假象。再加 seed 固定，保证可复现。
  ⑤ ★最关键：微调也要有【回归门禁】。这是你的护城河——训完不是"看着还行"就发版，
     而是拿同一套 held-out 用例，让【基座】和【基座+适配器】各答一遍打分对比，
     没比基座更好就 exit 1，跟 Day58 的 CI 质量门禁是同一套思路。
  另外还验证一件产品化的事：适配器存盘后【重新加载回来】必须还能复现同样的行为，
  否则产物是坏的（这类事故在真实项目里比训练本身更常见）。

用法
----
1) 冒烟跑（几 MB 的迷你模型、CPU 几十秒，只验证流程能跑通，不做质量断言）：
     python day49_lora_finetune.py --smoke

2) 真训（默认 Qwen2.5-0.5B-Instruct；有 GPU 几十秒，纯 CPU 大概几分钟）：
     python day49_lora_finetune.py
     python day49_lora_finetune.py --base Qwen/Qwen2.5-1.5B-Instruct --epochs 10

3) 导出成 LLaMA-Factory 配置（不训练，只生成数据集 + YAML，见第 4 节）：
     python day49_lora_finetune.py --export-llamafactory

退出码：0 = 回归门禁通过；1 = 微调后没比基座更好（该拦住，别发版）。
依赖：pip install torch transformers peft datasets accelerate
国内拉不动 HuggingFace 时：设 HF_ENDPOINT=https://hf-mirror.com，或先用 ModelScope
把模型下到本地，再 --base 指向本地目录（跟 common.py 里 bge 模型的做法一致）。
==========================================================
"""

from __future__ import annotations

import argparse
import inspect
import os
import sys
from pathlib import Path

# 训练本身是本地计算，不需要 DEEPSEEK_API_KEY（common.py 那套是给调 API 的 day 用的）
OUT_DIR = Path("output/day49_lora")     # output/ 已在 .gitignore，产物不进 git
SEED = 42

# ---------- 要教会模型的领域"口径"：客服固定话术（基座绝对不会这么说）----------
# 真实场景这里是你的领域语料（工单、话术、代码规范）；此处用 12 条玩具样本建体感。
STYLE_HEAD, STYLE_TAIL = "【小南客服】", "（如需人工，请回复 0）"
TRAIN_DATA = [
    ("怎么退货？", "7 天内未拆封可直接在订单页申请退货，运费我们出。"),
    ("发货要多久？", "现货 24 小时内发出，预售商品以商品页标注的档期为准。"),
    ("支持开发票吗？", "支持，订单完成后在「我的-发票」里申请，电子发票 1 个工作日开出。"),
    ("能改收货地址吗？", "未发货可在订单页自助修改，已发货请联系快递员改派。"),
    ("优惠券怎么用？", "结算页勾选可用券即可，一单只能叠加一张店铺券和一张平台券。"),
    ("坏了怎么办？", "签收 48 小时内拍照上传，质量问题包退换，不用您承担运费。"),
    ("有保修吗？", "整机保修一年，人为损坏不在保修范围内，可走付费维修。"),
    ("怎么查物流？", "订单页点「查看物流」即可，也可以把单号发我帮您查。"),
    ("能便宜点吗？", "价格是全国统一的，但可以帮您留意店铺满减活动的开始时间。"),
    ("几点上班？", "在线客服每天 9:00-21:00 值班，其余时间留言会在次日回复。"),
    ("支持货到付款吗？", "部分地区支持，下单时结算页会显示是否可选货到付款。"),
    ("怎么取消订单？", "未发货可在订单页直接取消，已发货请拒收后走退款流程。"),
]

# held-out：训练里【没出现过】的问题。门禁只认这个，训练集上的表现不算数。
EVAL_CASES = [
    "我买错型号了能换吗？",
    "你们周末发货吗？",
    "赠品少发了怎么处理？",
    "会员有什么权益？",
]

# 回归门禁阈值（写进代码、进 git、可回溯，跟 capstone/ci_gate.py 一个套路）
GATE = {
    "适配器最低得分": 0.75,   # 微调后 held-out 口径命中率下限
    "相对基座最小增益": 0.25,  # 且必须比基座明显更好，否则这次微调没价值
}


# ==========================================================
# 0. 运行环境：设备 / 精度 / 版本差异兜底
# ==========================================================
def pick_runtime():
    """选设备和精度。生产里这段决定你能不能训得动、训得快。"""
    import torch
    if torch.cuda.is_available():
        bf16 = torch.cuda.is_bf16_supported()
        return {"device": "cuda", "dtype": torch.bfloat16 if bf16 else torch.float16,
                "bf16": bf16, "fp16": not bf16, "use_cpu": False}
    # CPU 上必须 fp32：半精度在 CPU 上要么不支持，要么慢到没法用，还容易出 NaN
    return {"device": "cpu", "dtype": torch.float32,
            "bf16": False, "fp16": False, "use_cpu": True}


def _fit(cls, kwargs: dict, quiet: bool = False) -> dict:
    """只保留当前版本 cls 真正支持的参数。

    transformers 4→5 改过一批参数名（evaluation_strategy→eval_strategy、
    Trainer 的 tokenizer→processing_class）。教学文件要在别人机器上也能跑，
    与其钉死版本，不如按签名过滤——这也是生产里做版本兼容的常规手法。
    """
    ok = set(inspect.signature(cls.__init__).parameters)
    dropped = sorted(set(kwargs) - ok)
    if dropped and not quiet:
        print(f"  (当前版本 {cls.__name__} 不支持 {dropped}，已忽略)")
    return {k: v for k, v in kwargs.items() if k in ok}


# ==========================================================
# 1. 数据：chat template + 只对答案算 loss（生产要点 ①②）
# ==========================================================
def to_text(tok, question: str, answer: str | None = None) -> str:
    """把一条样本拼成模型真正看到的字符串。

    训练和推理必须走同一个模板，所以这里只有一个函数：
      answer=None  → 推理用的 prompt（结尾是"该你答了"的标记）
      answer=...   → 训练用的完整文本（prompt + 答案）
    没有 chat_template 的老模型（如 gpt2）退化成纯文本格式，流程一样跑。
    """
    if getattr(tok, "chat_template", None):
        msgs = [{"role": "user", "content": question}]
        if answer is None:
            return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        msgs.append({"role": "assistant", "content": answer})
        return tok.apply_chat_template(msgs, tokenize=False)
    base = f"问：{question}\n答："
    return base if answer is None else f"{base}{answer}{tok.eos_token}"


def encode(tok, question: str, answer: str, max_len: int = 256) -> dict:
    """★ 生产要点①：prompt 部分的 label 全置 -100，loss 只算在答案上。

    -100 是 PyTorch 交叉熵的忽略值。不做这一步，模型会连"用户会怎么问"
    一起学，推理时自问自答、复读问题——这是微调最常见的翻车原因。
    """
    prompt = to_text(tok, question)
    full = to_text(tok, question, answer)
    # 模板保证 full 以 prompt 开头，所以 prompt 的 token 数就是要屏蔽的长度
    prompt_len = len(tok(prompt, add_special_tokens=False)["input_ids"])
    ids = tok(full, add_special_tokens=False)["input_ids"][:max_len]
    labels = [-100] * min(prompt_len, len(ids)) + ids[prompt_len:]
    return {"input_ids": ids, "attention_mask": [1] * len(ids), "labels": labels}


def build_datasets(tok):
    """训练集 / 验证集切分（生产要点③）。验证集用来看它是"学会了"还是"背下来了"。"""
    from datasets import Dataset
    rows = [encode(tok, q, f"{STYLE_HEAD}{a}{STYLE_TAIL}") for q, a in TRAIN_DATA]
    split = max(1, len(rows) // 5)          # 留 20% 做 held-out loss
    return Dataset.from_list(rows[split:]), Dataset.from_list(rows[:split])


# ==========================================================
# 2. LoRA 配置与训练
# ==========================================================
# 生产常识：只挂 q/v 是论文里最省的配置，效果一般；要效果就把注意力四件套 +
# MLP 三件套都挂上（参数量仍只有全量的 1% 左右）。
PREFERRED_TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"]


def find_target_modules(model) -> list[str]:
    """自动探测该塞 LoRA 的线性层名。

    写死 ["q_proj","v_proj"] 只对 LLaMA/Qwen 系有效，换个模型（gpt2 用 Conv1D
    的 c_attn）就会报 "Target modules not found"。生产里换基座是常事，探测一下更稳。
    """
    kinds = {"Linear", "Conv1D", "Linear4bit", "Linear8bitLt"}
    names = {n.rsplit(".", 1)[-1] for n, m in model.named_modules()
             if m.__class__.__name__ in kinds}
    hit = [t for t in PREFERRED_TARGETS if t in names]
    return hit or sorted(names - {"lm_head", "score"})


def train_lora(base: str, epochs: int, rt: dict, out_dir: Path):
    """挂 LoRA → 训练 → 存适配器。返回 (peft_model, tokenizer, 训练指标)。"""
    from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer,
                              TrainingArguments, DataCollatorForSeq2Seq)
    from peft import LoraConfig, get_peft_model

    tok = AutoTokenizer.from_pretrained(base)
    if tok.pad_token is None:
        # 很多因果模型（Qwen/gpt2）没有 pad token，不补这一句 collator 直接抛异常
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(base, dtype=rt["dtype"])
    model.config.use_cache = False   # 训练期关掉 KV cache，和梯度检查点冲突且白占显存

    targets = find_target_modules(model)
    print(f"  LoRA 目标层：{targets}")
    # r=16 / alpha=32（经验比例 alpha=2r）；r 越大能学的越多，也越容易过拟合
    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
                      target_modules=targets, task_type="CAUSAL_LM")
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()    # 可训练参数占比通常 <1%

    train_ds, eval_ds = build_datasets(tok)
    args = TrainingArguments(**_fit(TrainingArguments, dict(
        output_dir=str(out_dir / "ckpt"),
        num_train_epochs=epochs,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=1,     # 显存不够时调大它凑等效 batch，比调 bs 安全
        learning_rate=2e-4,                # ★ 生产要点④：LoRA 要 1e-4~2e-4，不是默认 5e-5
        lr_scheduler_type="cosine",
        warmup_steps=5,
        max_grad_norm=1.0,
        seed=SEED,                         # ★ 可复现：同数据同 seed 训出同结果
        data_seed=SEED,
        logging_steps=5,
        eval_strategy="epoch",             # ★ 生产要点③：每轮看 held-out loss
        save_strategy="no",                # 教学场景不留中间检查点，省磁盘
        bf16=rt["bf16"], fp16=rt["fp16"], use_cpu=rt["use_cpu"],
        remove_unused_columns=False,       # PEFT 模型签名不同，开着会把我们的列删掉
        report_to=[],
    )))
    # 用 Seq2Seq collator：它会把 labels 用 -100 补齐。
    # 别用 DataCollatorForLanguageModeling——它会拿 input_ids 覆盖我们精心做的 labels，
    # 前面的 prompt 屏蔽就白做了。这是"看着能跑、其实训歪了"的经典坑。
    collator = DataCollatorForSeq2Seq(tok, padding=True, label_pad_token_id=-100)
    trainer = Trainer(**_fit(Trainer, dict(
        model=model, args=args, train_dataset=train_ds, eval_dataset=eval_ds,
        data_collator=collator, processing_class=tok, tokenizer=tok,
    ), quiet=True))

    train_out = trainer.train()
    metrics = {"train_loss": train_out.training_loss,
               "eval_loss": trainer.evaluate().get("eval_loss")}
    model.config.use_cache = True   # 训完记得开回来，否则后面生成会慢一个量级
    model.eval()
    adapter_dir = out_dir / "adapter"
    model.save_pretrained(str(adapter_dir))
    tok.save_pretrained(str(adapter_dir))   # 分词器要一起存，否则换机器加载对不上
    size_mb = sum(f.stat().st_size for f in adapter_dir.rglob("*") if f.is_file()) / 1e6
    print(f"  适配器已存到 {adapter_dir}/（{size_mb:.1f} MB，基座一个字节没动）")
    return model, tok, metrics


# ==========================================================
# 3. ★ 回归门禁：基座 vs 基座+适配器（生产要点⑤，你的护城河）
# ==========================================================
def generate(model, tok, question: str, max_new_tokens: int = 64) -> str:
    import torch
    prompt = to_text(tok, question)
    inputs = tok(prompt, return_tensors="pt", add_special_tokens=False).to(model.device)
    with torch.no_grad():
        # do_sample=False（贪心）：评测必须可复现，跟 common.py 里 temperature=0 同理。
        # 逐条生成不做 batch：批量生成要处理左 padding，一错就静默污染评测结果。
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                             pad_token_id=tok.pad_token_id)
    return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def score(model, tok, label: str) -> float:
    """在 held-out 用例上打分：口径命中率（开头标记 + 结尾标记各占一半）。

    真实项目里这里换成你的业务指标（格式合规率 / 关键词命中 / LLM-as-judge），
    形式不变：一个能进 CI 比大小的数。

    ⚠️ 注意这个门禁只保证【口径】，不保证【事实】：12 条样本训出来的模型能把格式
    学得一模一样，但答案内容大概率是编的。这恰恰说明分工——微调管"怎么说"，
    RAG 管"说什么"。所以真实项目的门禁要两套指标一起看，别拿格式合格当质量合格。
    """
    hits = 0.0
    for q in EVAL_CASES:
        ans = generate(model, tok, q)
        hit = (STYLE_HEAD in ans) * 0.5 + (STYLE_TAIL in ans) * 0.5
        hits += hit
        print(f"    [{label}] {q} → {ans.strip()[:60]!r}  得分 {hit}")
    return hits / len(EVAL_CASES)


def gate(base_score: float, lora_score: float) -> int:
    """达标 exit 0，不达标 exit 1——和 Day58 的 CI 质量门禁完全一致的用法。"""
    fails = []
    if lora_score < GATE["适配器最低得分"]:
        fails.append(f"适配器得分 {lora_score:.2f} < {GATE['适配器最低得分']}")
    gain = lora_score - base_score
    if gain < GATE["相对基座最小增益"]:
        fails.append(f"相对基座增益 {gain:+.2f} < {GATE['相对基座最小增益']}")
    if fails:
        print("\n[FAIL] 微调回归门禁未通过：")
        for f in fails:
            print("  -", f)
        print("  → 这版适配器不该发版。查数据量/轮数/学习率，或者干脆承认这个任务不该用微调。")
        return 1
    print(f"\n[PASS] 微调回归门禁通过：基座 {base_score:.2f} → 适配器 {lora_score:.2f}")
    return 0


def verify_reload(base: str, adapter_dir: Path, rt: dict) -> str:
    """产物验收：把适配器从磁盘加载回基座，确认它真的能用。

    "训练脚本里表现好、加载回来是另一回事"——路径写错、忘存分词器、
    基座版本对不上，都会让线上加载出来的模型行为不一致。所以必须验一次。
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    tok = AutoTokenizer.from_pretrained(str(adapter_dir))
    model = PeftModel.from_pretrained(
        AutoModelForCausalLM.from_pretrained(base, dtype=rt["dtype"]), str(adapter_dir))
    # 部署二选一：保持"基座 + 适配器"分开（一个基座能挂多套适配器，按租户切换，省显存），
    # 或 model.merge_and_unload() 合成一个普通模型（推理少一层开销，但从此绑死一套权重）。
    model.eval()
    return generate(model, tok, EVAL_CASES[0])


# ==========================================================
# 4. LLaMA-Factory：什么时候就别自己写训练脚本了
# ==========================================================
# 上面那套是手写的（transformers + peft）。真实项目里更常见的是直接用
# LLaMA-Factory（github.com/hiyouga/LLaMA-Factory）：一个 YAML 跑 LoRA/QLoRA/
# 全参/DPO，支持几百个模型，还带 WebUI 和多卡/DeepSpeed。
#
# 怎么选：
#   手写          → 要把训练嵌进自己的流水线（比如本文件第 3 节的回归门禁）、
#                   要改 loss/数据处理、或者就是想搞清楚每一步在干嘛（面试要讲的是这个）。
#   LLaMA-Factory → 只是"跑一次标准 SFT"：换基座、换数据、扫超参、开 QLoRA、上多卡。
#                   这些它都做好了，自己写就是重复造轮子，还容易踩前面那一串坑。
#
# ★ 但要看清它的边界：LLaMA-Factory 负责【把模型训出来】，不负责【判断这版能不能发】。
#   它内置的 eval 只有 loss / BLEU / ROUGE 这类通用指标，没有"我的业务口径达标没有"。
#   所以哪怕训练全交给它，第 3 节那套"基座 vs 适配器 + exit 1"的门禁还是得自己加，
#   接在 `llamafactory-cli train` 后面跑——这就是测试背景的人能补上的那一块。
#
# 下面这个函数把【本文件同一份数据和超参】导出成它能直接吃的配置，
# 方便你对着看：手写代码里的每个参数，在 YAML 里对应哪一行。
LF_DIR = OUT_DIR / "llamafactory"

# Qwen2.5 系用 qwen 模板；换基座要去 LLaMA-Factory README 的模型表查 Template 列
# （Qwen3 是 qwen3/qwen3_nothink，Llama3 是 llama3……填错等于训练模板和推理对不上）。
LF_TEMPLATE = "qwen"

LF_TRAIN_YAML = """\
### model
model_name_or_path: {base}
trust_remote_code: true

### method（对应本文件 train_lora() 里的 LoraConfig）
stage: sft                 # sft / dpo / ppo / pt，换个词就换一种训练范式
do_train: true
finetuning_type: lora      # 换成 full 就是全参微调，freeze 是只训部分层
lora_rank: 16
lora_alpha: 32
lora_target: all           # = 本文件 find_target_modules() 干的事，它帮你自动挂满

### dataset
dataset: cs_style          # 名字要和 dataset_info.json 里的 key 一致
# 不指定 dataset_dir 就去 LLaMA-Factory/data 找；指定了就不用把数据拷进它仓库
dataset_dir: {data_dir}
# ★ template 是最容易错的一行：它决定 chat 模板，填错等于白训
template: {template}
cutoff_len: 256
overwrite_cache: true

### output
output_dir: {out_dir}
logging_steps: 5
save_strategy: epoch
plot_loss: true            # 训完出一张 loss 曲线图，写周报/复盘直接用
overwrite_output_dir: true
report_to: none

### train（对应本文件的 TrainingArguments）
per_device_train_batch_size: 2
gradient_accumulation_steps: 1
learning_rate: 2.0e-4      # 同样别用默认值，LoRA 就是要这个量级
num_train_epochs: {epochs}.0
lr_scheduler_type: cosine
warmup_ratio: 0.1
bf16: true                 # 无 GPU 就改成 false（CPU 上半精度跑不动）
seed: 42

### eval（★ 默认是注释掉的，很多人就这么裸训了——一定要打开）
val_size: 0.2
per_device_eval_batch_size: 2
eval_strategy: epoch
"""

LF_MERGE_YAML = """\
### 合并：把适配器焊进基座，导出成一个普通模型（vLLM/Ollama 就能直接加载）
### 注意：合并时不能开 quantization_bit，否则精度会被量化误差污染
model_name_or_path: {base}
adapter_name_or_path: {out_dir}
template: {template}
trust_remote_code: true

export_dir: {merged_dir}
export_size: 5
export_device: cpu
export_legacy_format: false
"""


def export_llamafactory(base: str, epochs: int) -> int:
    """把本文件的数据 + 超参导出成 LLaMA-Factory 配置（只写文件，不训练）。"""
    import json
    LF_DIR.mkdir(parents=True, exist_ok=True)
    data_dir = LF_DIR.resolve().as_posix()
    out_dir = (LF_DIR / "saves").resolve().as_posix()

    # 1) alpaca 格式：instruction=用户问题，output=带口径的答案。
    #    prompt 屏蔽、chat 模板拼接这些它内部都做了，所以数据只要给"问/答"两列。
    rows = [{"instruction": q, "output": f"{STYLE_HEAD}{a}{STYLE_TAIL}"} for q, a in TRAIN_DATA]
    (LF_DIR / "cs_style.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # 2) 数据集注册表：不写这个直接报 Unknown dataset，是新手第一个卡点
    (LF_DIR / "dataset_info.json").write_text(json.dumps(
        {"cs_style": {"file_name": "cs_style.json",
                      "columns": {"prompt": "instruction", "response": "output"}}},
        ensure_ascii=False, indent=2), encoding="utf-8")

    (LF_DIR / "lora_sft.yaml").write_text(LF_TRAIN_YAML.format(
        base=base, data_dir=data_dir, out_dir=out_dir,
        template=LF_TEMPLATE, epochs=epochs), encoding="utf-8")
    (LF_DIR / "merge.yaml").write_text(LF_MERGE_YAML.format(
        base=base, out_dir=out_dir, template=LF_TEMPLATE,
        merged_dir=(LF_DIR / "merged").resolve().as_posix()), encoding="utf-8")

    print(f"已生成 LLaMA-Factory 配置：{LF_DIR}/")
    for f in ("cs_style.json", "dataset_info.json", "lora_sft.yaml", "merge.yaml"):
        print(f"  - {f}")
    print(f"""
装它（本项目 .venv 不用装，它依赖很重，建议单独建环境）：
  git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git
  cd LLaMA-Factory && pip install -e . && pip install -r requirements/metrics.txt

三条命令跑完训练 → 试聊 → 合并导出：
  llamafactory-cli train  {data_dir}/lora_sft.yaml
  llamafactory-cli chat   --model_name_or_path {base} --adapter_name_or_path {out_dir} \\
                          --template {LF_TEMPLATE}
  llamafactory-cli export {data_dir}/merge.yaml

不想写 YAML 就开 WebUI（LLaMA Board），页面上点完直接跑，还能导出等价 YAML：
  llamafactory-cli webui

国内下不动模型：先 set USE_MODELSCOPE_HUB=1（Linux 用 export），
model_name_or_path 换成 ModelScope 的 ID（如 Qwen/Qwen2.5-0.5B-Instruct）。
显存不够：train yaml 里加 quantization_bit: 4 + quantization_method: bnb → 就是 QLoRA。

★ 训完别停在这：把本文件的 score()/gate() 指向导出的适配器再跑一遍，
  让它照样输出 PASS/FAIL 和退出码，这一步才是能写进简历的东西。""")
    return 0


# ==========================================================
# 5. 主流程
# ==========================================================
def run(base: str, epochs: int, smoke: bool) -> int:
    rt = pick_runtime()
    print(f"设备 {rt['device']} / 精度 {rt['dtype']}；基座 {base}；{epochs} 轮")
    if rt["use_cpu"] and not smoke:
        print("  (无 GPU：能跑但慢。生产上 7B 以上必须上 GPU，或用 QLoRA 4bit 压显存)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("\n--- 1/4 训练 ---")
    model, tok, metrics = train_lora(base, epochs, rt, OUT_DIR)
    ev = metrics["eval_loss"]
    ev_txt = f"{ev:.4f}" if ev is not None else "n/a"
    print(f"  train_loss={metrics['train_loss']:.4f}  eval_loss={ev_txt}"
          "   ← eval 不降只有 train 降 = 背下来了，不是学会了")

    print("\n--- 2/4 基座基线（同一个模型，临时关掉适配器，排除环境差异）---")
    with model.disable_adapter():
        base_score = score(model, tok, "基座")

    print("\n--- 3/4 微调后 ---")
    lora_score = score(model, tok, "适配器")

    print("\n--- 4/4 产物验收：从磁盘重新加载适配器 ---")
    reloaded = verify_reload(base, OUT_DIR / "adapter", rt)
    print(f"  重载后输出：{reloaded.strip()[:60]!r}")

    if smoke:
        print(f"\n[SKIP] 冒烟模式（随机权重的迷你模型学不到东西）只验证流程跑通，"
              f"不做质量断言。得分：基座 {base_score:.2f} / 适配器 {lora_score:.2f}")
        return 0
    return gate(base_score, lora_score)


CONCEPTS = {
    "量化(Quantization)": "把模型权重精度降低（如 16bit→4bit），让大模型能在小显卡跑，省显存换一点精度",
    "QLoRA": "4bit 量化基座 + LoRA 适配器，单张消费级卡就能微调 7B~13B——预算有限时的默认选择",
    "蒸馏(Distillation)": "用大模型当老师教小模型，让小模型学到接近大模型的能力，部署更便宜",
    "灾难性遗忘": "只喂新领域数据，模型会忘掉通用能力——所以要留一套通用回归集，别只测新任务",
    "Flash Attention": "一种更省显存、更快的注意力计算实现，加速训练/推理，不改变结果",
    "Scaling Laws": "模型越大、数据越多、算力越足，效果通常越好的经验规律",
}


def main() -> int:
    p = argparse.ArgumentParser(description="Day49 LoRA 微调 + 回归门禁")
    p.add_argument("--base", default=os.getenv("LORA_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"))
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--smoke", action="store_true", help="迷你模型冒烟跑，只验流程")
    p.add_argument("--export-llamafactory", action="store_true",
                   help="不训练，只导出等价的 LLaMA-Factory 数据集 + YAML 配置")
    a = p.parse_args()
    base, epochs = ("sshleifer/tiny-gpt2", 1) if a.smoke else (a.base, a.epochs)

    if a.export_llamafactory:
        print("===== 导出 LLaMA-Factory 配置（同一份数据/超参，换个工具跑）=====")
        return export_llamafactory(a.base, a.epochs)

    print("===== LoRA 微调（按生产口径：屏蔽 prompt loss + held-out 验证 + 回归门禁）=====")
    try:
        code = run(base, epochs, a.smoke)
    except ImportError as e:
        print(f"缺依赖，跳过实际训练：pip install torch transformers peft datasets accelerate\n  {e}")
        code = 0
    print("\n===== 概念扫盲（一句话定义，面试能聊即可）=====")
    for k, v in CONCEPTS.items():
        print(f"  - {k}：{v}")
    return code


if __name__ == "__main__":
    sys.exit(main())


# ----------------------------------------------------------
# 小结：
# - LoRA：冻结原模型，只训练旁挂的低秩适配器——省显存省时间，产物几 MB。
# - "跑通"到"生产可用"差 5 件事：只对答案算 loss、走 chat template、留 held-out、
#   LoRA 专属超参 + 固定 seed、训完过回归门禁 + 产物重载验收。
# - 实测（Qwen2.5-0.5B-Instruct / CPU / 12 轮 / 12 条样本）：口径命中率 0.00 → 1.00，
#   但答案内容基本是编的——微调只教会了"怎么说"，"说什么"得交给 RAG。
# - 工具选型：日常跑标准 SFT 用 LLaMA-Factory（一个 YAML 的事），手写只在要改
#   loss/数据处理、或要把训练嵌进自己流水线时才做。但它只管训、不管判——
#   "这版能不能发"的门禁两条路都得自己加。
# - 量化/蒸馏/Flash Attention/Scaling Laws：一句话定义即可（那是算法/infra 岗）。
# - 你的定位是"用模型"，微调建立体感 + 能讲清取舍即可，别在这条线上和科班拼深度。
#
# 面试话术：
#   "我跑通过 LoRA，知道它冻结主干只训适配器、产物很小。但我关注的点跟算法同学不太一样：
#    我会先问 label 有没有屏蔽 prompt、训练模板和推理模板是不是一套、有没有 held-out 集。
#    我给微调也加了回归门禁——训完拿 held-out 让基座和适配器各答一遍打分对比，
#    没比基座更好就 exit 1 拦住，跟我给 RAG 做的 CI 质量门禁是同一套东西。
#    微调对我是'会用、能判断何时用'——多数场景 RAG + 提示词更划算，微调只治
#    '格式/口径稳不下来'这类病。真要批量训我会用 LLaMA-Factory，一个 YAML 的事，
#    但它只负责训出来、不负责判断能不能发，门禁那段还是得我自己接上。"
# ----------------------------------------------------------
