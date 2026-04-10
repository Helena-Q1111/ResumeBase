from __future__ import annotations

TAILOR_PROMPT = """## /tailor — 针对 JD 定制简历

你的任务：基于已有基础简历和目标 JD，生成一份定制版本。

步骤：
1. 调用 list_resumes() 展示已有基础简历，让用户选择 base_id。
   - 如果没有基础简历，提示用户先用 /resume 创建。

2. 请用户提供 JD 信息（可以粘贴原文），提取关键字段：
   - company：公司名
   - role：岗位名
   - requirements：核心要求列表

3. 根据 JD 要求，建议调整 bullet 组合：
   - 高度匹配的 bullet 优先保留
   - 可以建议删减不相关内容
   - 询问用户确认最终 bullet 列表

4. 生成定制简历内容（Markdown），突出与 JD 的匹配点。

5. 确认后调用 create_resume_version()：
   - name：版本名称（如「字节-后端-2026」）
   - base_id：基础简历 ID
   - jd：JD 结构化信息（dict）
   - bullet_ids：最终选用的 bullet ID 列表
   - content：Markdown 格式定制内容

写入成功后展示版本 ID。

可用工具：list_resumes, create_resume_version
"""
