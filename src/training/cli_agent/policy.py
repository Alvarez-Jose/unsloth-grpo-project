"""Policy network for the CLI agent.

Uses a causal language model (e.g. GPT-2) as the backbone. The model
takes in the task description + shell history and generates the next
shell command autoregressively.

The policy is fine-tuned with GRPO — no separate value head needed
since GRPO uses group-relative advantages instead of a learned baseline.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions import Categorical
from typing import Optional
from dataclasses import dataclass

from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedModel, PreTrainedTokenizer


@dataclass
class PolicyOutput:
    """Output from a forward pass of the policy."""
    command: str                        # decoded command string
    token_ids: torch.LongTensor         # generated token IDs
    log_probs: torch.FloatTensor        # log probs of each generated token
    entropy: torch.FloatTensor          # per-token entropy
    prompt_length: int                  # length of the prompt (for masking)


class CLIPolicy(nn.Module):
    def __init__(
        self,
        model_name="Qwen/Qwen2.5-Coder-3B-Instruct",
        max_seq_length = 512,
        load_in_4bit = False,
    ):
        super().__init__()
        self.model_name = model_name
        self.max_seq_length = max_seq_length

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


        # Load backbone — support 4-bit quantization for memory efficiency
        self.tokenizer: PreTrainedTokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True
        )

        model_kwargs = {"trust_remote_code": True}
        if load_in_4bit:
            from transformers import BitsAndBytesConfig
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
            )
            model_kwargs["device_map"] = "auto"
        else:
            model_kwargs["torch_dtype"] = torch.float16

        self.model: PreTrainedModel = AutoModelForCausalLM.from_pretrained(
            model_name, **model_kwargs
        )

        # Set pad token if missing
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.tokenizer.eos_token_id

    def format_prompt(self, task_description: str, history: list[dict]) -> str:
        """Format the observation into the model's expected prompt format.

        Uses a chat-style format compatible with Qwen2.5-Coder-Instruct.
        Falls back to special-token format if the tokenizer doesn't
        support chat templates.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a CLI expert. Given a task, output exactly the shell commands required. "
                    "No explanation, no markdown, no backticks. "
                ),
            },
        ]

        # Build conversation from history
        user_msg = f"TASK: {task_description}"
        if history:
            for entry in history:
                user_msg += f"\n$ {entry['command']}\n{entry['output'][:200]}"
            user_msg += "\n\nWhat is the next command?"

        messages.append({"role": "user", "content": user_msg})

        # Try to use the tokenizer's chat template
        try:
            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
        except Exception:
            # Fallback to special-token format
            parts = [f"<|TASK|> {task_description}"]
            for entry in history:
                parts.append(f"<|CMD|> {entry['command']}")
                parts.append(f"<|OUTPUT|> {entry['output'][:200]}")
            parts.append("<|CMD|>")
            prompt = "\n".join(parts)

        return prompt

    @torch.no_grad()
    def generate_command(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_new_tokens: int = 64,
        top_p: float = 0.9,
    ) -> PolicyOutput:
        """Generate a single command from the prompt (inference mode)."""
        return self._generate(
            prompt,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
            top_p=top_p,
        )


    def _generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_new_tokens: int = 64,
        top_p: float = 0.9,
    ) -> PolicyOutput:
        """Core generation logic."""
        # Tokenize prompt
        encoding = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_seq_length - max_new_tokens,
        ).to(self.device)

        input_ids = encoding["input_ids"]
        prompt_length = input_ids.shape[1]

        # Generate token by token (for per-token log probs)
        generated_ids = []
        all_log_probs = []
        all_entropy = []

        current_ids = input_ids

        self.model.eval()

        for _ in range(max_new_tokens):
            outputs = self.model(current_ids)
            next_logits = outputs.logits[:, -1, :] / temperature

            # Top-p filtering
            if top_p < 1.0:
                next_logits = self._top_p_filter(next_logits, top_p)

            probs = F.softmax(next_logits, dim=-1)
            dist = Categorical(probs)
            next_token = dist.sample()

            log_prob = dist.log_prob(next_token)
            entropy = dist.entropy()

            generated_ids.append(next_token)
            all_log_probs.append(log_prob)
            all_entropy.append(entropy)

            # Stop on EOS or newline (commands are single-line)
            if next_token.item() == self.tokenizer.eos_token_id:
                break
            decoded_so_far = self.tokenizer.decode(
                [t.item() for t in generated_ids], skip_special_tokens=True
            )
            if "\n" in decoded_so_far:
                break

            next_token = next_token.unsqueeze(-1)
            current_ids = torch.cat([current_ids, next_token], dim=1)

        # Decode the command
        if generated_ids:
            token_ids = torch.stack(generated_ids).squeeze(-1)
            command = self.tokenizer.decode(token_ids, skip_special_tokens=True).strip()
            log_probs = torch.stack(all_log_probs).squeeze(-1)
            entropy = torch.stack(all_entropy).squeeze(-1)
        else:
            token_ids = torch.tensor([], dtype=torch.long, device=self.device)
            command = ""
            log_probs = torch.tensor([], dtype=torch.float, device=self.device)
            entropy = torch.tensor([], dtype=torch.float, device=self.device)

        # Clean up: take first line, strip special tokens
        command = command.split("\n")[0].strip()

        return PolicyOutput(
            command=command,
            token_ids=token_ids,
            log_probs=log_probs,
            entropy=entropy,
            prompt_length=prompt_length,
        )


    @staticmethod
    def _top_p_filter(logits: torch.Tensor, top_p: float):
        """Nucleus (top-p) filtering."""
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

        # Remove tokens with cumulative probability above the threshold
        sorted_mask = cumulative_probs - F.softmax(sorted_logits, dim=-1) >= top_p
        sorted_logits[sorted_mask] = float("-inf")

        # Scatter back
        logits = logits.scatter(1, sorted_indices, sorted_logits)
        return logits

    def save(self, path: str):
        """Save model and tokenizer."""
        self.model.save_pretrained(path)
        self.tokenizer.save_pretrained(path)

    @classmethod
    def load(cls, path: str, device: str = "auto"):
        """Load a saved policy."""
        policy = cls.__new__(cls)
        nn.Module.__init__(policy)
        policy.tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        policy.model = AutoModelForCausalLM.from_pretrained(
            path, trust_remote_code=True, torch_dtype=torch.float16
        )
        if device == "auto":
            policy.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            policy.device = torch.device(device)
        policy.model.to(policy.device)
        policy.max_seq_length = 512
        policy.model_name = path
        return policy