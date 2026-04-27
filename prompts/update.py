from __future__ import annotations

UPDATE_PROMPT = """## /update — 修改已有经历或 Bullet

你的任务：帮用户修改已存在的 experience 或 bullet 的字段。这是 partial update——只动用户想改的字段，其它保持不变。

⚠️ 一次只处理一条，写入成功后等用户提交下一条。

步骤：

1. 询问用户想改的对象类型：
   - `experience`（经历元数据，如 role / 时间 / 标签）
   - `bullet`（成就 bullet 的文本、tags、category 等）

2. **如果改 experience**：
   1. 调用 get_experiences() 列出所有经历，让用户选 exp_id。
   2. 询问用户想改哪些字段。可改字段：
      - organization / role / start / end
      - exp_type（"internship" / "fulltime" / "project" / "research"）
      - direction_tags / skill_tags / tool_tags（**注意：传入是替换整个列表，不是追加**）
   3. ⚠️ **不能改 project_name 和 direction**——它们决定文件名和 bullet 的父目录。如果用户要改这两个字段，告知当前版本不支持，建议用 /init 重建。
   4. 用户确认改动后，调用 update_experience()，**只传需要改的字段**，其余参数留空（不传或显式传 None）。

3. **如果改 bullet**：
   1. 调用 get_experiences() 让用户选属于哪条经历，再调用 list_bullets(exp_id) 列出该经历下的 bullet，让用户选 bullet_id。
   2. 询问用户想改哪些字段。可改字段：
      - bullet_name（文件名 tag，不要含路径分隔符）
      - raw（原始描述）
      - rewritten（dict 格式，键为语言代码；必须非空）
      - skill_tags / tool_tags / metric_values（**全列表替换**）
      - category（"achievement" / "skill" / "responsibility"）
      - has_number（是否含量化数据）
   3. ⚠️ **不能改 exp_id**——bullet 一旦归属某条经历就不能跨经历移动。
   4. 如果用户要改 rewritten 的文本：
      - 保持原有语言集合（除非用户明确说要加 / 删某语言）
      - 沿用 /log 的风格规则：英文动词开头过去式 ≤20 词；中文动词开头 ≤30 字
      - 改动后展示新版给用户确认
   5. 用户确认后，调用 update_bullet()，**只传需要改的字段**。

4. 写入成功后，简要展示更新后的关键字段，告知用户改动已生效。

可用工具：get_experiences, list_bullets, update_experience, update_bullet
"""
