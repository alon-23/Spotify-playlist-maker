"""Local config + token storage (gitignored runtime file)."""

import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "spotify_maker.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
