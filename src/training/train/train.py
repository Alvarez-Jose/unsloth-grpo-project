from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from training.cli_agent.environment import TRAINING_TASKS
from training.train.grpo_trainer import UnslothGRPOTrainer, GRPOConfig
from training.utils import load_config, setup_logging

logger = setup_logging("training")


def main():
    config = load_config("configs/agent_config.yaml")
    train_cfg = config.get("training", {}).get("grpo", {})
    sft_cfg = config.get("training", {}).get("sft", {})
    lora_cfg = config.get("training", {}).get("lora", {})
    cli_cfg = config.get("cli_agent", {}).get("policy", {})
    ckpt_cfg = config.get("training", {}).get("checkpointing", {})
    log_cfg = config.get("training", {}).get("logging", {})
    save_cfg = config.get("training", {}).get("saving", {})

    grpo_config = GRPOConfig(
        # Model
        model_name=cli_cfg.get("model_name", "Qwen/Qwen2.5-Coder-3B-Instruct"),
        max_seq_length=cli_cfg.get("max_seq_length", 1024),
        load_in_4bit=cli_cfg.get("load_in_4bit", True),
        lora_rank=lora_cfg.get("r", 32),
        lora_alpha=lora_cfg.get("alpha", 64),
        lora_dropout=lora_cfg.get("dropout", 0.05),

        # SFT
        sft_enabled=sft_cfg.get("enabled", True),
        sft_learning_rate=sft_cfg.get("learning_rate", 2e-4),
        sft_epochs=sft_cfg.get("epochs", 2),
        sft_batch_size=sft_cfg.get("batch_size", 2),
        sft_warmup_steps=sft_cfg.get("warmup_steps", 5),

        # GRPO
        temperature=train_cfg.get("temperature", 1.0),
        learning_rate=train_cfg.get("learning_rate", 5e-6),
        num_generations=train_cfg.get("group_size", 8),
        batch_size=train_cfg.get("batch_size", 1),
        gradient_accumulation_steps=train_cfg.get("gradient_accumulation_steps", 4),
        total_steps=train_cfg.get("total_steps", 10000),
        warmup_ratio=train_cfg.get("warmup_ratio", 0.1),
        weight_decay=train_cfg.get("weight_decay", 0.001),
        max_completion_length=train_cfg.get("max_completion_length", 256),
        kl_coeff=train_cfg.get("kl_coeff", 0.05),

        # vLLM
        use_vllm=train_cfg.get("use_vllm", True),
        gpu_memory_utilization=train_cfg.get("gpu_memory_utilization", 0.9),

        # Saving
        checkpoint_dir=ckpt_cfg.get("checkpoint_dir", "./checkpoints/cli_agent"),
        save_every_steps=ckpt_cfg.get("save_every_steps", 500),

        # Logging
        log_every_steps=log_cfg.get("log_every_steps", 1),
        print_every_steps=log_cfg.get("print_every_steps", 5),
    )

    trainer = UnslothGRPOTrainer(
        config=grpo_config,
        tasks=TRAINING_TASKS,
    )

    print("ready to train")
    '''
    try:
        trainer.train()
    except KeyboardInterrupt:
        logger.info("Training interrupted — saving checkpoint...")
        trainer.save(f"{grpo_config.checkpoint_dir}/interrupted")
        logger.info("Checkpoint saved.")
        return

    # Save final model
    trainer.save()

    # Save merged if configured
    if save_cfg.get("merge_on_complete", False):
        trainer.save_merged(
            quantization=save_cfg.get("merge_format", "q4_k_m")
        )

    logger.info("Done")
    '''


if __name__ == "__main__":
    main()