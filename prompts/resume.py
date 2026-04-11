from __future__ import annotations

RESUME_PROMPT = """## /resume — 创建基础简历

你的任务：根据用户给的目标岗位方向，挑选合适的经历和 material，起草一份基础简历。

步骤：

1. 询问用户**目标岗位方向**（如 backend、data、PM、frontend）。

2. 调用 get_experiences() 拿到所有经历，按 exp_type 分组筛选：
   - `internship`、`fulltime` → **全部纳入**（工作履历不省略）
   - `project`、`research` → 根据 direction、direction_tags、skill_tags 与目标方向的匹配度，**挑最合适的几条**（建议 2–3 条）

3. 把筛选后的经历清单展示给用户，**询问是否合适或需要调整**：
   - 用户确认 OK → 进入下一步
   - 用户要修改 → 让用户给出要增加 / 删除的经历，更新清单后再次确认

4. 经历清单确定后，对每条调用 list_bullets(exp_id)，读取该经历下的所有 material。
   - 注意 bullet 的 `languages` 和 `rewritten` 字段，rewritten 是 dict，键为语言代码

5. **决定输出语言**：
   - 看选中 bullet 的语言情况（单语 / 多语）
   - 如果只有单一语言 → 直接用该语言起草
   - 如果是多语言 → **询问用户**输出形式：
     - **A. 拆分文件**：每种语言生成一份独立简历（如 `resume-backend-base-en.md` + `resume-backend-base-zh.md`）
     - **B. 单文件双语**：一份简历，同一段内中英交替排版

6. 基于读到的 material 起草简历正文（Markdown）：
   - 按经历分组排列
   - 每条经历下挑与目标方向最相关的 bullet
   - 工作经历可多保留，项目经历精炼
   - 按第 5 步确定的语言形式渲染

7. 展示简历草稿，用户确认后调用 create_base_resume()：
   - **输出形式 A（拆分文件）**：分别调用两次（或多次），每次：
     - direction：目标方向
     - bullet_ids：选用的 bullet ID 列表
     - content：该语言版本的 Markdown 正文
     - language：语言代码（如 `"en"` / `"zh"`）
   - **输出形式 B（单文件双语）**：调用一次，**不传 language**：
     - direction / bullet_ids / content（双语交替的 Markdown）
   - **单语言场景**：调用一次，可传也可不传 language（建议传，便于以后区分）

写入成功后展示简历 ID，告知用户可以用 /tailor 针对 JD 定制版本。

可用工具：get_experiences, list_bullets, create_base_resume
"""
