---
name: qa-spec-engine
description: "【qa-suite 套装内部技能 · 通常无需直接调用，直接说需求给总控 qa-suite 即可】需求解构引擎：把 PRD / 原型 / 接口文档 / 用户故事确定性地拆成「模块 → 功能点 → 测试点 → 场景」四级结构，产出 Spec Model（spec-model.json）。这是全链路唯一上游，售前评估与用例生成都必须先用它。触发场景：拆解需求、提取功能点、梳理测试点、建 Spec Model、分析需求范围。"
---

# 需求解构引擎（qa-spec-engine）

<!-- 激活回执（必须填写并放在产出最前）
skill: qa-spec-engine
已读取: references/00-authority-map.md / 01-requirement-decomposition.md / 03-spec-model-schema.md
上游: <需求文档名 + 版本>
产出: spec-model.json
机检: validate_spec_model.py <PASS/FAIL>
-->

## 0. 定位

| 项 | 内容 |
| --- | --- |
| **唯一上游** | 本技能是 `qa-suite` 全链路的第一步，也是**唯一**的 Spec Model 生产者 |
| **输入** | 需求文档（PRD / 原型 / 接口文档 / 用户故事） |
| **输出** | `spec-model.json`（结构见 `../../references/03-spec-model-schema.md`） |
| **不做** | 不写用例、不算条数、不报价（那是下游三个引擎的事） |

## 1. 必读（缺一不可）

```
../../SKILL.md                                      （总控：锁与契约）
../../references/00-authority-map.md                （权威分布与冲突处置）
../../references/01-requirement-decomposition.md    ★ 主规约
../../references/03-spec-model-schema.md            ★ 产出格式
../../references/02-case-granularity-contract.md    （场景枚举规则，Step 4 要用）
../../references/05-priority-taxonomy.md            （场景优先级推导，Step 4 要用）
```

**读取纪律**：必须先读文件再开工，不允许"凭经验直接拆"。产出前自检"我读的文件是否在回执头里如实列出"。

## 2. 执行流程（严格按序）

### Step 1 · 建立完整模块索引

- **只扫结构**：标题层级（H1/H2/H3）、目录、图号、接口清单。**不读正文细节**。
- 索引必须覆盖**每一个章节**，不允许跳过。
- 大文档（> 50 页）分批读取，但索引**一次建全**。
- 每个模块记录：`名称 / 章节号 / 是否含界面 / 是否含接口 / 是否含状态流转 / 是否含权限`。

### Step 2 · 逐模块提取功能点

- 按 `01` 第 3.1 节判定功能点（可独立验证的业务能力）。
- **逐模块独立处理**，每个模块单独走一遍，避免全局浏览导致后段模块被简化。
- 大文档建议用并行子代理分别负责不同模块区间，但**每个模块只算一次**。

### Step 3 · 复杂度定级

- 按 `01` 第 3.2 节判据逐功能点定级，取最高命中档。
- **必须写定级理由** `complexity_reason`，否则机检不过。
- 定级**不用于换算用例条数**（条数由场景枚举得出，见 `04`）。

### Step 4 · 铺开测试点（五类）

按 `01` 第 4 节铺开：正向 / 边界 / 异常 / 状态 / 权限。

- 边界只在字段**有明确约束**时铺。
- 状态类只在模块**含状态流转**时铺。
- 权限类只在模块**含角色差异**时铺。
- 编号：`TP-<模块短码>-<三位序号>`。

### Step 5 · 枚举场景（关键步）

严格按 `02-case-granularity-contract.md` 第 3 节的四抓手枚举：

| 抓手 | 规则 |
| --- | --- |
| A 入口 | 每个独立页面/子页签 = 1 条；显著不同的进入路径 +1 |
| B 动词 | `动词 × 宾语` 唯一组合 = 1 条（**同一动词同一宾语只算 1 条**） |
| C 状态 | 每个合法转移 1 条；非法/越权转移 1 条；与 B 重复则去重 |
| D 角色 | 仅权限语义变化时 +1；仅数据范围不同不算 |

- 每个场景必须回填 `point_ids`（它承载的测试点），**非空**。
- 按 `05` 的 R1~R8 推导 `priority`。

### Step 6 · 去重与登记

- 按 `02` 第 5 节去重，差额逐条登记进 `dedup_log`。

### Step 7 · 登记缺口与假设

- `gaps[]`：正文缺失/描述简略的章节，给出 `placeholder_cases` 与 `included_in_baseline: false`（默认不计入基准）。
- `assumptions[]`：解构依赖的关键假设。
- `confidence`：`high` / `medium` / `low`。

### Step 8 · 机检（必做，不可跳过）

```bash
python3 "$SKILL_DIR/scripts/validate_spec_model.py" <spec-model.json>
python3 "$SKILL_DIR/scripts/count_cases.py" <spec-model.json>
```

- 两个脚本必须 PASS。FAIL 则回到对应 Step 修正后重跑。
- `count_cases.py` 的输出即该 Spec Model 的**用例条数**，把它回填到 `modules[].case_count`。

## 3. 遗漏检查（收尾前逐项核对）

直接执行 `01` 第 7 节的检查清单，并额外确认：

- [ ] 聚合比（测试点 ÷ 场景）是否落在 [1.5, 4.0]？
- [ ] 模块数、功能点数是否与文档章节数**可对应**（不能少章）？
- [ ] `gaps` 中的模块是否标记为 `placeholder` 且未计入基准？
- [ ] `meta.granularity_contract` 是否已声明？

## 4. 高发错误

| 错误 | 后果 | 正确做法 |
| --- | --- | --- |
| 边读边估、跳过 Step 1 | 后段章节系统性漏项 | 先建全量索引 |
| 功能点定级不留 `complexity_reason` | 机检 FAIL、无法复核 | 必填 |
| 功能点为空 | 机检 FAIL | 无功能点的"章节"不是模块 |
| 场景不填 `point_ids` | 机检 FAIL、追溯断裂 | 必填非空 |
| 把字段/按钮当功能点 | 功能点虚高 | 按 `01` 第 3.1 节判定 |
| 场景按"每个字段一条"枚举 | 聚合比 < 1.5，粒度违规 | 校验维度落入步骤 |
| 文档缺口模块照常估 | 报价虚高 | 标 `placeholder` + `included_in_baseline: false` |
| 跳过机检直接交付 | 下游全部基于脏数据 | Step 8 必做 |

## 5. 产出交付格式

1. **激活回执头**（本文件开头模板）
2. **Spec Model 文件**：`spec-model.json`
3. **模块概览表**（人读）：

| 模块 | 章节 | 功能点数 | 简/中/复 | 测试点数 | 场景数(=用例数) |
| --- | --- | --- | --- | --- | --- |

4. **机检结果**：两个脚本的 PASS/FAIL 原文输出
5. **假设与缺口**：`assumptions` 与 `gaps` 逐条列出
6. **置信度**与理由