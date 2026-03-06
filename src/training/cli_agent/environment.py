from __future__ import annotations
import os
import subprocess
import shlex
import time
import tempfile
import json
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


"""

I had claude generate this but IDK what is going on here lmao

"""

"""Reinforcement Learning environment for the CLI agent.

Wraps a sandboxed shell session as a Gym-like environment. The agent
observes a task prompt + shell history and produces a shell command as
its action. The environment executes the command and returns the output.
"""



# Task Definitions

@dataclass
class CLITask:
    """A single task the CLI agent must solve."""
    task_id: str
    description: str             # Natural language task description
    setup_commands: list[str]    # Commands to set up the environment
    validation_fn: str           # Name of the validation function to use
    expected_output: str = ""    # Expected output
    max_steps: int = 10
    tags: list[str] = field(default_factory=list)



# Validation Functions
def check_output_contains(output: str, expected: str) -> float:
    """Check if expected string appears in output. Returns 0.0 or 1.0."""
    return 1.0 if expected.strip() in output.strip() else 0.0


def check_command_success(output: str, expected: str) -> float:
    """Check that the command produced any output and no errors."""
    if not output.strip():
        return 0.0
    elif "[exit code" in output:  # your env already appends this
        return 0.0
    else:
        return 1.0


def check_sorted_unique(output: str, expected: str) -> float:
    """Check that output is sorted and deduplicated correctly."""
    lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
    expected_lines = [l.strip() for l in expected.strip().split("\n") if l.strip()]
    if lines == expected_lines:
        return 1.0
    if sorted(set(lines)) == expected_lines:
        return 0.5
    return 0.0


def check_directory_structure(output: str, expected: str) -> float:
    """Check that expected files exist."""
    paths = [p.strip() for p in expected.split(",")]
    score = sum(1.0 for p in paths if os.path.exists(p)) / len(paths)
    return score


VALIDATORS = {
    "check_output_contains": check_output_contains,
    "check_command_success": check_command_success,
    "check_sorted_unique": check_sorted_unique,
    "check_directory_structure": check_directory_structure,
}



# Environment
@dataclass
class StepResult:
    """Result of a single environment step."""
    observation: str     # stdout + stderr from the command
    reward: float        # immediate reward for this step
    done: bool           # whether the episode is over
    info: dict = field(default_factory=dict)


class CLIEnvironment:
    """Gym-like RL environment for CLI agent training.

    Each episode:
    1. A task is sampled and its setup commands are run.
    2. The agent receives the task description as the initial observation.
    3. At each step, the agent produces a shell command.
    4. The environment executes it and returns the output.
    5. The episode ends when the agent says "DONE", hits max steps, or times out.
    """

    BLOCKED = {"rm -rf /", "sudo", "shutdown", "reboot", "mkfs", "dd if=/dev"}

    def __init__(
        self,
        tasks: Optional[list[CLITask]] = None,
        timeout: int = 30,
        max_steps: int = 20,
        work_dir: Optional[str] = None,
    ):
        self.tasks = tasks
        self.timeout = timeout
        self.default_max_steps = max_steps
        self.work_dir = work_dir or tempfile.mkdtemp(prefix="cli_env_")
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)

        self.current_task: Optional[CLITask] = None
        self.history: list[dict[str, str]] = []
        self.steps_taken: int = 0
        self.start_time: float = 0.0

    def reset(self, task: Optional[CLITask] = None):
        """Reset the environment with a new (or specific) task.

        Returns the initial observation (task description).
        """
        import random
        self.current_task = task or random.choice(self.tasks)
        self.history = []
        self.steps_taken = 0
        self.start_time = time.time()

        # Run setup commands
        for cmd in self.current_task.setup_commands:
            subprocess.run(cmd, shell=True, capture_output=True, timeout=10)

        observation = (
            f"TASK: {self.current_task.description}\n"
            f"You have up to {self.current_task.max_steps} commands. "
            f"Type 'DONE' when finished.\n"
            f"Working directory: {self.work_dir}\n"
        )
        return observation

    def step(self, command):
        """Execute a command and return the result."""
        self.steps_taken += 1
        command = command.strip()
        max_steps = self.current_task.max_steps if self.current_task else self.default_max_steps

        # Check for episode-ending action
        if command.upper() == "DONE":
            final_reward = self._compute_final_reward()
            return StepResult(
                observation="Episode ended by agent.",
                reward=final_reward,
                done=True,
                info={"reason": "agent_done", "steps": self.steps_taken},
            )

        # Safety check
        for blocked in self.BLOCKED:
            if blocked in command:
                return StepResult(
                    observation=f"BLOCKED: Command contains forbidden pattern.",
                    reward=-0.5,
                    done=False,
                    info={"reason": "blocked_command"},
                )

        # Execute
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.work_dir,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code {result.returncode}]"
                step_reward = -0.1  # small penalty for errors
            else:
                step_reward = 0.0   # neutral — final reward matters more
        except subprocess.TimeoutExpired:
            output = f"Command timed out after {self.timeout}s"
            step_reward = -0.2
        except Exception as e:
            output = f"Error: {e}"
            step_reward = -0.2

        self.history.append({"command": command, "output": output})

        # Check if max steps reached
        done = self.steps_taken >= max_steps
        if done:
            step_reward += self._compute_final_reward()

        return StepResult(
            observation=output.strip() or "(no output)",
            reward=step_reward,
            done=done,
            info={
                "steps": self.steps_taken,
                "reason": "max_steps" if done else "continue",
            },
        )

    def _compute_final_reward(self):
        """Compute the task-completion reward."""
        if not self.current_task or not self.history:
            return 0.0

        validator = VALIDATORS.get(self.current_task.validation_fn)
        if not validator:
            return 0.0

        # Use the last command's output for validation
        last_output = self.history[-1]["output"] if self.history else ""
        correctness = validator(last_output, self.current_task.expected_output)

        # Efficiency bonus: fewer steps = better
        max_steps = self.current_task.max_steps
        steps_used = self.steps_taken
        efficiency = max(0.0, 1.0 - (steps_used / max_steps))

        return correctness + 0.3 * efficiency

    def get_prompt(self):
        """Build the full prompt for the policy (task + history).
        """
        parts = [f"TASK: {self.current_task.description}\n"]

        for i, entry in enumerate(self.history):
            parts.append(f"$ {entry['command']}")
            parts.append(entry["output"])

        parts.append("$ ")  # prompt for next command
        return "\n".join(parts)