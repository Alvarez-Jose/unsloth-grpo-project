#!/usr/bin/env python3
import os, sys
import torch

# Multi-GPU setup
os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'
os.environ['TORCHDYNAMO_CACHE_SIZE_LIMIT'] = '4096'

# Disable dynamo to prevent recompile crashes
torch._dynamo.config.disable = True

from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.training.train.grpo_trainer import UnslothGRPOTrainer, GRPOConfig
from src.training.train.training_data import TRAINING_TASKS
import yaml

def main():
    print("=" * 60)
    print(f"GPUs available: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    print("=" * 60)

    with open('src/training/configs/agent_config.yaml') as f:
        config_dict = yaml.safe_load(f)

    grpo_config = GRPOConfig(
        model_name=config_dict['cli_agent']['policy']['model_name'],
        max_seq_length=512,
        load_in_4bit=False,
        temperature=config_dict['training']['grpo']['temperature'],
        learning_rate=3e-6,
        num_generations=config_dict['training']['grpo']['group_size'],
        batch_size=2,
        gradient_accumulation_steps=2,
        total_steps=10000,
        warmup_ratio=config_dict['training']['grpo']['warmup_ratio'],
        kl_coeff=config_dict['training']['grpo']['kl_coeff'],
        use_vllm=True,
        gpu_memory_utilization=0.70,
        checkpoint_dir='./checkpoints/cli_agent/interrupted/checkpoint-4500',
        save_every_steps=250,
    save_total_limit=2,
    )

    save_dir = "./checkpoints/cli_agent/final_run"
    os.makedirs(save_dir, exist_ok=True)

    trainer = UnslothGRPOTrainer(config=grpo_config, tasks=TRAINING_TASKS)
    if hasattr(trainer, 'args'):
        trainer.args.output_dir = save_dir
        trainer.args.save_steps = 250
        trainer.args.per_device_train_batch_size = 1

    trainer.run_grpo()

if __name__ == "__main__":
    main()
