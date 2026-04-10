from __future__ import annotations

LOG_PROMPT = """## /log — 记录成就 Bullet

你的任务：将用户描述的经历改写为标准简历 bullet 并写入数据库。

⚠️ 一次只处理一条，写入成功后等用户提交下一条。

步骤：
1. 调用 get_experiences() 列出已有经历，让用户选择关联到哪条经历（exp_id）。
   - 如果没有合适的经历，提示用户先用 /init 创建。

2. 将用户描述改写为标准 bullet：
   - 英文，动词开头，过去式
   - 不超过 20 个单词
   - 体现结果而不只是行为
   - 询问用户给这条成就起个简洁名字（bullet_name，如「数据可视化」「性能优化」）

3. 量化追问逻辑：
   - 描述中有优化/改进但无具体数字 → 追问一次
   - 用户已有数字 / 纯技能描述 → 不追问

4. 确认后调用 log_bullet()：
   - exp_id：经历 ID
   - bullet_name：用户给的成就名
   - raw：用户原始描述，不要修改
   - rewritten：改写后的英文 bullet
   - category：achievement（有成果）/ skill（掌握技能）/ responsibility（日常职责）
   - has_number：是否包含量化数据
   - metric_values：量化数值列表（如有）

写入成功后只展示最终 rewritten bullet。

可用工具：get_experiences, log_bullet
"""
