from __future__ import annotations
import json
import time
import subprocess
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
import torch
from vllm import SamplingParams 
from datasets import Dataset
from unsloth import FastLanguageModel
from trl import GRPOTrainer as TRLGRPOTrainer, GRPOConfig as TRLGRPOConfig, SFTTrainer, SFTConfig
from training.cli_agent.environment import CLIEnvironment, CLITask, TRAINING_TASKS
from training.train.rewards import reward_combined, set_tasks
import logging

logger = logging.getLogger("training.grpo")

# Config
@dataclass
class GRPOConfig:
    # Model
    model_name = "Qwen/Qwen2.5-Coder-3B-Instruct"
    max_seq_length = 1024
    load_in_4bit = True
    lora_rank = 32
    lora_alpha = 64
    lora_dropout = 0.05
    lora_target_modules = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

    # SFT
    sft_enabled = True
    sft_learning_rate = 2e-4
    sft_epochs = 2
    sft_batch_size = 2
    sft_warmup_steps = 5

    # GRPO
    temperature = 1.0    
    learning_rate = 5e-6
    num_generations = 8 
    batch_size = 1
    gradient_accumulation_steps = 4
    total_steps = 10000
    warmup_ratio = 0.1
    weight_decay = 0.001
    max_completion_length = 256
    kl_coeff = 0.05

    # vllm
    use_vllm = True
    gpu_memory_utilization = 0.9

    # Saving
    checkpoint_dir = "./checkpoints/cli_agent"
    save_every_steps = 500

    # Logging
    log_every_steps = 1
    print_every_steps = 5



# SFT Data — example task-command pairs to teach format
SYSTEM_PROMPT = (
    "You are a CLI expert. Given a task, output exactly the shell commands required. "
    "No explanation, no markdown, no backticks. "
)

# These are gold-standard examples for SFT
SFT_EXAMPLES = [
    ("Count the number of lines in /tmp/data/log.txt", "wc -l < /tmp/data/log.txt"),
    ("List all files in the current directory", "ls -la"),
    ("Find all .py files in /home", "find /home -name '*.py'"),
    ("Show disk usage in human-readable format", "df -h"),
    ("Search for the word ERROR in /var/log/syslog", "grep 'ERROR' /var/log/syslog"),
    ("Sort /tmp/names.txt alphabetically and remove duplicates", "sort -u /tmp/names.txt"),
    ("Show the top 5 processes by memory usage", "ps aux --sort=-%mem | head -6"),
    ("Count how many .txt files are in /tmp", "find /tmp -name '*.txt' | wc -l"),
    ("Display the last 20 lines of /var/log/auth.log", "tail -20 /var/log/auth.log"),
    ("Show current memory usage", "free -m"),
    ("Find files modified in the last 24 hours in /tmp", "find /tmp -mtime -1"),
    ("Extract the second column from a space-separated file", "awk '{print $2}' /tmp/data.txt"),
    ("Create directories src, tests, and docs under /tmp/project", "mkdir -p /tmp/project/{src,tests,docs}"),
    ("Sum all numbers in /tmp/numbers.txt", "awk '{s+=$1} END {print s}' /tmp/numbers.txt"),
    ("Show the 10 largest files in /tmp", "du -ah /tmp | sort -rh | head -10"),
    ("Check which process is using port 8080", "lsof -i :8080"),
    ("Find all empty files in /tmp", "find /tmp -empty -type f"),
    ("Replace all occurrences of foo with bar in /tmp/config.txt", "sed -i 's/foo/bar/g' /tmp/config.txt"),
    ("Show environment variables containing PATH", "env | grep PATH"),
    ("Compress /tmp/logs into a tar.gz archive", "tar -czf /tmp/logs.tar.gz /tmp/logs"),
]

# SFT data
def build_sft_dataset(tokenizer, max_seq_length):
    messages_list = []

    for task, command in SFT_EXAMPLES:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
            {"role": "assistant", "content": command},
        ]
        messages_list.append(messages)

    texts = [
        tokenizer.apply_chat_template(m, tokenize=False)
        for m in messages_list
    ]

    # Filter by length
    dataset = Dataset.from_dict({"text": texts})
    dataset = dataset.filter(
        lambda x: len(tokenizer(x["text"])["input_ids"]) <= max_seq_length
    )

    logger.info(f"SFT dataset: {len(dataset)} examples")
    return dataset



# GRPO data
def build_grpo_dataset(tasks: list[CLITask], tokenizer, max_prompt_length):
    prompts = []
    answers = []
    task_ids = []

    for task in tasks:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task.description},
        ]
        prompts.append(messages)
        answers.append(task.expected_output)
        task_ids.append(task.task_id)

    dataset = Dataset.from_dict({
        "prompt": prompts,
        "answer": answers,
        "task_id": task_ids,
    })

    # Filter by token length
    tokenized = dataset.map(
        lambda x: {
            "tokens": tokenizer.apply_chat_template(
                x["prompt"], add_generation_prompt=True, tokenize=True
            )
        },
        batched=True,
    )
    tokenized = tokenized.map(lambda x: {"L": len(x["tokens"])})
    dataset = dataset.select(
        np.where(np.array(tokenized["L"]) <= max_prompt_length)[0]
    )

    logger.info(f"GRPO dataset: {len(dataset)} prompts from {len(tasks)} tasks")
    return dataset

# Trainer
class UnslothGRPOTrainer:
    """uses SFT for format, GRPO for quality."""

    def __init__(self,config: GRPOConfig = None,tasks: Optional[list[CLITask]] = None):
        self.config = config or GRPOConfig()
        self.tasks = tasks or TRAINING_TASKS

        # Update the task list for reward functions
        set_tasks(self.tasks)

        # Load model with unsloth
        logger.info(f"Loading model: {self.config.model_name}")

        model_kwargs = {
            "model_name": self.config.model_name,
            "max_seq_length": self.config.max_seq_length,
            "load_in_4bit": self.config.load_in_4bit,
            "dtype": None,
        }

        if self.config.use_vllm:
            model_kwargs["fast_inference"] = True
            model_kwargs["max_lora_rank"] = self.config.lora_rank
            model_kwargs["gpu_memory_utilization"] = self.config.gpu_memory_utilization

        self.model, self.tokenizer = FastLanguageModel.from_pretrained(**model_kwargs)

        # lora
        self.model = FastLanguageModel.get_peft_model(
            self.model,
            r=self.config.lora_rank,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.lora_target_modules,
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=3407,
        )

        Path(self.config.checkpoint_dir).mkdir(parents=True, exist_ok=True)
        logger.info("Model loaded and LoRA applied")

    def train(self):
        """Run both training phases."""
        self.run_sft()
        self.run_grpo()

    # SFT
    def run_sft(self):
        """Supervised fine-tuning to teach output format."""
        logger.info("=" * 60)
        logger.info("Phase 1: SFT — teaching output format")
        logger.info("=" * 60)

        dataset = build_sft_dataset(self.tokenizer, self.config.max_seq_length)

        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=dataset,
            args=SFTConfig(
                dataset_text_field="text",
                per_device_train_batch_size=self.config.sft_batch_size,
                gradient_accumulation_steps=1,
                warmup_steps=self.config.sft_warmup_steps,
                num_train_epochs=self.config.sft_epochs,
                learning_rate=self.config.sft_learning_rate,
                logging_steps=5,
                optim="adamw_8bit",
                weight_decay=0.001,
                seed=3407,
                output_dir=f"{self.config.checkpoint_dir}/sft",
                report_to="none",
            ),
        )

        trainer.train()
        logger.info("SFT phase complete")

    # GRPO
    def run_grpo(self):
        """GRPO training for command quality."""
        logger.info("=" * 60)
        logger.info("Phase 2: GRPO — improving command quality")
        logger.info("=" * 60)

        # Compute prompt length
        max_prompt_length = self.config.max_seq_length - self.config.max_completion_length

        dataset = build_grpo_dataset(self.tasks, self.tokenizer, max_prompt_length)

        # vLLM sampling params
        grpo_kwargs = {}
        if self.config.use_vllm:
            grpo_kwargs["vllm_sampling_params"] = SamplingParams(
                min_p=0.1,
                top_p=1.0,
                top_k=-1,
                seed=3407,
                stop=[self.tokenizer.eos_token],
                include_stop_str_in_output=True,
            )

        training_args = TRLGRPOConfig(
            **grpo_kwargs,
            temperature=self.config.temperature,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            warmup_ratio=self.config.warmup_ratio,
            lr_scheduler_type="linear",
            optim="adamw_8bit",
            logging_steps=self.config.log_every_steps,
            per_device_train_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            num_generations=self.config.num_generations,
            max_prompt_length=max_prompt_length,
            max_completion_length=self.config.max_completion_length,
            max_steps=self.config.total_steps,
            save_steps=self.config.save_every_steps,
            save_total_limit=3,
            output_dir=self.config.checkpoint_dir,
            remove_unused_columns=False,
            beta=self.config.kl_coeff,
        )

        trainer = TRLGRPOTrainer(
            model=self.model,
            processing_class=self.tokenizer,
            reward_funcs=reward_combined,
            args=training_args,
            train_dataset=dataset,
        )

        trainer.train()
        logger.info("GRPO phase complete")

    # saving weights
    def save_merged(self, quantization):
        """Save fully merged model for deployment."""
        save_path = f"{self.config.checkpoint_dir}/merged"
        logger.info(f"Saving merged model ({quantization}): {save_path}")

        self.model.save_pretrained_gguf(save_path, self.tokenizer, quantization_method=quantization)

        logger.info(f"Merged model saved: {save_path}")