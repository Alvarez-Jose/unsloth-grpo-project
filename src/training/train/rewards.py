from __future__ import annotations
import re
import shlex
from training.cli_agent.environment import CLIEnvironment, CLITask, TRAINING_TASKS


_reward_env = CLIEnvironment(tasks=TRAINING_TASKS)
_task_list: list[CLITask] = list(TRAINING_TASKS)
_print_counter = 0


def set_tasks(tasks: list[CLITask]):
    """Update the task list and environment."""
    global _task_list, _reward_env
    _task_list = list(tasks)
    _reward_env = CLIEnvironment(tasks=tasks)


def _find_task(prompt):
    """Match a prompt back to its task."""
    if isinstance(prompt, list):
        text = " ".join(m["content"] for m in prompt if isinstance(m, dict))
    else:
        text = prompt
    for task in _task_list:
        if task.description in text:
            return task
    return None


def _execute_completion(task: CLITask, completion: str) -> tuple[list[dict], str]:
    """Run a completions commands in the environment."""
    _reward_env.reset(task)
    commands = [
        line.strip()
        for line in completion.strip().split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]

    history = []
    for cmd in commands[:task.max_steps]:
        if cmd.upper() == "DONE":
            break
        result = _reward_env.step(cmd)
        history.append({"command": cmd, "output": result.observation})
        if result.done:
            break

    last_output = history[-1]["output"] if history else ""
    return history, last_output


def _get_response(completion) -> str:
    """Extract text from the completion format."""
    if isinstance(completion, list):
        return completion[0]["content"]
    return completion


# Reward functions
def reward_format(prompts, completions, **kwargs) -> list[float]:
    """Reward well-formed shell commands. +2.0 if parseable, -1.5 if not."""
    scores = []
    for completion in completions:
        response = _get_response(completion)
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]

        if not lines:
            scores.append(-2.0)
            continue

        score = 0.0
        for line in lines:
            if line.upper() == "DONE":
                continue
            try:
                shlex.split(line)
                score += 1.0
            except ValueError:
                score -= 1.0

        scores.append(min(max(score, -2.0), 2.0))
    return scores


def reward_safety(prompts, completions, **kwargs):
    """Penalize dangerous commands. 0.0 if safe, up to -5.0 if dangerous."""
    DANGEROUS = [
        r"rm\s+-rf\s+/",
        r"rm\s+-rf\s+\*",
        r"chmod\s+777",
        r"chmod\s+-R\s+777",
        r">\s*/dev/sd",
        r"mkfs\.",
        r"dd\s+if=",
        r":\(\)\{",
        r"sudo\s+",
        r"curl.*\|\s*sh",
        r"wget.*\|\s*sh",
    ]

    scores = []
    for completion in completions:
        response = _get_response(completion)
        penalty = 0.0
        for pattern in DANGEROUS:
            if re.search(pattern, response):
                penalty -= 2.5
        scores.append(max(penalty, -5.0))
    return scores


def reward_correctness(prompts, completions, answer, **kwargs):
    """Execute the command and check if output matches expected answer.

    +5.0 for exact match, +2.0 for partial, -2.0 for wrong.
    """
    global _print_counter
    scores = []

    for prompt, completion, expected in zip(prompts, completions, answer):
        response = _get_response(completion)
        task = _find_task(prompt)

        if task is None:
            scores.append(0.0)
            continue

        history, last_output = _execute_completion(task, response)

        if not history:
            scores.append(-2.0)
            continue

        if expected and expected.strip() in last_output.strip():
            score = 5.0
        elif expected and expected.strip().lower() in last_output.strip().lower():
            score = 2.0
        else:
            score = -2.0

        if _print_counter % 5 == 0:
            print(
                f"{'*'*20}\n"
                f"Task: {task.description}\n"
                f"Expected: {expected}\n"
                f"Command: {response}\n"
                f"Output: {last_output[:200]}\n"
                f"Score: {score}\n"
            )
        _print_counter += 1

        scores.append(score)
    return scores


def reward_efficiency(prompts, completions, **kwargs):
    """Reward concise solutions. +1.5 for single command, less for more."""
    scores = []
    for completion in completions:
        response = _get_response(completion)
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]
        num_commands = len(lines)

        if num_commands == 0:
            scores.append(-1.0)
        elif num_commands == 1:
            scores.append(1.5)
        elif num_commands == 2:
            scores.append(0.5)
        else:
            scores.append(-0.5)
    return scores

def reward_combined(prompts, completions, **kwargs):
    """
    Single reward function that combines all components.

    """
    fmt_scores = reward_format(prompts, completions, **kwargs)
    safety_scores = reward_safety(prompts, completions, **kwargs)
    correct_scores = reward_correctness(prompts, completions, **kwargs)
    eff_scores = reward_efficiency(prompts, completions, **kwargs)

    return [f + s + c + e for f, s, c, e in zip(fmt_scores, safety_scores, correct_scores, eff_scores)]