<!--
  STARTER README for github.com/Alvarez-Jose/unsloth-grpo-project
  This repo currently has no description; this draft assumes it's a GRPO fine-tuning experiment using Unsloth.
  Personalize the bracketed sections, then drop into the repo as README.md.
-->

# unsloth-grpo-project

> Group Relative Policy Optimization (GRPO) fine-tuning experiments on small open models using [Unsloth](https://github.com/unslothai/unsloth) for memory-efficient training.

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch&logoColor=white)
![HuggingFace](https://img.shields.io/badge/Transformers-TRL-FFD21E?logo=huggingface&logoColor=black)
![Unsloth](https://img.shields.io/badge/Unsloth-2x_faster-2ECC71)

## What it does

- Fine-tunes [REPLACE: e.g., Qwen-2.5-0.5B / Llama-3.2-1B] with **GRPO** using TRL + Unsloth
- Reward function: [REPLACE: e.g., format-correctness + numeric accuracy on GSM8K-style problems]
- Tracks reward, KL divergence, and length penalties across rollout batches
- Designed to run on a single consumer GPU ([REPLACE: e.g., RTX 4090 24GB])

## Why GRPO

GRPO removes the value model from PPO and instead computes advantages from group-relative rewards. That's significantly cheaper — both in memory and in compute — than PPO with a separate critic, which makes it tractable on commodity hardware. This repo is my hands-on study of *what actually changes* when you train this way: reward stability, mode collapse, and the effect of group size.

## Results

<!-- Replace with your actual numbers when you have them. -->

| Setup | Reward (held-out) | KL to base | GPU hours |
|---|---|---|---|
| Base model | [REPLACE] | — | — |
| GRPO, group size 4 | [REPLACE] | [REPLACE] | [REPLACE] |
| GRPO, group size 8 | **[REPLACE]** | [REPLACE] | [REPLACE] |

## Quick start

```bash
git clone https://github.com/Alvarez-Jose/unsloth-grpo-project
cd unsloth-grpo-project
pip install -r requirements.txt
python train_grpo.py --config configs/[REPLACE].yaml
```

## Repo layout

```
.
├── train_grpo.py        # GRPO training loop using TRL + Unsloth
├── reward.py            # task-specific reward function
├── configs/             # YAML configs per experiment
├── runs/                # checkpoints + logs (gitignored)
└── notebooks/           # eval + analysis
```

## References

- [Shao et al., 2024 — DeepSeekMath / GRPO](https://arxiv.org/abs/2402.03300)
- [TRL GRPOTrainer docs](https://huggingface.co/docs/trl/grpo_trainer)
- [Unsloth](https://github.com/unslothai/unsloth)

## License

MIT — see [`LICENSE`](LICENSE).

---

**Author:** Antonio Alvarez Maciel · M.S. NLP, UC Santa Cruz · [LinkedIn](https://linkedin.com/in/jose-alvarez-maciel)
