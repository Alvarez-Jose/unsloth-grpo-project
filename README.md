# unsloth-grpo-project

> Extending [@Carson1829](https://github.com/Carson1829)'s GRPO training section with my own testing, infrastructure, and trained model artifacts on Hugging Face. GRPO fine-tuning of Llama-3-8B via [Unsloth](https://github.com/unslothai/unsloth) + [TRL](https://github.com/huggingface/trl).

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch&logoColor=white)
![HuggingFace](https://img.shields.io/badge/Transformers-TRL-FFD21E?logo=huggingface&logoColor=black)
![Unsloth](https://img.shields.io/badge/Unsloth-2x_faster-2ECC71)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Origin and credit

This repository is the **GRPO training portion** that I split out and extended from a larger team project. The core GRPO training scaffolding was authored by my teammate **[@Carson1829](https://github.com/Carson1829)**; I forked that section to do my own testing, infrastructure work, and produce trained model artifacts.

The wider multi-agent desktop assistant this fed into lives in a private team repository (`Visualtaggy/project_cortex`).

## What I contributed

- **Trained model artifacts** — two LoRA adapters fine-tuned with GRPO on `unsloth/llama-3-8b-Instruct`, both published on Hugging Face (see below).
- **GUI / Tkinter wrapper** so the training + inference loop is driveable without dropping to a terminal.
- **Docker + Northflank deployment** path so the trained adapter can run as a hosted endpoint instead of requiring a local GPU at inference time.
- **Requirements / integration tightening** — pinned dependency versions, fixed CUDA/bnb/peft compatibility issues, made the training script reproducible end-to-end on a single consumer GPU.
- **Training runs** that produced the published model artifacts (see Hugging Face links).

## Trained models

| Model | Base | Method | License | Link |
|---|---|---|---|---|
| `jalva182/cli-agent-model` | `unsloth/llama-3-8b-Instruct` | GRPO + LoRA (TRL via Unsloth) | Apache-2.0 | [huggingface.co/jalva182/cli-agent-model](https://huggingface.co/jalva182/cli-agent-model) |
| `jalva182/cli-agent-model-gpu1` | `unsloth/llama-3-8b-Instruct` (4-bit bnb variant in PEFT config) | GRPO + LoRA (TRL via Unsloth) | Apache-2.0 *(to be set on the model card)* | [huggingface.co/jalva182/cli-agent-model-gpu1](https://huggingface.co/jalva182/cli-agent-model-gpu1) |

Both are PEFT/LoRA adapters — load them on top of the Llama-3-8B-Instruct base model.

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = "unsloth/llama-3-8b-Instruct"
model = AutoModelForCausalLM.from_pretrained(base)
tok = AutoTokenizer.from_pretrained(base)
model = PeftModel.from_pretrained(model, "jalva182/cli-agent-model")
```

## Why GRPO

GRPO drops the value model from PPO and instead computes advantages from group-relative rewards. That's significantly cheaper — both in memory and in compute — than PPO with a separate critic, which makes it tractable on commodity hardware. This repo is my hands-on study of *what actually changes* when you train this way: reward stability, mode collapse, and the effect of group size.

## Quick start

```bash
git clone https://github.com/Alvarez-Jose/unsloth-grpo-project
cd unsloth-grpo-project
pip install -r requirements.txt
python train_grpo.py --config configs/llama3-8b-grpo.yaml
```

## References

- [Shao et al., 2024 — DeepSeekMath / GRPO](https://arxiv.org/abs/2402.03300)
- [TRL `GRPOTrainer` docs](https://huggingface.co/docs/trl/grpo_trainer)
- [Unsloth](https://github.com/unslothai/unsloth)

## License

MIT — see [`LICENSE`](LICENSE).

---

**Author:** Antonio Alvarez Maciel · M.S. NLP, UC Santa Cruz · [LinkedIn](https://linkedin.com/in/jose-alvarez-maciel) · [Email](mailto:jalva182@ucsc.edu)
**Credit:** Original GRPO training scaffolding by [@Carson1829](https://github.com/Carson1829). This repo extends that work.
