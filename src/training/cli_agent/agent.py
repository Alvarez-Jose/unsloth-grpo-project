from __future__ import annotations
import argparse
import sys
import os
from typing import Optional
from .policy import CLIPolicy
from .environment import CLIEnvironment, TRAINING_TASKS
from training.utils import load_config


class CLIAgent:
    def __init__(
        self,
        policy: CLIPolicy,
        max_steps: int = 20,
        temperature: float = 0.3,
        verbose: bool = True,
    ):
        self.policy = policy
        self.max_steps = max_steps
        self.temperature = temperature
        self.verbose = verbose
        self.env = CLIEnvironment(max_steps=max_steps)

    def solve_task(self, task_description):
        """
        Returns a dict with the command history, final output, and metadata.
        """
        history = []
        prompt_parts = [f"<|TASK|> {task_description}"]

        for step in range(self.max_steps):
            prompt = "\n".join(prompt_parts) + "\n<|CMD|>"

            output = self.policy.generate_command(
                prompt,
                temperature=self.temperature,
            )
            command = output.command

            if self.verbose:
                print(f"  [{step + 1}] $ {command}")

            if command.upper() == "DONE" or not command:
                break

            # Execute via environment
            result = self.env.step(command)
            history.append({
                "step": step + 1,
                "command": command,
                "output": result.observation,
            })

            if self.verbose and result.observation:
                for line in result.observation.split("\n")[:5]:
                    print(f"       {line}")

            prompt_parts.append(f"<|CMD|> {command}")
            prompt_parts.append(f"<|OUTPUT|> {result.observation[:200]}")

            if result.done:
                break

        return {
            "task": task_description,
            "history": history,
            "steps_used": len(history),
            "final_output": history[-1]["output"] if history else "",
        }

    def run_benchmark(self, tasks: Optional[list] = None):
        """Run the agent on a set of benchmark tasks and report results."""
        tasks = tasks or TRAINING_TASKS
        results = []
        total_reward = 0.0

        for task in tasks:
            if self.verbose:
                print(f"\n{'='*50}")
                print(f"Task: {task.description}")
                print(f"{'='*50}")

            obs = self.env.reset(task)
            episode_reward = 0.0

            for step in range(task.max_steps):
                prompt = self.env.get_prompt()
                output = self.policy.generate_command(
                    prompt, temperature=self.temperature
                )
                command = output.command

                if self.verbose:
                    print(f"  [{step+1}] $ {command}")

                if command.upper() == "DONE" or not command:
                    result = self.env.step("DONE")
                    episode_reward += result.reward
                    break

                result = self.env.step(command)
                episode_reward += result.reward

                if self.verbose and result.observation:
                    for line in result.observation.split("\n")[:3]:
                        print(f"       {line}")

                if result.done:
                    break

            results.append({
                "task_id": task.task_id,
                "reward": episode_reward,
                "steps": step + 1,
                "success": episode_reward > 0.5,
            })
            total_reward += episode_reward

            if self.verbose:
                status = "PASS" if episode_reward > 0.5 else "FAIL"
                print(f"  Result: {status} (reward={episode_reward:.2f})")

        summary = {
            "total_tasks": len(tasks),
            "passed": sum(1 for r in results if r["success"]),
            "total_reward": total_reward,
            "avg_reward": total_reward / len(tasks) if tasks else 0,
            "details": results,
        }

        if self.verbose:
            print(f"\n{'='*50}")
            print(f"Benchmark: {summary['passed']}/{summary['total_tasks']} passed")
            print(f"Average reward: {summary['avg_reward']:.3f}")

        return summary


def main():
    config = load_config("configs/agent_config.yaml")
    cli_cfg = config.get("cli_agent", {})
    policy_cfg = cli_cfg.get("policy", {})
    inference_cfg = cli_cfg.get("inference", {})

    model_path = inference_cfg.get("model_path", policy_cfg.get("model_name"))
    mode = inference_cfg.get("mode", "interactive")
    temperature = inference_cfg.get("temperature", 0.3)
    max_steps = inference_cfg.get("max_steps", 15)

    print("Loading model...")
    if os.path.isdir(model_path):
        policy = CLIPolicy.load(model_path)
    else:
        policy = CLIPolicy(model_name=model_path)

    agent = CLIAgent(policy=policy,max_steps=max_steps,temperature=temperature,)

    if mode == "benchmark":
        agent.run_benchmark()
    else:
        print("\nCLI Agent — Interactive Mode")
        print("Describe a task and the agent will try to solve it.")
        print("Type 'quit' to exit.\n")

        while True:
            try:
                task = input("[Task] > ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not task or task.lower() == "quit":
                break

            agent.solve_task(task)


if __name__ == "__main__":
    main()