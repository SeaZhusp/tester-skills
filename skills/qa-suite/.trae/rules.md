# qa-suite 规则入口

以仓库根目录的 `SKILL.md` 为唯一权威。执行测试相关任务前先完整读取它，再按其中的「子技能路由表」与「强制读取清单」读取 `references/` 与 `subskills/`。

关键约束：
- 售前评估用例数 = 用 `scripts/count_cases.py` 对 Spec Model 做模拟计数，不得凭经验估数。
- 用例计量单位见 `references/02-case-granularity-contract.md`，全链路唯一。
- 交付前三个机检脚本必须 PASS。