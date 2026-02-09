"""
SmartBerth AI - Lightweight Fine-Tuning Script
Uses Qwen2.5-1.5B-Instruct for fast fine-tuning on 8GB VRAM

This script:
1. Downloads a small model (~1.5GB) instead of 16GB
2. Uses QLoRA with 4-bit quantization
3. Can complete training in ~30-60 minutes on RTX 4070
"""

import os
import json
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, List

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check GPU
print("=" * 60)
print("SmartBerth AI - Lightweight Fine-Tuning")
print("=" * 60)

if not torch.cuda.is_available():
    print("ERROR: CUDA not available!")
    exit(1)

gpu_name = torch.cuda.get_device_name(0)
gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
print(f"GPU: {gpu_name}")
print(f"VRAM: {gpu_mem:.1f} GB")

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    BitsAndBytesConfig,
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType,
)
from datasets import Dataset


# ========== Configuration ==========
class Config:
    # Use smaller model - downloads ~1.5GB instead of 16GB
    model_name = "Qwen/Qwen2.5-1.5B-Instruct"  # Small but capable
    
    # Alternative: 3B for better quality (~2GB download)
    # model_name = "Qwen/Qwen2.5-3B-Instruct"
    
    # Training data
    train_file = "training/train_chat.jsonl"
    val_file = "training/val_chat.jsonl"
    
    # Output
    output_dir = "training/output/smartberth-qwen-1.5b"
    
    # LoRA config
    lora_r = 16
    lora_alpha = 32
    lora_dropout = 0.05
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"]
    
    # Training - optimized for 8GB VRAM
    max_seq_length = 1024  # Shorter for faster training
    per_device_train_batch_size = 2
    gradient_accumulation_steps = 4
    num_train_epochs = 2
    learning_rate = 2e-4
    warmup_ratio = 0.1
    
    # Quantization
    load_in_4bit = True
    
    # Logging
    logging_steps = 50
    save_steps = 200


def load_training_data(config: Config):
    """Load training data"""
    base_path = Path(__file__).parent.parent
    
    train_path = base_path / config.train_file
    val_path = base_path / config.val_file
    
    logger.info(f"Loading training data from {train_path}")
    
    train_data = []
    with open(train_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 2000:  # Limit for faster training
                break
            train_data.append(json.loads(line))
    
    val_data = []
    with open(val_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 200:  # Limit validation
                break
            val_data.append(json.loads(line))
    
    logger.info(f"Loaded {len(train_data)} training, {len(val_data)} validation examples")
    
    return train_data, val_data


def format_chat(example: Dict, tokenizer) -> Dict:
    """Format using chat template"""
    messages = example["messages"]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )
    return {"text": text}


def tokenize(examples, tokenizer, max_length):
    """Tokenize text"""
    result = tokenizer(
        examples["text"],
        truncation=True,
        max_length=max_length,
        padding=False,
    )
    result["labels"] = result["input_ids"].copy()
    return result


def main():
    config = Config()
    
    # Output directory
    base_path = Path(__file__).parent.parent
    output_path = base_path / config.output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    # ========== Quantization Config ==========
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    
    # ========== Load Model ==========
    logger.info(f"Loading model: {config.model_name}")
    logger.info("Downloading ~1.5GB model...")
    
    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    
    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name,
        trust_remote_code=True,
        padding_side="right",
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    logger.info("✅ Model loaded!")
    
    # ========== Prepare for Training ==========
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # ========== Load Data ==========
    train_data, val_data = load_training_data(config)
    
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data)
    
    # Format
    logger.info("Formatting examples...")
    train_dataset = train_dataset.map(
        lambda x: format_chat(x, tokenizer),
        remove_columns=train_dataset.column_names,
    )
    val_dataset = val_dataset.map(
        lambda x: format_chat(x, tokenizer),
        remove_columns=val_dataset.column_names,
    )
    
    # Tokenize
    logger.info("Tokenizing...")
    train_dataset = train_dataset.map(
        lambda x: tokenize(x, tokenizer, config.max_seq_length),
        remove_columns=["text"],
    )
    val_dataset = val_dataset.map(
        lambda x: tokenize(x, tokenizer, config.max_seq_length),
        remove_columns=["text"],
    )
    
    # ========== Training ==========
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
    )
    
    training_args = TrainingArguments(
        output_dir=str(output_path),
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        weight_decay=0.01,
        optim="paged_adamw_8bit",
        fp16=True,
        gradient_checkpointing=True,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        eval_strategy="steps",
        eval_steps=config.save_steps,
        save_total_limit=2,
        load_best_model_at_end=True,
        report_to="none",
        remove_unused_columns=False,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )
    
    # Show memory usage
    logger.info(f"GPU Memory: {torch.cuda.max_memory_allocated() / 1024**3:.2f} GB allocated")
    
    logger.info("=" * 60)
    logger.info("Starting training...")
    logger.info(f"Examples: {len(train_dataset)}")
    logger.info(f"Epochs: {config.num_train_epochs}")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    trainer.train()
    training_time = datetime.now() - start_time
    
    logger.info(f"Training completed in {training_time}")
    
    # ========== Save ==========
    logger.info("Saving model...")
    trainer.save_model(str(output_path / "final"))
    tokenizer.save_pretrained(str(output_path / "final"))
    
    # Save info
    info = {
        "model": config.model_name,
        "examples": len(train_dataset),
        "epochs": config.num_train_epochs,
        "training_time": str(training_time),
        "completed": datetime.now().isoformat(),
    }
    with open(output_path / "training_info.json", 'w') as f:
        json.dump(info, f, indent=2)
    
    logger.info(f"✅ Saved to: {output_path / 'final'}")
    
    # ========== Test ==========
    logger.info("\nTesting fine-tuned model...")
    
    test_prompt = "What are the hard constraints for berth allocation at JNPT?"
    messages = [
        {"role": "system", "content": "You are SmartBerth AI, an intelligent port management assistant."},
        {"role": "user", "content": test_prompt}
    ]
    
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to("cuda")
    
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
        )
    
    response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
    
    print(f"\n📝 Prompt: {test_prompt}")
    print(f"🤖 Response: {response}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Fine-tuning complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
