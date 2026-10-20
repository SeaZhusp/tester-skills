---
name: qa-estimate-engine
description: "【qa-suite 套装内部技能 · 通常无需直接调用，直接说需求给总控 qa-suite 即可】售前评估与报价引擎：基于 Spec Model 做「模拟计数」得出用例条数，输出可行性结论、三档区间、冒烟占比、测试周期与人员投入，并按优先级或测试类型计价生成计费报告。触发场景：售前需求评估、能不能做、大概多少用例、要多久、要几个人、报价、按优先级计价、计费 Excel。"
---

# 售前评估与报价引擎（qa-estimate-engine）

<!-- 激活回执（必须填写并放在产出最前）
skill: qa-estimate-engine
已读取: references/03-spec-model-schema.md / 04-counting-and-conversion.md /
        05-priority-taxonomy.md / assets/estimate-config.json (若出报价: assets/pricing-config.json)
条数来源: scripts/count_cases.py <spec-model.json>  （模拟计数）
上游: spec-model.json
-->

## 0. 定位与铁律

| 项 | 内容 |
| --- | --- |
| **输入** | `spec-model.json`（**必须**）+ 可选团队人数 / 目标周期 |
| **输出** | 评估报告 md（+ 可选计费 Excel） |
| **铁律 1** | 用例条数**只能**来自 `scripts/count_cases.py`，禁止手写、禁止按经验倍率推算 |
| **铁律 2** | 三档区间**必须有具体来源**（未决项），不是"基准 × 0.8 / × 1.2" |
| **铁律 3** | 优先级分布用**真实统计**（`count_cases.py` 的 `priority_counts`），不预设任何比例 |
| **铁律 4** | 报告必附**模块级明细表**，不允许只给总数 |

> **为什么铁律 1 不可协商**：评估报告上的条数如果不由 Spec Model 数出来，就无法与最终交付的用例逐条对齐。
> 两个数字之间没有桥梁，客户质疑时无法自证，偏差只能等交付完成才发现——那时已经无法补救。

## 1. 必读

```
../../SKILL.md                                        （锁与门禁）
../../references/04-counting-and-conversion.md        ★★ 计数口径与换算
../../references/03-spec-model-schema.md
../../references/05-priority-taxonomy.md
../../references/02-case-granularity-contract.md      （口径来源）
../../assets/estimate-config.json                     （参数，禁止硬编码）
../../assets/pricing-config.json                      （出报价时）
```

## 2. 执行流程

### Step 1 · 前置检查

- 无 Spec Model → **先路由 `qa-spec-engine`**。跳过解构直接估数是**明令禁止**的。
- 确认 Spec Model 已通过 `validate_spec_model.py`。

### Step 2 · 模拟计数（核心）

```bash
python3 "$SKILL_DIR/scripts/count_cases.py" spec-model.json --json
```

输出：总条数 / 模块明细 / 测试点总览 / 聚合比。
**该输出即最终条数，直接使用，不得调整。**

### Step 3 · 可行性判定

依据四类证据给结论（✅ 可承接 / ⚠️ 有条件承接 / ❌ 不建议承接）：

1. **技术范围**：是否在团队已有能力范围内（功能/接口/UI/性能/安全/兼容/真机）。
2. **需求完整度**：`meta.confidence` + `gaps` 数量与影响面。
3. **外部依赖**：需要的账号/接口文档/环境/第三方服务，是否可得；不可得则列为**承接前提**。
4. **范围明确性**：本期范围与砍掉项是否清晰。

**"有条件承接"必须列出前提条件清单**（缺什么、谁提供、不提供会导致哪部分不可验证）。

### Step 4 · 三档区间（来源可解释）

按 `04` 第 3 节：

| 档 | 来源 |
| --- | --- |
| 保守（min） | 基准 − `gaps` 中 `included_in_baseline=true` 的占位 − 跨模块集成场景 |
| 基准（typical） | `count_cases.py` 全部枚举结果 |
| 激进（max） | 基准 + `gaps` 全部占位 + 跨模块集成/契约场景 + 非功能加点 |

**报告必须逐条列出未决项**（哪些模块不计入基准、为什么）。

### Step 5 · 冒烟用例

- 冒烟集 = **P0 集合**（含端到端 L0 主场景），两者必须完全一致（`05` 第 2 节）。
- 占比 = 冒烟数 ÷ 总数，基准 10%，合理区间 8%~15%。
- **必须列出端到端 L0 主场景清单**（如 E2E-1 ~ E2E-n），不能只给个数。

### Step 6 · 周期与人员

```bash
echo '{"total_cases": <条数>, "team_size": <人数>}' | python3 "$SKILL_DIR/scripts/estimate.py"
# 或给定周期算人数：
echo '{"total_cases": <条数>, "target_days": <自然日>}' | python3 "$SKILL_DIR/scripts/estimate.py"
```

- 参数取自 `assets/estimate-config.json`（产能参数已按聚合用例口径标定，见 `04` 第 6 节）。
- 输出各阶段人天 + 含缓冲合计 + 周期/人数。**报告必须引用脚本输出，不得手算。**

### Step 7 · 报价（用户要报价时）

- 方案与单价取 `assets/pricing-config.json`。
- 计价条数 = **真实统计**（`count_cases.py` 条数 + 真实优先级/类型分布）。
- 输出：统计明细 + 计价明细 + 小计 + 总计。
- 提供两套方案对比（按优先级 / 按测试类型），由用户选择。

### Step 8 · 门禁

```bash
python3 "$SKILL_DIR/scripts/check_consistency.py" --estimate <spec-model.json> --cases <用例集.json>   # 若已交付用例
```
- 交付前必须 PASS；若尚无用例集，则至少完成 `count_cases.py` 与 `validate_spec_model.py`。

## 3. 报告结构（固定模板）

```markdown
<!-- 激活回执头 -->

# 《<项目名>》测试需求评估报告

## 一、可行性结论
结论（可承接 / 有条件承接 / 不建议）+ 判定依据 4 条 + 承接前提条件清单

## 二、需求范围与模块概览
| 模块 | 章节 | 功能点数 | 复杂度构成(简/中/复) | 测试点数 | 用例数(基准) |

## 三、用例规模估算
- 估算方法：需求解构 + 场景枚举 + 模拟计数（条数由枚举得出，不做公式推算）
- 总数区间：保守 X / 基准 Y / 激进 Z（附未决项来源）
- 模块级明细表（证据链）
- 多视角交叉校验结果（模块 / 状态机 / 角色 / 端到端）
- 假设清单 + 置信度

## 四、冒烟测试占比
条数 + 占比 + 端到端 L0 主场景清单

## 五、测试周期计划与人员投入
（三档各一张：优先级分布 / 各阶段人天 / 周期与人数）
参数说明（引用 estimate-config.json）

## 六、风险与待澄清项
gaps 逐条 + 影响范围 + 建议动作
```

## 4. 严格禁止

| 禁止 | 原因 |
| --- | --- |
| "功能点数 × 每功能点 N 条" 估算条数 | 把聚合度当常数，结果不可核销 |
| 手写条数（不经 `count_cases.py`） | 与交付口径脱节 |
| 三档 = 基准 × 0.8 / × 1.2 | 差异无来源、不可解释 |
| 先定 P0/P1/P2/P3 比例再往用例上套 | 比例是预设值，与业务风险无关，直接扭曲按优先级计价的总价 |
| 只给总数不给模块明细 | 不可追溯、不可核销 |
| 手算人天而不跑 `estimate.py` | 参数失控 |
| 在报告里硬编码参数值 | 违反配置唯一契约 |
| 文档缺口模块照常计入基准 | 报价虚高 |

## 5. 高发错误

| 错误 | 后果 |
| --- | --- |
| 跳过 Spec Model 直接估 | 条数无来源，报告不可核销 |
| 按细碎用例口径标定产能（如 300 条/人天） | 人天低估约 3 倍（必须按聚合用例口径取值） |
| 冒烟占比偏离 8%~15% 不解释 | 说明枚举有偏 |
| 未列出未决项 | 三档区间不可信 |
| 报了价但没给统计明细 | 客户无法核对 |

## 6. 交付格式

1. **激活回执头**
2. 评估报告 md（按第 3 节模板）
3. **机检与脚本原文输出**：`count_cases.py`、`estimate.py`（、`check_consistency.py`）
4. 可选：计费 Excel
5. 待澄清项清单（`gaps`）