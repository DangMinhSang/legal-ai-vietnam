"""Script huấn luyện QLoRA cho mô hình LLM chuyên ngành Luật Hình sự Việt Nam.

Phù hợp chạy trên Kaggle (GPU T4 / P100) hoặc Local GPU (RTX 3060/4060):
- Base Model hỗ trợ:
  + "Qwen/Qwen2.5-3B-Instruct" (Khuyến nghị: Siêu nhanh, tiếng Việt xuất sắc)
  + "Qwen/Qwen2.5-7B-Instruct" (Thông minh, lý luận pháp lý sâu sắc)
  + "vinai/PhoGPT-4B-Chat" (Mô hình 4B chuyên ngữ tiếng Việt)
- Kỹ thuật: 4-bit Quantization (bitsandbytes) + PEFT LoRA + HuggingFace TRL SFTTrainer
"""

from __future__ import annotations

import argparse
import os

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune Legal LLM with QLoRA on Kaggle / Local GPU")
    parser.add_argument(
        "--model_name_or_path",
        type=str,
        default="Qwen/Qwen2.5-3B-Instruct",
        help="HuggingFace model ID hoặc đường dẫn model (vd: Qwen/Qwen2.5-3B-Instruct, Qwen/Qwen2.5-7B-Instruct)",
    )
    parser.add_argument(
        "--train_file",
        type=str,
        default="data/processed/finetune/legal_sft_train.jsonl",
        help="Đường dẫn file dữ liệu train JSONL",
    )
    parser.add_argument(
        "--val_file",
        type=str,
        default="data/processed/finetune/legal_sft_val.jsonl",
        help="Đường dẫn file dữ liệu val JSONL",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./output_legal_llm_lora",
        help="Thư mục lưu adapter sau khi huấn luyện",
    )
    parser.add_argument("--epochs", type=int, default=3, help="Số epochs huấn luyện")
    parser.add_argument("--batch_size", type=int, default=2, help="Batch size per device")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max_seq_length", type=int, default=2048, help="Độ dài context tối đa")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA alpha")
    return parser.parse_args()


def formatting_prompts_func(example: dict, tokenizer: AutoTokenizer) -> str:
    """Format tin nhắn messages thành chuỗi văn bản theo Chat template của model."""
    messages = example.get("messages", [])
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    # Fallback thủ công
    text = ""
    for m in messages:
        text += f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
    return text


def main() -> None:
    args = parse_args()
    print("=" * 70)
    print("   HUẤN LUYỆN FINE-TUNING LEGAL LLM VIỆT NAM (QLoRA 4-BIT)")
    print("=" * 70)
    print(f"[*] Base Model       : {args.model_name_or_path}")
    print(f"[*] Train file       : {args.train_file}")
    print(f"[*] Output directory : {args.output_dir}")
    print(f"[*] CUDA Available   : {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[*] Device Name      : {torch.cuda.get_device_name(0)}")

    # 1. Cấu hình 4-bit Quantization để tiết kiệm tối đa VRAM
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    # 2. Tải Tokenizer
    print("[*] Đang tải Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # 3. Tải Model với 4-bit
    print(f"[*] Đang tải Model {args.model_name_or_path} ở định dạng 4-bit...")
    device_map = "auto" if torch.cuda.is_available() else None
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name_or_path,
        quantization_config=bnb_config if torch.cuda.is_available() else None,
        device_map=device_map,
        trust_remote_code=True,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

    if torch.cuda.is_available():
        model = prepare_model_for_kbit_training(model)

    # 4. Cấu hình LoRA (PEFT)
    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 5. Tải dữ liệu
    print("[*] Đang nạp dataset JSONL...")
    data_files = {"train": args.train_file}
    if os.path.exists(args.val_file):
        data_files["validation"] = args.val_file

    dataset = load_dataset("json", data_files=data_files)
    print(f"[+] Đã tải: {len(dataset['train'])} mẫu train")

    # 6. Training Arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        num_train_epochs=args.epochs,
        logging_steps=10,
        save_strategy="epoch",
        evaluation_strategy="epoch" if "validation" in dataset else "no",
        fp16=torch.cuda.is_available(),
        optim="paged_adamw_8bit" if torch.cuda.is_available() else "adamw_torch",
        warmup_ratio=0.05,
        report_to="none",
    )

    # 7. SFT Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset.get("validation"),
        peft_config=peft_config,
        dataset_text_field="text",
        formatting_func=lambda ex: formatting_prompts_func(ex, tokenizer),
        max_seq_length=args.max_seq_length,
        tokenizer=tokenizer,
        args=training_args,
    )

    print("[*] Bắt đầu quá trình huấn luyện Fine-tuning...")
    trainer.train()

    # 8. Lưu kết quả
    print(f"[*] Đang lưu LoRA Adapter vào {args.output_dir}...")
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("[+] Hoàn tất huấn luyện thành công!")


if __name__ == "__main__":
    main()
