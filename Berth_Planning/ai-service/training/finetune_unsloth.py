"""
SmartBerth AI - Efficient Fine-Tuning with Unsloth
Optimized for RTX 4070 Laptop GPU (8GB VRAM)

Unsloth is 2-5x faster and uses 70% less VRAM than standard training.
It downloads quantized model directly, no need for full 16GB download.
"""

import os
import json
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Check GPU
print("=" * 60)
print("SmartBerth AI - Qwen3 Fine-Tuning with Unsloth")
print("=" * 60)

if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"GPU: {gpu_name}")
    print(f"VRAM: {gpu_mem:.1f} GB")
else:
    print("ERROR: CUDA not available!")
    exit(1)

# Install unsloth if not available
try:
    from unsloth import FastLanguageModel
    from unsloth import is_bfloat16_supported
    print("✅ Unsloth loaded successfully")
except ImportError:
    print("Installing Unsloth...")
    import subprocess
    subprocess.run([
        "pip", "install", "unsloth[colab-new]@git+https://github.com/unslothai/unsloth.git",
        "--quiet"
    ])
    from unsloth import FastLanguageModel
    from unsloth import is_bfloat16_supported

from datasets import Dataset
from trl import SFTTrainer
from transformers import TrainingArguments, DataCollatorForSeq2Seq
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ========== Configuration ==========
class Config:
    # Model - Unsloth provides optimized 4-bit versions
    model_name = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit"  # Pre-quantized, ~4GB download
    
    # Alternative smaller models for faster training:
    # model_name = "unsloth/Qwen2.5-3B-Instruct-bnb-4bit"  # ~2GB, faster
    # model_name = "unsloth/Qwen2.5-1.5B-Instruct-bnb-4bit"  # ~1GB, fastest
    
    # Training data
    train_file = "training/train_chat.jsonl"
    val_file = "training/val_chat.jsonl"
    
    # Output
    output_dir = "training/output/smartberth-unsloth"
    
    # LoRA config - optimized for 8GB VRAM
    lora_r = 16
    lora_alpha = 16
    lora_dropout = 0
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"]
    
    # Training - conservative for 8GB VRAM
    max_seq_length = 2048
    per_device_train_batch_size = 2
    gradient_accumulation_steps = 4
    num_train_epochs = 3
    learning_rate = 2e-4
    warmup_steps = 50
    
    # Logging
    logging_steps = 25
    save_steps = 200


def load_training_data(config: Config):
    """Load training data from JSONL files"""
    base_path = Path(__file__).parent.parent
    
    train_path = base_path / config.train_file
    val_path = base_path / config.val_file
    
    logger.info(f"Loading training data from {train_path}")
    
    train_data = []
    with open(train_path, 'r', encoding='utf-8') as f:
        for line in f:
            train_data.append(json.loads(line))
    
    val_data = []
    if val_path.exists():
        with open(val_path, 'r', encoding='utf-8') as f:
            for line in f:
                val_data.append(json.loads(line))
    
    logger.info(f"Loaded {len(train_data)} training, {len(val_data)} validation examples")
    
    return train_data, val_data


def format_chat_template(example: Dict, tokenizer) -> Dict:
    """Format messages using Qwen chat template"""
    messages = example["messages"]
    
    # Apply the model's chat template
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )
    
    return {"text": text}


def main():
    config = Config()
    
    # Create output directory
    base_path = Path(__file__).parent.parent
    output_path = base_path / config.output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    # ========== Load Model with Unsloth ==========
    logger.info(f"Loading model: {config.model_name}")
    logger.info("This will download ~4GB (pre-quantized model)")
    
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config.model_name,
        max_seq_length=config.max_seq_length,
        dtype=None,  # Auto-detect
        load_in_4bit=True,
    )
    
    logger.info("✅ Model loaded successfully!")
    
    # ========== Add LoRA Adapters ==========
    logger.info("Adding LoRA adapters...")
    
    model = FastLanguageModel.get_peft_model(
        model,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        bias="none",
        use_gradient_checkpointing="unsloth",  # Optimized checkpointing
        random_state=42,
        use_rslora=False,
        loftq_config=None,
    )
    
    model.print_trainable_parameters()
    
    # ========== Load and Format Data ==========
    train_data, val_data = load_training_data(config)
    
    train_dataset = Dataset.from_list(train_data)
    val_dataset = Dataset.from_list(val_data) if val_data else None
    
    # Format with chat template
    logger.info("Formatting training examples...")
    train_dataset = train_dataset.map(
        lambda x: format_chat_template(x, tokenizer),
        remove_columns=train_dataset.column_names,
    )
    
    if val_dataset:
        val_dataset = val_dataset.map(
            lambda x: format_chat_template(x, tokenizer),
            remove_columns=val_dataset.column_names,
        )
    
    logger.info(f"Sample formatted text:\n{train_dataset[0]['text'][:500]}...")
    
    # ========== Training Arguments ==========
    training_args = TrainingArguments(
        output_dir=str(output_path),
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        save_total_limit=3,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        report_to="none",
    )
    
    # ========== Trainer ==========
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        dataset_text_field="text",
        max_seq_length=config.max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=training_args,
    )
    
    # ========== Train ==========
    logger.info("=" * 60)
    logger.info("Starting training...")
    logger.info(f"Total examples: {len(train_dataset)}")
    logger.info(f"Batch size: {config.per_device_train_batch_size}")
    logger.info(f"Gradient accumulation: {config.gradient_accumulation_steps}")
    logger.info(f"Effective batch size: {config.per_device_train_batch_size * config.gradient_accumulation_steps}")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    # Show GPU memory before training
    gpu_stats = torch.cuda.get_device_properties(0)
    start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
    max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
    logger.info(f"GPU memory: {start_gpu_memory} GB / {max_memory} GB")
    
    trainer.train()
    
    training_time = datetime.now() - start_time
    logger.info(f"Training completed in {training_time}")
    
    # ========== Save Model ==========
    logger.info("Saving LoRA adapters...")
    
    # Save LoRA adapters (small, ~50-100MB)
    lora_path = output_path / "lora_adapters"
    model.save_pretrained(str(lora_path))
    tokenizer.save_pretrained(str(lora_path))
    
    logger.info(f"LoRA adapters saved to: {lora_path}")
    
    # ========== Save to GGUF for Ollama ==========
    logger.info("Converting to GGUF for Ollama...")
    
    gguf_path = output_path / "gguf"
    gguf_path.mkdir(exist_ok=True)
    
    # Save as 16-bit GGUF (for Ollama)
    try:
        model.save_pretrained_gguf(
            str(gguf_path / "smartberth-finetuned"),
            tokenizer,
            quantization_method="q4_k_m"  # 4-bit quantization
        )
        logger.info(f"GGUF model saved to: {gguf_path}")
    except Exception as e:
        logger.warning(f"GGUF export failed: {e}")
        logger.info("LoRA adapters saved successfully. Manual GGUF conversion may be needed.")
    
    # ========== Save Training Info ==========
    info = {
        "model_name": config.model_name,
        "training_examples": len(train_dataset),
        "validation_examples": len(val_dataset) if val_dataset else 0,
        "epochs": config.num_train_epochs,
        "lora_r": config.lora_r,
        "lora_alpha": config.lora_alpha,
        "training_time": str(training_time),
        "completed_at": datetime.now().isoformat(),
        "output_path": str(output_path),
    }
    
    with open(output_path / "training_info.json", 'w') as f:
        json.dump(info, f, indent=2)
    
    # ========== Test Inference ==========
    logger.info("\n" + "=" * 60)
    logger.info("Testing fine-tuned model...")
    logger.info("=" * 60)
    
    # Enable fast inference
    FastLanguageModel.for_inference(model)
    
    test_prompts = [
        "What are the hard constraints for berth allocation at JNPT?",
        "How is UKC calculated for vessel transit?",
        "What factors affect ETA prediction accuracy?",
    ]
    
    for prompt in test_prompts:
        messages = [
            {"role": "system", "content": "You are SmartBerth AI, an intelligent port management assistant for JNPT."},
            {"role": "user", "content": prompt}
        ]
        
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to("cuda")
        
        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
        )
        
        response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        
        print(f"\n📝 Prompt: {prompt}")
        print(f"🤖 Response: {response[:500]}...")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Fine-tuning complete!")
    logger.info(f"Output saved to: {output_path}")
    logger.info("=" * 60)
    
    return model, tokenizer


if __name__ == "__main__":
    main()
