"""
SmartBerth AI - Qwen3 Fine-Tuning with LoRA
Uses PEFT and bitsandbytes for efficient GPU-accelerated training

Optimized for RTX 4070 Laptop GPU (8GB VRAM)
"""

import os
import json
import torch
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

# Transformers and PEFT
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
from datasets import Dataset, load_dataset

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== Configuration ==========
@dataclass
class TrainingConfig:
    """Configuration for Qwen3 LoRA fine-tuning"""
    
    # Model
    model_name: str = "Qwen/Qwen3-8B"  # Base model
    model_local_path: Optional[str] = None  # Optional local path
    
    # Training data
    train_file: str = "training/train_chat.jsonl"
    val_file: str = "training/val_chat.jsonl"
    
    # Output
    output_dir: str = "training/output/smartberth-qwen3-lora"
    
    # LoRA Configuration
    lora_r: int = 16  # LoRA rank
    lora_alpha: int = 32  # LoRA alpha (usually 2x r)
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
        "gate_proj", "up_proj", "down_proj",  # MLP
    ])
    
    # Quantization (for 8GB VRAM)
    load_in_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    bnb_4bit_use_double_quant: bool = True
    
    # Training hyperparameters
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.1
    weight_decay: float = 0.01
    max_seq_length: int = 2048
    
    # Optimization
    optim: str = "paged_adamw_8bit"  # Memory-efficient optimizer
    gradient_checkpointing: bool = True
    fp16: bool = True
    bf16: bool = False  # Set True if GPU supports it
    
    # Logging
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100
    save_total_limit: int = 3


# ========== Data Processing ==========
def load_training_data(config: TrainingConfig):
    """Load and preprocess training data"""
    base_path = Path(__file__).parent.parent
    
    train_path = base_path / config.train_file
    val_path = base_path / config.val_file
    
    logger.info(f"Loading training data from {train_path}")
    logger.info(f"Loading validation data from {val_path}")
    
    train_data = []
    with open(train_path, 'r', encoding='utf-8') as f:
        for line in f:
            train_data.append(json.loads(line))
    
    val_data = []
    with open(val_path, 'r', encoding='utf-8') as f:
        for line in f:
            val_data.append(json.loads(line))
    
    logger.info(f"Loaded {len(train_data)} training examples, {len(val_data)} validation examples")
    
    return Dataset.from_list(train_data), Dataset.from_list(val_data)


def format_chat_messages(example: Dict, tokenizer) -> str:
    """Format chat messages using the Qwen3 chat template"""
    messages = example["messages"]
    
    # Apply chat template
    formatted = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )
    
    return {"text": formatted}


def tokenize_function(examples, tokenizer, max_length):
    """Tokenize the formatted text"""
    result = tokenizer(
        examples["text"],
        truncation=True,
        max_length=max_length,
        padding=False,
        return_tensors=None,
    )
    
    # Create labels (same as input_ids for causal LM)
    result["labels"] = result["input_ids"].copy()
    
    return result


# ========== Model Setup ==========
def setup_model_and_tokenizer(config: TrainingConfig):
    """Setup model with quantization and LoRA"""
    
    # BitsAndBytes configuration for 4-bit quantization
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=config.load_in_4bit,
        bnb_4bit_compute_dtype=getattr(torch, config.bnb_4bit_compute_dtype),
        bnb_4bit_quant_type=config.bnb_4bit_quant_type,
        bnb_4bit_use_double_quant=config.bnb_4bit_use_double_quant,
    )
    
    model_path = config.model_local_path or config.model_name
    logger.info(f"Loading model: {model_path}")
    
    # Load model with quantization
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        trust_remote_code=True,
        padding_side="right",
    )
    
    # Add padding token if not present
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(
        model, 
        use_gradient_checkpointing=config.gradient_checkpointing
    )
    
    # LoRA configuration
    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    
    # Apply LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, tokenizer


# ========== Training ==========
def train(config: TrainingConfig):
    """Main training function"""
    
    logger.info("="*60)
    logger.info("SmartBerth AI - Qwen3 LoRA Fine-Tuning")
    logger.info("="*60)
    
    # Setup paths
    base_path = Path(__file__).parent.parent
    output_path = base_path / config.output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load model and tokenizer
    model, tokenizer = setup_model_and_tokenizer(config)
    
    # Load data
    train_dataset, val_dataset = load_training_data(config)
    
    # Format messages
    logger.info("Formatting training examples...")
    train_dataset = train_dataset.map(
        lambda x: format_chat_messages(x, tokenizer),
        remove_columns=train_dataset.column_names,
    )
    val_dataset = val_dataset.map(
        lambda x: format_chat_messages(x, tokenizer),
        remove_columns=val_dataset.column_names,
    )
    
    # Tokenize
    logger.info("Tokenizing...")
    train_dataset = train_dataset.map(
        lambda x: tokenize_function(x, tokenizer, config.max_seq_length),
        batched=False,
        remove_columns=["text"],
    )
    val_dataset = val_dataset.map(
        lambda x: tokenize_function(x, tokenizer, config.max_seq_length),
        batched=False,
        remove_columns=["text"],
    )
    
    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        return_tensors="pt",
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_path),
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_ratio=config.warmup_ratio,
        weight_decay=config.weight_decay,
        optim=config.optim,
        fp16=config.fp16,
        bf16=config.bf16,
        gradient_checkpointing=config.gradient_checkpointing,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        eval_strategy="steps",
        eval_steps=config.eval_steps,
        save_total_limit=config.save_total_limit,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",  # Disable wandb/tensorboard
        dataloader_pin_memory=False,  # Save memory
        remove_unused_columns=False,
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )
    
    # Train
    logger.info("Starting training...")
    start_time = datetime.now()
    
    trainer.train()
    
    training_time = datetime.now() - start_time
    logger.info(f"Training completed in {training_time}")
    
    # Save final model
    logger.info("Saving model...")
    trainer.save_model(str(output_path / "final"))
    tokenizer.save_pretrained(str(output_path / "final"))
    
    # Save training config
    config_dict = {
        "training_config": config.__dict__,
        "training_time": str(training_time),
        "completed_at": datetime.now().isoformat(),
    }
    with open(output_path / "training_info.json", 'w') as f:
        json.dump(config_dict, f, indent=2, default=str)
    
    logger.info(f"Model saved to {output_path / 'final'}")
    logger.info("="*60)
    
    return trainer


# ========== Inference ==========
def test_inference(model, tokenizer, prompt: str):
    """Test inference with the fine-tuned model"""
    messages = [
        {"role": "system", "content": "You are SmartBerth AI, an intelligent assistant specialized in port berth planning and optimization."},
        {"role": "user", "content": prompt}
    ]
    
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
        )
    
    response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
    return response


def main():
    """Main entry point"""
    
    # Check GPU
    if not torch.cuda.is_available():
        logger.error("CUDA not available! GPU required for training.")
        return
    
    logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
    logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Training configuration
    config = TrainingConfig()
    
    # Start training
    trainer = train(config)
    
    # Test inference
    logger.info("\n" + "="*60)
    logger.info("Testing inference...")
    logger.info("="*60)
    
    test_prompts = [
        "What are the specifications of berth JNPT-CT01?",
        "Can a vessel with LOA 350m and draft 14.5m berth at a berth with max LOA 320m?",
        "What factors affect ETA prediction?",
    ]
    
    for prompt in test_prompts:
        logger.info(f"\nPrompt: {prompt}")
        response = test_inference(trainer.model, trainer.tokenizer, prompt)
        logger.info(f"Response: {response}\n")


if __name__ == "__main__":
    main()
