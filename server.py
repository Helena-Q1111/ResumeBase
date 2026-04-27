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
    """List all experiences with their metadata and bullet counts.

    Read-only. Call this first whenever you need a valid `exp_id` for
    another tool (e.g. log_bullet, list_bullets), or when surfacing the
    user's existing experiences.

    Returns:
        JSON string: a list of experience objects. Each object contains the
        full frontmatter (id, project_name, direction, organization, role,
        start, end, type, *_tags, created_at, updated_at) plus a derived
        `bullet_count` field. Empty list if no experiences exist.
    """
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
    """Create one experience entry (project, internship, job, or research).

    Writes one experience per call. Filename is derived from
    `{project_name}-{direction}.md`, so the (project_name, direction) pair
    should be unique within the user's vault.

    Args:
        project_name: Project or company name. Used as part of the filename.
        direction: Career direction tag (e.g. "backend", "data", "frontend",
            "pm"). Free-form string. Used as part of the filename.
        organization: Hosting organization or company.
        role: Job title or role name.
        start: Start date in `YYYY-MM` format.
        exp_type: Exactly one of "internship", "fulltime", "project",
            "research".
        end: End date in `YYYY-MM` format. Omit or pass empty for ongoing
            roles.
        direction_tags: Career-direction tags this experience aligns with,
            e.g. ["backend", "infra"]. Optional.
        skill_tags: Conceptual skills, e.g. ["distributed-systems"].
            Optional.
        tool_tags: Concrete tools/frameworks, e.g. ["pytorch"]. Optional.

    Returns:
        The new experience's id (string, prefix "exp-").
    """
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
    rewritten: dict[str, str],
    skill_tags: list[str] | None = None,
    tool_tags: list[str] | None = None,
    category: str = "achievement",
    has_number: bool = False,
    metric_values: list[str] | None = None,
) -> str:
    """Persist one polished resume bullet under an existing experience.

    Writes exactly one bullet per call. This is the only way to add bullets
    to storage; do not use for free-form notes.

    Args:
        exp_id: ID of the parent experience. Must come from
            get_experiences() — do not synthesize. If no matching experience
            exists, the user must create one first.
        bullet_name: Short identifier used as the markdown filename. A tag,
            not the bullet text. Must not contain path separators.
        raw: The user's original description, stored verbatim. Pass through
            unchanged.
        rewritten: Polished bullet text keyed by ISO 639-1 language code.
            Must contain at least one entry. Wording style is governed by
            the active workflow prompt, not this tool.
            - Single language: {"en": "..."}
            - Bilingual:       {"en": "...", "zh": "..."}
        skill_tags: Conceptual skills, e.g. ["distributed-systems"]. Optional.
        tool_tags: Concrete tools/frameworks, e.g. ["pytorch"]. Optional.
        category: Exactly one of "achievement", "skill", "responsibility".
        has_number: True iff `rewritten` contains quantitative metrics.
        metric_values: Raw metric strings when has_number is True, e.g.
            ["30%", "2.5x"]. Omit otherwise.

    Returns:
        The new bullet's id (string, prefix "bul-").

    Raises:
        ValueError: if `rewritten` is empty, or if `exp_id` does not match
            any experience.
    """
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
async def list_bullets(exp_id: str) -> str:
    """List all bullets under a given experience.

    Read-only. Use this to inspect what's already been logged for an
    experience — typically before composing a resume so you know what
    material is available.

    Args:
        exp_id: ID of the experience. Must come from get_experiences().

    Returns:
        JSON string: a list of bullet objects, each containing id,
        bullet_name, category, languages, rewritten (dict keyed by lang),
        skill_tags, tool_tags, has_number, metric_values, and the markdown
        body (`content`). Empty list if the experience has no bullets yet.

    Raises:
        ValueError: if `exp_id` does not match any experience.
    """
    return await _with_lock(
        "list_bullets",
        lambda: json.dumps(backend.list_bullets(exp_id), ensure_ascii=False),
    )


@mcp.tool()
async def update_experience(
    exp_id: str,
    organization: str | None = None,
    role: str | None = None,
    start: str | None = None,
    end: str | None = None,
    exp_type: str | None = None,
    direction_tags: list[str] | None = None,
    skill_tags: list[str] | None = None,
    tool_tags: list[str] | None = None,
) -> str:
    """Modify metadata fields on an existing experience.

    Partial update: pass only the fields the user wants to change. Omitted
    or None fields are left as-is. Tag lists fully replace the stored list
    (this is not an append operation).

    Note: `project_name` and `direction` are intentionally not editable in
    this version — they form the filename and bullet parent path. To change
    them, recreate the experience.

    Args:
        exp_id: ID of the experience. Must come from get_experiences().
        organization: New organization / company name. Optional.
        role: New job title or role name. Optional.
        start: New start date in `YYYY-MM` format. Optional.
        end: New end date in `YYYY-MM` format, or "" for ongoing. Optional.
        exp_type: One of "internship", "fulltime", "project", "research".
            Optional.
        direction_tags: Replacement direction tags (full list). Optional.
        skill_tags: Replacement skill tags (full list). Optional.
        tool_tags: Replacement tool tags (full list). Optional.

    Returns:
        JSON string of the updated experience metadata.

    Raises:
        ValueError: if `exp_id` does not match any experience.
    """
    return await _with_lock(
        "update_experience",
        lambda: json.dumps(
            backend.update_experience(
                exp_id=exp_id,
                organization=organization,
                role=role,
                start=start,
                end=end,
                exp_type=exp_type,
                direction_tags=direction_tags,
                skill_tags=skill_tags,
                tool_tags=tool_tags,
            ),
            ensure_ascii=False,
        ),
    )


@mcp.tool()
async def update_bullet(
    bullet_id: str,
    bullet_name: str | None = None,
    raw: str | None = None,
    rewritten: dict[str, str] | None = None,
    skill_tags: list[str] | None = None,
    tool_tags: list[str] | None = None,
    category: str | None = None,
    has_number: bool | None = None,
    metric_values: list[str] | None = None,
) -> str:
    """Modify fields on an existing bullet.

    Partial update: pass only the fields the user wants to change. Omitted
    or None fields are left as-is. Tag lists fully replace the stored list.
    Cannot reassign a bullet to a different experience — `exp_id` is fixed.

    If `raw` or `rewritten` change, the markdown body is regenerated to stay
    in sync with the new metadata; user-added notes in body sections may be
    lost.

    Args:
        bullet_id: ID of the bullet. Must come from list_bullets().
        bullet_name: New filename tag (no path separators). Renames the
            underlying .md file. Optional.
        raw: Replacement raw description (stored verbatim). Optional.
        rewritten: Replacement polished text dict, keyed by ISO 639-1
            language code. Must be non-empty if provided. Optional.
        skill_tags: Replacement skill tags. Optional.
        tool_tags: Replacement tool tags. Optional.
        category: One of "achievement", "skill", "responsibility". Optional.
        has_number: True iff `rewritten` contains quantitative metrics.
            Optional.
        metric_values: Replacement metric strings. Optional.

    Returns:
        JSON string of the updated bullet metadata, including a
        `bullet_name` field reflecting any rename.

    Raises:
        ValueError: if `bullet_id` does not match any bullet, or if
            `rewritten` is provided but empty.
    """
    return await _with_lock(
        "update_bullet",
        lambda: json.dumps(
            backend.update_bullet(
                bullet_id=bullet_id,
                bullet_name=bullet_name,
                raw=raw,
                rewritten=rewritten,
                skill_tags=skill_tags,
                tool_tags=tool_tags,
                category=category,
                has_number=has_number,
                metric_values=metric_values,
            ),
            ensure_ascii=False,
        ),
    )


@mcp.tool()
async def create_base_resume(
    direction: str,
    bullet_ids: list[str],
    content: str,
    language: str | None = None,
) -> str:
    """Persist a base resume composed from selected bullets for a direction.

    A base resume is the starting point for later JD-tailored versions
    (see create_resume_version). The associated `project_name` is inferred
    from the first bullet's parent experience, so `bullet_ids` must be
    non-empty and reference real bullets.

    Args:
        direction: Career direction this resume targets (e.g. "backend").
            Free-form string; used in the filename.
        bullet_ids: Bullet ids to include, in display order. Must be
            non-empty. Each must reference an existing bullet.
        content: The full resume body as Markdown. Stored verbatim.
        language: ISO 639-1 language code (e.g. "en", "zh"). Optional.
            - Pass a code → filename suffixed `-{lang}` (per-language
              split resume).
            - Omit → no suffix (e.g. single bilingual file).

    Returns:
        The new resume's id (string, prefix "res-").

    Raises:
        ValueError: if `project_name` cannot be derived from `bullet_ids`
            (empty list or invalid ids).
    """
    return await _with_lock(
        "create_base_resume",
        backend.create_base_resume,
        direction=direction,
        bullet_ids=bullet_ids,
        content=content,
        language=language,
    )


@mcp.tool()
async def create_resume_version(
    name: str,
    base_id: str,
    jd: dict[str, Any],
    bullet_ids: list[str],
    content: str,
    language: str | None = None,
) -> str:
    """Persist a JD-tailored variant of an existing base resume.

    Inherits project_name and direction from the base. Computes a diff
    (`bullet_ids` added/removed vs the base) and stores it for
    traceability.

    Args:
        name: Short version name, used in the filename (e.g.
            "bytedance-backend-2026"). Must not contain path separators.
        base_id: ID of the base resume to derive from. Must come from
            list_resumes() and refer to a base resume (`is_base=True`).
        jd: Structured job-description metadata. Recommended keys:
            `company`, `role`, `requirements` (list). Stored as-is.
        bullet_ids: Final bullet ids included in this tailored version, in
            display order.
        content: Tailored resume body as Markdown. Stored verbatim.
        language: ISO 639-1 code. Optional. If omitted, inherits the base
            resume's language. Pass explicitly only when changing language.

    Returns:
        The new version's id (string, prefix "res-").

    Raises:
        ValueError: if `base_id` does not match any resume.
    """
    return await _with_lock(
        "create_resume_version",
        backend.create_resume_version,
        name=name,
        base_id=base_id,
        jd=jd,
        bullet_ids=bullet_ids,
        content=content,
        language=language,
    )


@mcp.tool()
async def list_resumes(direction: str | None = None) -> str:
    """List resume summaries, optionally filtered by direction.

    Read-only. Use to surface the user's existing resumes (both bases and
    tailored versions) for selection.

    Args:
        direction: If provided, filter to resumes whose `direction` matches
            exactly. Omit to list all.

    Returns:
        JSON string: a list of resume summaries, each containing id, name,
        direction, language, is_base, created_at. Use get_resume(id) to
        load the full body.
    """
    return await _with_lock(
        "list_resumes",
        lambda: json.dumps(backend.list_resumes(direction=direction), ensure_ascii=False),
    )


@mcp.tool()
async def get_resume(resume_id: str) -> str:
    """Load a single resume's full metadata and Markdown body.

    Read-only. Typically used to seed a tailored version from its base —
    preserving header, education, skills, and other non-bullet sections.

    Args:
        resume_id: ID returned by create_base_resume / create_resume_version
            / list_resumes.

    Returns:
        JSON string: the resume's full frontmatter (id, name, direction,
        project_name, language, is_base, base_id, jd, bullet_ids,
        diff_from_base, export_path, created_at) plus the Markdown body in
        a `content` field.

    Raises:
        ValueError: if `resume_id` does not match any resume.
    """
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
