# ResumeBase

An MCP (Model Context Protocol) server that acts as an AI-powered resume material manager. It helps users systematically collect, organize, and reuse their professional experiences and achievements to generate tailored resumes.

## What It Does

Job seekers often struggle to recall and articulate their accomplishments when writing resumes, especially when tailoring them for different positions. ResumeBase solves this by providing a structured workflow:

1. **Log experiences** — Record each project, internship, or job as a structured entry with metadata (organization, role, dates, skill/tool tags).
2. **Log achievement bullets** — For each experience, incrementally log accomplishments. The agent rewrites raw descriptions into polished, concise resume bullets (supporting multiple languages).
3. **Generate base resumes** — Select a subset of bullets and compose a base resume for a given career direction.
4. **Tailor for specific jobs** — Given a job description (JD), generate a customized resume version by swapping, reordering, or rewriting bullets to match the target role.

All data is stored as **Markdown files with YAML frontmatter**, making it human-readable, version-controllable, and compatible with tools like Obsidian.

## Architecture

ResumeBase is a layered system built on [FastMCP](https://github.com/jlowin/fastmcp): **prompts** drive workflows, **tools** read and write data, **storage** persists everything as files.

```
MCP Client  (Claude Desktop / Codex / Gemini CLI / Cursor / ...)
     │  stdio + MCP protocol
     ▼
┌──────────────────────────────────────────────────┐
│  server.py  (FastMCP)                            │
│                                                  │
│   Prompts  ──invoke──►  Tools                    │
│   (workflow             (data ops, contract-only)│
│    scripts)                  │                   │
│                              ▼                   │
│                       Storage backend            │
│                       (pluggable; Markdown today)│
└──────────────────────────────────────────────────┘
```

### Three layers

- **Prompts** ([prompts/](prompts/)) — workflow scripts loaded when the user invokes a slash command; they tell the LLM what to ask the user and which tools to call.
- **Tools** (`@mcp.tool()` in [server.py](server.py)) — the data-operation API the LLM calls to read or write resume material.
- **Storage** ([storage/](storage/)) — pluggable backend behind a `StorageBackend` interface; the default writes Markdown + YAML frontmatter to local files.

### Workflows

| Slash command | Tools used | What it does |
| --- | --- | --- |
| `/init`    | `create_experience` | Create a new experience entry (project / job / internship / research) |
| `/log`     | `get_experiences`, `log_bullet` | Log a polished achievement bullet under an existing experience |
| `/resume`  | `get_experiences`, `list_bullets`, `create_base_resume` | Compose a base resume for a career direction |
| `/tailor`  | `list_resumes`, `get_resume`, `create_resume_version` | Generate a JD-tailored version from a base resume |
| `/update`  | `get_experiences`, `list_bullets`, `update_experience`, `update_bullet` | Edit existing experiences or bullets (partial update) |
| `/help`    | —                                                       | Show available commands |

> **`/update` v1 limitations**
> - Cannot change an experience's `project_name` or `direction` — they form the filename and the bullet parent path. To rename, recreate the experience.
> - Cannot move a bullet to a different experience (`exp_id` is fixed).
> - Tag fields (`*_tags`, `metric_values`) are replaced wholesale, not appended.

### File layout

```
server.py            — MCP server entry; tool & prompt registration
prompts/             — Workflow scripts (one file per slash command)
storage/base.py      — Abstract StorageBackend interface
storage/markdown.py  — Markdown + YAML frontmatter implementation
config.example.yaml  — Default config; copied to user-config dir on first run
```

## Quickstart

### 1. Requirements

- Python 3.10+
- An MCP-compatible client (e.g. [Claude Desktop](https://claude.ai/download), Claude Code)

### 2. Install

```bash
git clone https://github.com/Helena-Q1111/ResumeBase.git
cd ResumeBase
pip install -r requirements.txt
```

### 3. Connect to your MCP client

ResumeBase runs as a local stdio MCP server — your client launches `server.py` on demand, you don't start it manually. **Each MCP client keeps its own server list**, so add ResumeBase to whichever client(s) you want to use it from. The same `server.py` works for all of them.

Replace `/absolute/path/to/ResumeBase/server.py` in the snippets below with the actual path on your machine.

<details open>
<summary><b>Claude Desktop</b></summary>

Settings → Developer → Edit Config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "resume-agent": {
      "command": "python",
      "args": ["/absolute/path/to/ResumeBase/server.py"]
    }
  }
}
```
</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add resume-agent -- python /absolute/path/to/ResumeBase/server.py
```
</details>

<details>
<summary><b>Codex CLI</b></summary>

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.resume-agent]
command = "python"
args = ["/absolute/path/to/ResumeBase/server.py"]
```
</details>

<details>
<summary><b>Gemini CLI</b></summary>

Edit `~/.gemini/settings.json` (user scope) or `.gemini/settings.json` (project scope):

```json
{
  "mcpServers": {
    "resume-agent": {
      "command": "python",
      "args": ["/absolute/path/to/ResumeBase/server.py"]
    }
  }
}
```
</details>

<details>
<summary><b>Cursor</b></summary>

Create `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per-project):

```json
{
  "mcpServers": {
    "resume-agent": {
      "command": "python",
      "args": ["/absolute/path/to/ResumeBase/server.py"]
    }
  }
}
```
</details>

Restart the client after editing. You should see `/init`, `/log`, `/resume`, `/tailor`, `/update`, `/help` in the slash-command list.

> **Tip:** if `python` isn't on your PATH or you use a virtualenv, replace `"python"` with the absolute path to the interpreter (e.g. `/Users/you/.venv/bin/python`).

### 4. First run

In your MCP client, run `/init` to start. The server will:

- Create `config.yaml` at the OS user-config path on first launch:
  - macOS: `~/Library/Application Support/resume-agent/config.yaml`
  - Linux: `~/.config/resume-agent/config.yaml`
  - Windows: `%APPDATA%\resume-agent\config.yaml`
- Store your resume data under the OS user-data path by default:
  - macOS: `~/Library/Application Support/resume-agent/data/`
  - Linux: `~/.local/share/resume-agent/data/`
  - Windows: `%LOCALAPPDATA%\resume-agent\data\`
- Write logs to the OS user-log path (`server.log`).

To use a custom location (e.g. an Obsidian vault), edit `config.yaml`:

```yaml
storage:
  backend: markdown
  vault_path: /Users/you/Documents/MyVault/Resume   # absolute path
```

Relative paths are resolved against the user-data directory above.

### 5. Next

Run `/init` to create your first experience, then `/log` to add bullets. See [Architecture → Workflows](#workflows) for the full command list and what each one does.

## License

[MIT](LICENSE)