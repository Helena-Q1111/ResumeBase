from __future__ import annotations

RESUME_PROMPT = """## /resume — 创建基础简历

你的任务：帮用户从已有 bullet 中选择组合，生成一份基础简历。

步骤：
1. 调用 get_experiences() 展示所有经历及其 bullet，供用户选择。

2. 询问用户：
   - 目标方向（direction），如 backend、data、PM
   - 希望包含哪些 bullet（可以多选）

3. 根据所选 bullet 起草简历内容（content），格式为 Markdown。
   - 按经历分组排列
   - 保留用户选择的所有 bullet

4. 展示草稿，用户确认后调用 create_base_resume()：
   - direction：目标方向
   - bullet_ids：所选 bullet 的 ID 列表
   - content：Markdown 格式简历正文

写入成功后展示简历 ID，告知用户可以用 /tailor 针对 JD 定制版本。

可用工具：get_experiences, create_base_resume
"""
