from __future__ import annotations

import asyncio
import json
import logging
import shutil
from pathlib import Path
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP
from platformdirs import user_config_dir, user_data_dir, user_log_dir

from prompts import (
    SYSTEM_PROMPT,
    INIT_PROMPT,
    LOG_PROMPT,
    RESUME_PROMPT,
    TAILOR_PROMPT,
    UPDATE_PROMPT,
    HELP_PROMPT,
)
from storage import create_backend

APP_NAME = "resume-agent"
SOURCE_DIR = Path(__file__).resolve().parent

CONFIG_DIR = Path(user_config_dir(APP_NAME, ensure_exists=True))
DATA_DIR = Path(user_data_dir(APP_NAME, ensure_exists=True))
LOG_DIR = Path(user_log_dir(APP_NAME, ensure_exists=True))

CONFIG_PATH = CONFIG_DIR / "config.yaml"

# ── logging setup ───────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    filename=str(LOG_DIR / "server.log"),
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# ── serial execution lock ──────────────────────────────────────────

_lock = asyncio.Lock()


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        # 首次运行，从源码目录复制默认配置
        example = SOURCE_DIR / "config.example.yaml"
        if example.exists():
            shutil.copy(example, CONFIG_PATH)
            logger.info(f"Created default config at {CONFIG_PATH}")
        else:
            raise FileNotFoundError(
                f"config.yaml not found at {CONFIG_PATH} "
                f"and no config.example.yaml in {SOURCE_DIR}"
            )
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        logger.error("config.yaml must be a YAML object")
        raise ValueError("config.yaml must define a YAML object at the top level")
    return data


async def _with_lock(tool_name: str, func, *args, **kwargs):
    """Execute a tool function with serial lock and logging."""
    logger.info(f"[{tool_name}] start")
    async with _lock:
        try:
            result = func(*args, **kwargs)
            logger.info(f"[{tool_name}] done")
            return result
        except Exception as e:
            logger.error(f"[{tool_name}] error: {e}", exc_info=True)
            raise


# ── init ────────────────────────────────────────────────────────────

config = load_config()

vault_path = config.get("storage", {}).get("vault_path", "")
if vault_path:
    vault = Path(vault_path)
    # 绝对路径直接用，相对路径基于 DATA_DIR 解析
    if not vault.is_absolute():
        vault = DATA_DIR / vault
else:
    vault = DATA_DIR / "data"
config.setdefault("storage", {})["vault_path"] = str(vault)

backend = create_backend(config)

mcp = FastMCP("resume-agent")

# ── tools with serial lock ───────────────────────────────────────────


@mcp.tool()
async def get_experiences() -> str:
    return await _with_lock(
        "get_experiences",
        lambda: json.dumps(backend.get_experiences(), ensure_ascii=False),
    )


@mcp.tool()
async def create_experience(
    project_name: str,
    direction: str,
    organization: str,
    role: str,
    start: str,
    exp_type: str,
    end: str | None = None,
    direction_tags: list[str] | None = None,
    skill_tags: list[str] | None = None,
    tool_tags: list[str] | None = None,
) -> str:
    return await _with_lock(
        "create_experience",
        backend.create_experience,
        project_name=project_name,
        direction=direction,
        organization=organization,
        role=role,
        start=start,
        exp_type=exp_type,
        end=end,
        direction_tags=direction_tags,
        skill_tags=skill_tags,
        tool_tags=tool_tags,
    )


@mcp.tool()
async def log_bullet(
    exp_id: str,
    bullet_name: str,
    raw: str,
    rewritten: str,
    skill_tags: list[str] | None = None,
    tool_tags: list[str] | None = None,
    category: str = "achievement",
    has_number: bool = False,
    metric_values: list[str] | None = None,
) -> str:
    return await _with_lock(
        "log_bullet",
        backend.log_bullet,
        exp_id=exp_id,
        bullet_name=bullet_name,
        raw=raw,
        rewritten=rewritten,
        skill_tags=skill_tags,
        tool_tags=tool_tags,
        category=category,
        has_number=has_number,
        metric_values=metric_values,
    )


@mcp.tool()
async def create_base_resume(
    direction: str,
    bullet_ids: list[str],
    content: str,
) -> str:
    return await _with_lock(
        "create_base_resume",
        backend.create_base_resume,
        direction=direction,
        bullet_ids=bullet_ids,
        content=content,
    )


@mcp.tool()
async def create_resume_version(
    name: str,
    base_id: str,
    jd: dict[str, Any],
    bullet_ids: list[str],
    content: str,
) -> str:
    return await _with_lock(
        "create_resume_version",
        backend.create_resume_version,
        name=name,
        base_id=base_id,
        jd=jd,
        bullet_ids=bullet_ids,
        content=content,
    )


@mcp.tool()
async def list_resumes(direction: str | None = None) -> str:
    return await _with_lock(
        "list_resumes",
        lambda: json.dumps(backend.list_resumes(direction=direction), ensure_ascii=False),
    )


@mcp.tool()
async def get_resume(resume_id: str) -> str:
    return await _with_lock(
        "get_resume",
        lambda: json.dumps(backend.get_resume(resume_id), ensure_ascii=False),
    )


# ── prompts ─────────────────────────────────────────────────────────


@mcp.prompt(name="init")
def init_prompt() -> str:
    return SYSTEM_PROMPT + "\n\n" + INIT_PROMPT


@mcp.prompt(name="log")
def log_prompt() -> str:
    return SYSTEM_PROMPT + "\n\n" + LOG_PROMPT


@mcp.prompt(name="resume")
def resume_prompt() -> str:
    return SYSTEM_PROMPT + "\n\n" + RESUME_PROMPT


@mcp.prompt(name="tailor")
def tailor_prompt() -> str:
    return SYSTEM_PROMPT + "\n\n" + TAILOR_PROMPT


@mcp.prompt(name="update")
def update_prompt() -> str:
    return SYSTEM_PROMPT + "\n\n" + UPDATE_PROMPT


@mcp.prompt(name="help")
def help_prompt() -> str:
    return HELP_PROMPT


if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as e:
        logger.error(f"Server crashed: {e}", exc_info=True)
        raise
