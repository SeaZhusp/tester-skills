# 测试服务套件（qa-suite）

本项目为**测试服务交付套件**。执行本仓库内任何测试相关任务前，**先完整读取 `SKILL.md`**，它是唯一权威入口。

- 共享规则：`references/`（唯一真相，禁止另立摘要）
- 子技能：`subskills/qa-spec-engine|qa-case-engine|qa-estimate-engine|qa-audit-engine`
- 机检脚本：`scripts/validate_spec_model.py`、`count_cases.py`、`check_consistency.py`

核心纪律：**先出 Spec Model，再投影**。售前评估的用例条数必须由 `count_cases.py` 模拟计数得出，不允许凭经验估算。