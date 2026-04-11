from __future__ import annotations

TAILOR_PROMPT = """## /tailor — 针对 JD 定制简历

你的任务：基于已有基础简历和目标 JD，生成一份定制版本。

步骤：
1. 调用 list_resumes() 展示已有基础简历，让用户选择 base_id。
   - 如果没有基础简历，提示用户先用 /resume 创建。
   - 注意每条简历的 `language` 字段，定制版本默认沿用 base 的语言。

2. 调用 get_resume(base_id) 读取 base 简历的完整正文和元数据。
   - **以 base 正文作为起草起点**，保留 header / education / skills 等非 bullet 章节
   - 拿到 base 的 `bullet_ids` 作为初始候选集

3. 请用户提供 JD 信息（可以粘贴原文），提取关键字段：
   - company：公司名
   - role：岗位名
   - requirements：核心要求列表

4. 根据 JD 要求，在 base 基础上建议调整：
   - 高度匹配的 bullet 优先保留
   - 不相关 bullet 建议删减
   - 必要时调整段落顺序、措辞重点
   - 询问用户确认最终 bullet 列表

5. 在 base 正文上做最小必要修改，生成定制简历内容（Markdown）：
   - 不重建结构，只改要改的部分
   - 语言沿用 base 的 `language`：单语言 → 同语言；双语 base（language 为空，单文件双语）→ 同样保持双语交替
   - 如果 base 是按语言拆分的（language 已设），定制版本通常也只针对该语言生成

6. 确认后调用 create_resume_version()：
   - name：版本名称（如「字节-后端-2026」）
   - base_id：基础简历 ID
   - jd：JD 结构化信息（dict）
   - bullet_ids：最终选用的 bullet ID 列表
   - content：Markdown 格式定制内容
   - language：可选，**默认不传**会自动沿用 base 的语言；只有当用户明确要换语言时才显式传

写入成功后展示版本 ID。

可用工具：list_resumes, get_resume, create_resume_version
"""
