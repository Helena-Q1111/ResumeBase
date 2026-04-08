from __future__ import annotations

"""
Claude Desktop 注册示例（claude_desktop_config.json）：

{
  "mcpServers": {
    "resume-agent": {
      "command": "python",
      "args": ["绝对路径/server.py"]
    }
  }
}
"""

from mcp.server.fastmcp import FastMCP

from prompts.templates import LOGGING_SYSTEM_PROMPT
from tools.logging import create_experience, get_experiences, log_bullet


mcp = FastMCP("resume-agent")


# Directly register the three logging tools imported from tools/logging.py.
mcp.tool()(get_experiences)
mcp.tool()(create_experience)
mcp.tool()(log_bullet)


@mcp.prompt(name="log")
def log_prompt() -> str:
    """Prompt invoked by /log in Claude Desktop."""
    # If your installed SDK version uses a different prompt decorator signature,
    # replace with the closest equivalent (e.g. @mcp.prompt("log")).
    return LOGGING_SYSTEM_PROMPT


if __name__ == "__main__":
    # 验证方式：
    # 1) 启动：在项目根目录执行 `python server.py`（或由 Claude Desktop 按配置自动拉起）。
    # 2) 验证 get_experiences：在 Claude Desktop 输入 `/log` 后发送“先帮我看已有经历”，
    #    正常情况下模型会调用 get_experiences 并返回已有 experience 摘要。
    # 3) 验证 log_bullet：在 Claude Desktop 继续输入一条可归属的经历描述，
    #    然后检查 data/db.json 中对应 experience 的 bullets 下是否新增 bul_xxxxxx 记录。
    mcp.run()
