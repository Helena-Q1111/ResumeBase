# ResumeBase

An MCP (Model Context Protocol) server that acts as an AI-powered resume material manager. It helps users systematically collect, organize, and reuse their professional experiences and achievements to generate tailored resumes.

**Repo:** [github.com/Helena-Q1111/ResumeBase](https://github.com/Helena-Q1111/ResumeBase)

## What It Does

Job seekers often struggle to recall and articulate their accomplishments when writing resumes, especially when tailoring them for different positions. ResumeBase solves this by providing a structured workflow:

1. **Log experiences** — Record each project, internship, or job as a structured entry with metadata (organization, role, dates, skill/tool tags).
2. **Log achievement bullets** — For each experience, incrementally log accomplishments. The agent rewrites raw descriptions into polished, concise resume bullets (supporting multiple languages).
3. **Generate base resumes** — Select a subset of bullets and compose a base resume for a given career direction.
4. **Tailor for specific jobs** — Given a job description (JD), generate a customized resume version by swapping, reordering, or rewriting bullets to match the target role.

All data is stored as **Markdown files with YAML frontmatter**, making it human-readable, version-controllable, and compatible with tools like Obsidian.

## Architecture

ResumeBase is built as an **MCP server** using the [FastMCP](https://github.com/jlowin/fastmcp) framework. It exposes tools and prompts that any MCP-compatible AI client (e.g., Claude Desktop) can call:

- **Tools** — `create_experience`, `log_bullet`, `list_bullets`, `create_base_resume`, `create_resume_version`, `list_resumes`, `get_resume`, `get_experiences`
- **Prompts** — `/init`, `/log`, `/resume`, `/tailor`, `/update`, `/help` — each guides the AI through a specific workflow step
- **Storage** — A pluggable backend (currently Markdown-based) that persists everything to local files

```
server.py          — MCP server entry point, tool/prompt registration
prompts/           — Prompt templates for each workflow command
storage/base.py    — Abstract storage interface
storage/markdown.py — Markdown + frontmatter implementation
config.example.yaml — Default configuration
```

## Setup

```bash
pip install -r requirements.txt
python server.py
```

Configure storage path in `config.yaml` (auto-created on first run from `config.example.yaml`).

## Current Status & Remaining Work

The core functionality is complete. Remaining work for the final milestone:

- **Documentation** — Expand usage guides and add examples
- **Bug fixes** — Address edge cases in bullet/resume management
- **`/update` command** — Finish the experience update workflow
