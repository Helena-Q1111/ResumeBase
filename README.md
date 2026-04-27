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

### 5. Typical workflow

| Command   | What it does                                                  |
| --------- | ------------------------------------------------------------- |
| `/init`   | Set up your profile and create your first experience entry   |
| `/log`    | Add achievement bullets to an existing experience            |
| `/resume` | Compose a base resume for a career direction                 |
| `/tailor` | Generate a JD-tailored version of a base resume              |
| `/update` | Edit existing experiences or bullets                         |
| `/help`   | Show available commands                                      |

## License

[MIT](LICENSE)