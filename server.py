from __future__ import annotations

"""
Claude Desktop 注册示例（claude_desktop_config.json）：

{
  "mcpServers": {
    "resume-base": {
      "command": "python",
      "args": ["绝对路径/server.py"]
    }
  }
}
"""

from pathlib import Path
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP

from prompts.templates import LOGGING_SYSTEM_PROMPT
from storage import create_backend
import tools.logging as logging_tools
import tools.version as version_tools

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


# ── init ────────────────────────────────────────────────────────────

config = load_config()

# resolve relative vault_path against project root
vault_path = config.get("storage", {}).get("vault_path", "./data")
config.setdefault("storage", {})["vault_path"] = str((BASE_DIR / vault_path).resolve())

backend = create_backend(config)
logging_tools.init(backend)
version_tools.init(backend)

mcp = FastMCP("resume-agent")

# ── tools ───────────────────────────────────────────────────────────

mcp.tool()(logging_tools.get_experiences)
mcp.tool()(logging_tools.create_experience)
mcp.tool()(logging_tools.log_bullet)
mcp.tool()(version_tools.create_base_resume)
mcp.tool()(version_tools.create_resume_version)
mcp.tool()(version_tools.list_resumes)
mcp.tool()(version_tools.get_resume)

# ── prompts ─────────────────────────────────────────────────────────


@mcp.prompt(name="log")
def log_prompt() -> str:
    """Prompt invoked by /log in Claude Desktop."""
    return LOGGING_SYSTEM_PROMPT


if __name__ == "__main__":
    mcp.run()
