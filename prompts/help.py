from __future__ import annotations

HELP_PROMPT = """## Resume Agent 使用指南

### 可用命令

| 命令 | 功能 |
|------|------|
| `/init` | 创建新经历（项目/实习/工作） |
| `/log` | 记录成就 bullet，关联到已有经历 |
| `/resume` | 从 bullet 组合生成基础简历 |
| `/tailor` | 针对具体 JD 定制简历版本 |
| `/update` | 更新经历（开发中） |
| `/help` | 显示此帮助信息 |

### 推荐工作流

```
/init   →  创建经历锚点（公司/项目）
  ↓
/log    →  反复记录每条成就（可多次使用）
  ↓
/resume →  选择 bullet 组合，生成基础简历
  ↓
/tailor →  针对每个目标 JD 生成定制版本
```

### 使用建议

- 每次 `/log` 只提交一条成就，等确认后再提交下一条
- 一个经历可以对应多条 bullet，多次使用 `/log` 即可
- 一份基础简历可以对应多个 `/tailor` 定制版本
"""
