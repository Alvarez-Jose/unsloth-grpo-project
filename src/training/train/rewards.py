import re
import shlex
from training.cli_agent.environment import CLIEnvironment, CLITask
from training.train.training_data import TRAINING_TASKS

_reward_env = CLIEnvironment(tasks=TRAINING_TASKS)
_task_list: list[CLITask] = list(TRAINING_TASKS)
_print_counter = 0


def set_tasks(tasks: list[CLITask]):
    global _task_list, _reward_env
    _task_list = list(tasks)
    _reward_env = CLIEnvironment(tasks=tasks)


def _find_task(prompt):
    if isinstance(prompt, list):
        text = " ".join(m["content"] for m in prompt if isinstance(m, dict))
    else:
        text = prompt
    for task in _task_list:
        if task.description in text:
            return task
    return None


def _execute_completion(task: CLITask, completion: str) -> tuple[list[dict], str]:
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
    if isinstance(completion, list):
        return completion[0]["content"]
    return completion


# --- Reward Functions ---

def reward_format(prompts, completions, **kwargs) -> list[float]:
    """
    Reward well-formed shell commands.
    +2.0 if all lines are parseable shell.
    -2.0 if markdown formatting detected.
    -1.0 per unparseable line.
    """
    scores = []
    for completion in completions:
        response = _get_response(completion)

        # Penalize markdown formatting
        if "```" in response or response.strip().startswith("`"):
            scores.append(-2.0)
            continue

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


def reward_safety(prompts, completions, **kwargs) -> list[float]:
    """
    Penalize dangerous commands.
    0.0 if safe, up to -5.0 if dangerous.
    """
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
        r"rm\s+-rf\s+~",        # rm -rf home dir
        r"mv\s+.*\s+/dev/null", # silently destroy files
        r"echo\s+.*>>\s*/etc/", # appending to system files
        r"shutdown",             # shutdown/reboot commands
        r"reboot",
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


def reward_correctness(prompts, completions, answer, **kwargs) -> list[float]:
    """
    Execute the command and check output against expected answer.

    +5.0 exact match
    +2.0 case-insensitive match
    +1.0 no expected output required, command succeeded cleanly
    +0.5 wrong answer but non-empty output with no errors (partial credit)
    -2.0 wrong, empty, or errored
    """
    global _print_counter
    scores = []

    for prompt, completion, expected in zip(prompts, completions, answer):
        response = _get_response(completion)
        task = _find_task(prompt)

        if task is None:
            logger.warning(f"Could not match prompt to any task: {str(text)[:100]}")
            scores.append(0.0)
            continue

        history, last_output = _execute_completion(task, response)

        if not history:
            logger.warning(f"Empty completion for task: {task.task_id}")  # 👈 add this
            scores.append(-2.0)
            continue



        has_errors = (
            "[stderr]" in last_output and "No such file" not in last_output
        ) or "[exit code" in last_output

        if expected and expected.strip() in last_output.strip():
            score = 5.0
        elif expected and expected.strip().lower() in last_output.strip().lower():
            score = 2.0
        elif not expected and last_output.strip() and not has_errors:
            score = 1.0
        elif last_output.strip() and not has_errors:
            score = 0.5
        else:
            score = -2.0

        if _print_counter % 5 == 0:
            print(
                f"{'*' * 20}\n"
                f"Task: {task.description}\n"
                f"Expected: {expected}\n"
                f"Command: {response}\n"
                f"Output: {last_output[:200]}\n"
                f"Score: {score}\n"
            )
        _print_counter += 1
        scores.append(score)
    return scores


def reward_efficiency(prompts, completions, **kwargs) -> list[float]:
    """
    Reward concise solutions, penalize hardcoded answers.

    -1.5 for bare echo/printf hardcoding (anti-memorization)
    +1.5 for a single real command
    +0.5 for 2 commands
     0.0 for 3 commands
    -0.3 for 4+ commands
    """
    scores = []
    for completion in completions:
        response = _get_response(completion)
        lines = [l.strip() for l in response.strip().split("\n") if l.strip()]

        if not lines:
            scores.append(-1.0)
            continue

        # Penalize trivial hardcoded answers like "echo 42" or "printf 100"
        if len(lines) == 1 and re.match(r'^(echo|printf)\s+[\d.]+\s*$', lines[0]):
            scores.append(-1.5)
            continue

        if len(lines) == 1:
            scores.append(1.5)
        elif len(lines) == 2:
            scores.append(0.5)
        elif len(lines) == 3:
            scores.append(0.0)
        else:
            scores.append(-0.3)

    return scores


def reward_tool_appropriateness(prompts, completions, **kwargs) -> list[float]:
    """
    Small bonus (+0.5 max) for using canonical tools for the job.
    Never penalizes — only adds signal.
    """
    TASK_TOOL_HINTS = {
        "count": ["wc", "grep -c", "awk"],
        "lines": ["wc", "grep", "awk", "sed"],
        "find": ["find"],
        "search": ["grep"],
        "sort": ["sort"],
        "extract column": ["awk", "cut"],
        "sum": ["awk", "bc"],
        "average": ["awk"],
        "compress": ["tar", "gzip", "zip"],
        "extract": ["tar", "unzip", "gunzip"],
        "replace": ["sed"],
        "duplicate": ["sort", "uniq"],
        "permission": ["chmod", "find"],
        "process": ["ps", "pgrep", "top"],
        "disk": ["df", "du"],
        "memory": ["free"],
        "unique": ["sort", "uniq", "awk"],
        "reverse": ["tac", "awk"],
        "number": ["nl", "awk", "cat -n"],
        "compare": ["diff", "cmp"],
        "port": ["ss", "netstat", "lsof"],
        "network": ["ip", "ifconfig", "ss"],
        "download": ["curl", "wget"],
        "dns": ["nslookup", "dig", "host"],
        "ping": ["ping"],
    }
    scores = []
    for prompt, completion in zip(prompts, completions):
        response = _get_response(completion)
        task_text = " ".join(
            m["content"] for m in prompt if isinstance(m, dict)
        ).lower()
        score = 0.0
        for keyword, tools in TASK_TOOL_HINTS.items():
            if keyword in task_text:
                if any(tool in response for tool in tools):
                    score = 0.5
                break
        scores.append(score)
    return scores


def reward_combined(prompts, completions, **kwargs) -> list[float]:
    """Combine all reward components."""
    fmt = reward_format(prompts, completions, **kwargs)
    safety = reward_safety(prompts, completions, **kwargs)
    correct = reward_correctness(prompts, completions, **kwargs)
    eff = reward_efficiency(prompts, completions, **kwargs)
    tool = reward_tool_appropriateness(prompts, completions, **kwargs)

    return [f + s + c + e + t for f, s, c, e, t in zip(fmt, safety, correct, eff, tool)]