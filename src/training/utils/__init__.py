import yaml
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


def load_config(path: str = "configs/agent_config.yaml") -> dict:
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        training_root = Path(__file__).parent.parent  # utils/ → training/
        p = training_root / path
    with open(p, "r") as f:
        return yaml.safe_load(f)


def setup_logging(name: str, log_dir: str = "./logs", level: int = logging.INFO) -> logging.Logger:
    """Configure a logger with file and console handlers."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(
            "[%(asctime)s] %(name)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(console)

        fh = logging.FileHandler(Path(log_dir) / f"{name}.log")
        fh.setFormatter(logging.Formatter(
            "[%(asctime)s] %(name)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(fh)

    return logger