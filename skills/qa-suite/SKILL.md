---
name: qa-suite
description: "测试服务全流程总控（1 总控 + 4 子技能 + 共享权威层）。覆盖「需求解构 → 用例生成 → 售前评估/报价 → 一致性核销」全链路，并用同一份 Spec Model 与同一套用例粒度契约，消除售前评估用例数与最终交付用例数的偏差。触发场景：测试需求评估、售前报价、生成测试用例、提取测试点、梳理业务场景、用例评审查漏、导入禅道/TestRail/飞书表格。用户直接说需求即可，本总控会自动路由到对应子技能。"
---

# 测试服务总控（qa-suite）

> 版本：1.0 ｜ 定位：**测试服务交付的单一入口与共享权威**
> 一句话：**一份需求解构产物（Spec Model），喂给多个投影器（评估 / 用例 / 报价 / 核销），全链路同一套计量单位。**

---

## 0. 你是什么，不是什么

| 你是 | 你不是 |
| --- | --- |
| 测试服务交付的**唯一入口**与**唯一权威来源** | 不是用例生成器本身（那是 `qa-case-engine`） |
| 共享规则（计量单位、优先级、追溯、口径）的**持有者** | 不是把子技能内容抄一遍的"大杂烩" |
| 任务路由、锁选择、机检门禁的**执行者** | 不负责领域专精（画布交互、AI 用例生成等细节） |
| 交付质量的**最终把关人**（机检 FAIL 不许交付） | 不允许子技能自行发明计量口径或输出格式 |

**最高原则**：跨阶段共用的内容**只在 `references/` 定义一次**，子技能只读取、不另立。
（这是本套件的全部设计前提：同一个计量单位被 N 个环节各自表述一次，就会分裂出 N 套口径，且每一套都能自圆其说。）

---

## 1. 组织原则：一份权威，多个投影

```
                     ┌─────────────────────────────┐
                     │   需求文档 PRD / 原型 / 接口  │
                     └──────────────┬──────────────┘
                                    │ ① 解构（唯一一次）
                                    ▼
                     ┌─────────────────────────────┐
                     │  Spec Model（唯一上游产物）  │
                     │  模块 → 功能点 → 测试点 → 场景 │
                     └──────────────┬──────────────┘
                                    │ ② 投影（可多条，共用规则）
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
      ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
      │ 售前评估/报价  │    │   用例集交付   │    │  一致性核销    │
      │ (模拟计数投影) │    │ (文本化投影)   │    │ (回填校准投影) │
      └───────────────┘    └───────────────┘    └───────────────┘
              └─────────────────────┴─────────────────────┘
                        同源 · 同规则 · 可核销
```

**两条铁律（违反任一，偏差必然复现）**：

1. **唯一上游**：禁止任何一个子技能绕过 Spec Model 直接从需求文档数数/写用例。
2. **唯一计量单位**：定义见 `references/02-case-granularity-contract.md`。售前"预估条数"与交付"实际条数"必须是**同一量纲、同一聚合规则**。

---

## 2. 目录地图与文件所有权

```
qa-suite/
├── SKILL.md                        ← 你（总控，唯一真身入口）
├── AGENTS.md / CLAUDE.md / .trae/  ← 跨平台薄壳入口（只指向 SKILL.md）
├── references/                     ← ★ 共享权威层（唯一真相）
│   ├── 00-authority-map.md             权威地图：什么内容唯一在哪里
│   ├── 01-requirement-decomposition.md 需求解构规约（模块/功能点/复杂度定级判据）
│   ├── 02-case-granularity-contract.md ★★ 用例粒度契约（计量单位 + 聚合规则）
│   ├── 03-spec-model-schema.md         ★ Spec Model 数据模型（全链路交接格式）
│   ├── 04-counting-and-conversion.md   ★ 计数口径与换算（评估=交付口径）
│   ├── 05-priority-taxonomy.md         优先级定义 P0~P3
│   ├── 06-test-type-taxonomy.md        测试类型定义
│   └── 07-traceability-rules.md        追溯链路规约
├── subskills/
│   ├── qa-spec-engine/SKILL.md         需求解构 → Spec Model
│   ├── qa-case-engine/SKILL.md         Spec Model → 用例集（+ 场景推理/测试点提取）
│   ├── qa-estimate-engine/SKILL.md     Spec Model → 售前评估 / 报价
│   └── qa-audit-engine/SKILL.md        一致性核销 / 用例评审查漏 / 校准回填
├── scripts/
│   ├── validate_spec_model.py          Spec Model 结构机检
│   ├── count_cases.py                  ★ 模拟计数（售前用它预跑生成逻辑）
│   ├── check_consistency.py            ★ 跨阶段一致性核销
│   └── estimate.py                     用例数 → 人天/周期（读 assets/estimate-config.json）
└── assets/
    ├── spec-model.example.json
    ├── estimate-config.json            产能与周期参数
    └── pricing-config.json             计价参数
```

**所有权规则**：`references/` 与 `assets/` 由总控独占维护；`subskills/` 只读；`scripts/` 由总控调用。

---

## 3. 前置锁（开工前必须确认，缺一即停）

用户意图模糊时必须**主动问**，不允许猜。四道锁：

| 锁 | 取值 | 缺省 | 影响 |
| --- | --- | --- | --- |
| **① 交付形态锁** | 需求解构 / 用例集 / 售前评估 / 报价 / 核销（可多选） | 按用户话术判定 | 决定路由到哪些子技能 |
| **② 计量口径锁** | 聚合用例口径（**本套件唯一口径，不可选**） | 固定 | 见 `02-case-granularity-contract.md` |
| **③ 测试类型锁** | 功能 / 接口 / UI / 性能 / 安全 / 兼容 / 真机 | 功能 | 决定用例展开维度与计价单价 |
| **④ 输出格式锁** | Markdown / JSON / xlsx / CSV / 禅道导入 | 按用户话术 | 决定是否调用导出能力 |

> ② **不可选**：售前评估直接采用交付口径。理由——项目最终按生成的用例执行与验收，只有"交付口径"这一个数字是有兑现意义的；另立一套预估口径必然产生两个对不上的数。此锁不开放给单次任务覆盖。

**锁确认后的动作**：把四把锁的值**逐条列给用户确认**，再开工。禁止"边做边猜"。

---

## 4. 子技能路由表

总控**不自己干领域活**，按下表路由。读取子技能一律用**显式相对路径**（可移植性要求，见第 8 节）。

| 用户信号 | 路由到 | 读取路径 | 说明 |
| --- | --- | --- | --- |
| 给了一份需求文档 / PRD / 原型 / 接口文档，要"拆需求/提取功能点/建 Spec Model" | `qa-spec-engine` | `subskills/qa-spec-engine/SKILL.md` | **全链路第一步，必做** |
| 要"生成用例 / 写测试用例 / 导出 Excel / 导入禅道" | `qa-case-engine` | `subskills/qa-case-engine/SKILL.md` | 消费 Spec Model |
| 要"梳理业务场景 / 端到端流程 / 场景流程图" | `qa-case-engine`（场景子流程） | 同上 | 场景是 Spec Model 的一部分 |
| 要"提取测试点 / 功能测试点" | `qa-case-engine`（测试点子流程） | 同上 | 测试点也归 Spec Model |
| 要"售前评估 / 能不能做 / 大概多少用例 / 要多久 / 要几个人" | `qa-estimate-engine` | `subskills/qa-estimate-engine/SKILL.md` | **模拟计数**，不凭经验估数 |
| 要"报价 / 计费 / 按优先级计价 / 出计费 Excel" | `qa-estimate-engine`（计价子流程） | 同上 | 依赖真实用例统计 |
| 要"用例评审 / 查漏 / 对比需求 / 覆盖分析" | `qa-audit-engine` | `subskills/qa-audit-engine/SKILL.md` | 独立视角核销 |

**路由纪律**：
- 一次任务可能命中**多条**（如"评估一下并生成用例"）→ 先 `qa-spec-engine` 出 Spec Model，再**并行**投影。
- 用户只要评估却还没解构 → **先解构**。跳过解构直接估数被明令禁止：没有 Spec Model，就没有可核销的条数。
- 子技能**不自我调度**，永远由总控编排。

---

## 5. 强制读取清单（阶段 → 必读 → 硬产出）

**硬产出 = 不做出来就不算完成**。子技能启动前必须把"必读文件"真正读进上下文，并在产出开头写**激活回执头**（见 5.1）。

| 阶段 | 必读文件 | 硬产出 |
| --- | --- | --- |
| **S1 需求解构** | `00-authority-map.md`<br>`01-requirement-decomposition.md`<br>`03-spec-model-schema.md` | `spec-model.json`（含模块清单、功能点清单+复杂度定级、测试点清单、场景清单） |
| **S2 用例设计** | `02-case-granularity-contract.md`<br>`03-spec-model-schema.md`<br>`05-priority-taxonomy.md`<br>`06-test-type-taxonomy.md`<br>`07-traceability-rules.md` | 用例集（JSON / xlsx / CSV），每条含 `point` 追溯与 `note` 需求追溯 |
| **S3 售前评估** | `03-spec-model-schema.md`<br>`04-counting-and-conversion.md`<br>`05-priority-taxonomy.md` | 评估报告 md（可行性结论 / 模块级明细 / 三档区间 / 冒烟占比 / 周期人数） |
| **S4 报价** | `04-counting-and-conversion.md`<br>`assets/pricing-config.json` | 计费 Excel（统计 + 计价 + 成本） |
| **S5 核销** | `02-case-granularity-contract.md`<br>`04-counting-and-conversion.md`<br>`07-traceability-rules.md` | 核销报告 md（覆盖率 / 偏差 / 缺失清单 / 校准建议） |
| **S6 交付门禁** | 全部 `references/` | 三个脚本全 PASS（见第 7 节） |

### 5.1 激活回执头（强制）

任何子技能产出的**第一段**必须是回执头，证明"规则真的被读进去了"而不是挂名：

```markdown
<!-- 激活回执
skill: qa-case-engine
已读取: 02-case-granularity-contract.md / 03-spec-model-schema.md /
        05-priority-taxonomy.md / 06-test-type-taxonomy.md / 07-traceability-rules.md
计量口径: 聚合用例口径 v1（1 用例 = 1 个可独立执行的业务操作场景）
上游: spec-model.json（模块数 / 功能点数 / 测试点数）
本次承接: module=3.1,3.2
-->
```

缺回执头 → 总控认定该产出**无效**，要求重做。

---

## 6. 套装共享契约（子技能禁止另立）

以下 10 条**只在总控定义**。子技能若需要其中任何内容，**必须读取对应文件**，禁止自行编写"精简版""适配版"。

1. **计量单位唯一**：一条用例的定义 = `02-case-granularity-contract.md`。禁止子技能自行定义"什么算一条用例"。
2. **上游产物唯一**：全链路交接格式 = `03-spec-model-schema.md`。禁止自造中间格式。
3. **售前口径 = 交付口径**：评估条数与交付条数同量纲、同聚合规则，见 `04-counting-and-conversion.md`。
4. **优先级体系唯一**：P0~P3 定义 = `05-priority-taxonomy.md`。生成、统计、计价三方共用同一套。
5. **测试类型体系唯一**：`06-test-type-taxonomy.md`。生成、统计、计价三方共用。
6. **追溯链路唯一**：用例 → 测试点 → 功能点 → 需求，四段可双向回溯，见 `07-traceability-rules.md`。
7. **配置唯一**：所有数值参数只存在于 `assets/`。禁止在任何 SKILL.md 里硬编码参数值。

**执行约定（装到技能目录后必读）**：
- `$SKILL_DIR` = 本 `SKILL.md` 所在目录。下文所有 `scripts/`、`assets/`、`subskills/` 都相对它。
- 调用脚本一律给**绝对路径**（`python3 "$SKILL_DIR/scripts/xxx.py"`），**不要 `cd`**：用户的工作目录是他自己的项目，不是技能目录，`cd` 之后相对路径照样错。
- 待处理文件（`spec-model.json` 等）用其真实路径，不要假设它在技能目录里。
8. **禁止另立摘要层**：不允许任何子技能编写"规则概要/速查版"并把它放在比原文更靠前的位置。**唯一真相只有一份原文。**
9. **交付必过机检**：三个脚本全 PASS 才允许声称"已完成"。
10. **锁外不产出**：未在"交付形态锁"里勾选的产物，一律不生成（防止顺手扩大范围、污染口径）。

---

## 7. 机检门禁（交付前必须全 PASS）

```bash
# 1. Spec Model 结构与定级合法性
python3 "$SKILL_DIR/scripts/validate_spec_model.py" <spec-model.json>

# 2. 模拟计数（售前评估的条数必须由它算，不许手写）
python3 "$SKILL_DIR/scripts/count_cases.py" <spec-model.json> [--modules 3.1,3.2] [--json]

# 3. 跨阶段一致性核销（售前预估 vs 实际交付）
python3 "$SKILL_DIR/scripts/check_consistency.py" --estimate <评估报告或spec-model> --cases <用例集.json>

# 4. 换算周期（不在交付门禁内，评估/报价时用）
echo '{"total_cases": 340, "team_size": 4}' | python3 "$SKILL_DIR/scripts/estimate.py"
```

| 脚本 | FAIL 判据 | 处置 |
| --- | --- | --- |
| `validate_spec_model.py` | 有模块无功能点；功能点缺复杂度定级；测试点无归属；ID 重复；场景引用本模块不存在的测试点；存在全局孤儿测试点 | 回 S1 补 |
| `count_cases.py` | 输入非法；出现未定义复杂度档 | 回 S1 修 |
| `check_consistency.py` | 模块覆盖率 < 90%；存在用例指向不存在的测试点；预估/实际偏差 > 20% 无说明 | 回 S1/S2 修，或在报告中显式登记偏差原因 |

**门禁纪律**：脚本 FAIL 不等于"可以口头说明后放过"。必须在产出中**显式登记**：FAIL 项、原因、处置、残留风险。

---

## 8. 跨智能体适配（可移植性）

本套件刻意**不依赖任何平台的自动技能发现/自动路由**（manju-laoli 沿用技能名调度，换平台即失效）。适配方式：

| 平台 | 入口 | 机制 |
| --- | --- | --- |
| CodeBuddy | `SKILL.md`（本文件） | 项目 `.codebuddy/skills/qa-suite/` 或用户 `~/.codebuddy/skills/qa-suite/` |
| Codex / 通用 | `AGENTS.md` | 薄壳，内容仅一句"以 `SKILL.md` 为准" |
| Claude Code | `CLAUDE.md` | 同上 |
| Trae | `.trae/rules.md` | 同上 |

**移植三原则**：
1. **显式路径**：总控与子技能之间一律用 `subskills/<name>/SKILL.md` 这类相对路径引用，不使用"技能名调度"。
2. **零平台 API**：不使用任何平台专有工具名/JSON schema 作为流程前提；脚本只用标准库 Python 3。
3. **整体拷贝即用**：`qa-suite/` 目录拷到任何位置都能跑，无外部依赖。

### 8.1 安装到各平台

| 平台 | 安装方式 |
| --- | --- |
| CodeBuddy（项目级） | 把 `qa-suite/` 拷到 `<项目>/.codebuddy/skills/qa-suite/` |
| CodeBuddy（用户级） | 拷到 `~/.codebuddy/skills/qa-suite/` |
| Codex / 通用 agent | 把 `qa-suite/` 放进仓库，`AGENTS.md` 即入口 |
| Claude Code | 同上，`CLAUDE.md` 即入口 |
| Trae | 同上，`.trae/rules.md` 即入口 |

**关键点**：本套件**不依赖"每个子技能被独立注册为技能"**，所以无需为 4 个子技能单独安装——拷贝一个目录即完成安装。

### 8.2 快速自检

```bash
python3 "$SKILL_DIR/scripts/validate_spec_model.py" "$SKILL_DIR/assets/spec-model.example.json"   # 应 PASS
python3 "$SKILL_DIR/scripts/count_cases.py" "$SKILL_DIR/assets/spec-model.example.json"           # 应输出 7 条
echo '{"total_cases": 7, "team_size": 2}' | python3 "$SKILL_DIR/scripts/estimate.py"
```

---

## 9. 高发错误

| 错误 | 后果 | 正确做法 |
| --- | --- | --- |
| 跳过 Spec Model 直接评估用例数 | 条数无来源、不可核销 | 强制先 S1 |
| 用"功能点数 × 每功能点 N 条"估条数 | 把聚合度当常数，误差不可收敛 | 用 `count_cases.py` 模拟计数 |
| 售前用一套粒度、交付用另一套 | 报价与交付对不上账 | 统一走 `02-case-granularity-contract.md` |
| 在 SKILL.md 里硬编码参数值 | 多处维护、互相矛盾 | 参数只放 `assets/` |
| 子技能写"规则概要"放最前面 | 漂移后最容易害人 | 禁令 #8 |
| 一次任务顺手把范围外的东西也做了 | 口径污染、报价失真 | 禁令 #10，按锁产出 |
| 脚本 FAIL 后口头解释放过 | 质量失控 | 必须显式登记 FAIL 与残留风险 |

---

## 10. 执行总流程（默认路径）

```
0. 识别意图 → 列出四道锁的值给用户确认
1. 若无 Spec Model → 路由 qa-spec-engine（S1），产出 spec-model.json
2. 校验：python3 "$SKILL_DIR/scripts/validate_spec_model.py" spec-model.json   （必须 PASS）
3. 按锁并行投影：
     - 要评估/报价 → qa-estimate-engine（内部先跑 count_cases.py，再算周期与价格）
     - 要用例     → qa-case-engine（严格按粒度契约聚合）
     - 要核销     → qa-audit-engine
4. 门禁：python3 "$SKILL_DIR/scripts/check_consistency.py" --estimate ... --cases ...
5. 输出交付，附「激活回执头」与「机检结果」两段
```

**结束语规则**：交付时必须说明 (a) 读了哪些规则文件、(b) 三个脚本的 PASS/FAIL、(c) 若 FAIL，原因与残留风险。