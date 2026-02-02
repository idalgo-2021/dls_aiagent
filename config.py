import yaml
from pathlib import Path

CONFIG_PATH = Path("config.yaml")


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Конфиг не найден: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()
