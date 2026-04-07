from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP

from tools.logging import log_experience as log_experience_impl

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "config.yaml not found. Copy config.example.yaml to config.yaml first."
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("config.yaml must define a YAML object at the top level")

    return data


mcp = FastMCP("resume-agent")


@mcp.tool()
def log_experience(text: str) -> str:
    """记录一段经历文本（第一阶段仅打印，不写入存储）。"""
    return log_experience_impl(text)


@mcp.tool()
def health_check() -> str:
    """Simple health check for quick debugging in clients."""
    config = load_config()
    backend = config.get("storage", {}).get("backend", "local")
    return json.dumps({"status": "ok", "backend": backend}, ensure_ascii=False)


if __name__ == "__main__":
    # Uses stdio transport so Claude Desktop can launch and talk to this server.
    mcp.run()
