from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path


def require_hpc_deps() -> None:
    missing = [
        name
        for name in ["torch", "transformers", "peft", "datasets", "accelerate"]
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        raise SystemExit(
            "Missing SFT dependencies: "
            + ", ".join(missing)
            + "\nInstall the HPC extras before training: pip install -e .[hpc]"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the mandatory SFT warm-start adapter.")
    parser.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("artifacts") / "checkpoints" / "sft_qwen25_3b")
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    args = parser.parse_args()
    require_hpc_deps()

    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

    dataset = load_dataset("json", data_files=str(args.dataset), split="train")
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)

    def tokenize(row):
        text = row["prompt"] + "\n" + row["completion"]
        tokens = tokenizer(text, truncation=True, max_length=4096)
        tokens["labels"] = tokens["input_ids"].copy()
        return tokens

    tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        device_map="auto",
        torch_dtype="auto",
        trust_remote_code=True,
    )
    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_r * 2,
        target_modules="all-linear",
        task_type="CAUSAL_LM",
    )
    model.add_adapter(lora)
    model.gradient_checkpointing_enable()

    training_args = TrainingArguments(
        output_dir=str(args.out),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=16,
        learning_rate=args.learning_rate,
        bf16=True,
        logging_steps=10,
        save_steps=200,
        save_total_limit=3,
        report_to="none",
    )
    trainer = Trainer(model=model, args=training_args, train_dataset=tokenized)
    trainer.train()
    model.save_pretrained(args.out)
    tokenizer.save_pretrained(args.out)
    print(f"Wrote SFT adapter to {args.out.resolve()}")


if __name__ == "__main__":
    main()
