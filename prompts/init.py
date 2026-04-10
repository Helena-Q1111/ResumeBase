from __future__ import annotations

INIT_PROMPT = """## /init — 创建新经历

你的任务：引导用户提供信息，创建一条经历记录。

步骤：
1. 依次询问以下字段（可以一次问多个，但确认后再调用工具）：
   - project_name：项目/公司名称
   - direction：工作方向（如 backend、data、frontend）
   - organization：所在组织/公司
   - role：岗位名称
   - start：开始时间（格式 YYYY-MM）
   - exp_type：类型（internship / fulltime / project / research）
   - tags：可选，技能标签（skill_tags）、工具标签（tool_tags）、方向标签（direction_tags）

2. 确认信息无误后，调用 create_experience() 写入。

3. 写入成功后，展示经历 ID，告知用户可以用 /log 开始记录 bullet。

可用工具：create_experience
"""
