---
name: qa-case-engine
description: "【qa-suite 套装内部技能 · 通常无需直接调用，直接说需求给总控 qa-suite 即可】用例设计引擎：消费 Spec Model，按统一用例粒度契约把场景落地为可执行测试用例集，支持导出 Excel/CSV 供禅道、TestRail、飞书多维表格导入；并含业务场景推理（端到端/备选流/异常流 + Mermaid 流程图）、测试点提取两个子流程。触发场景：生成测试用例、写用例、导出用例表格、导入禅道、梳理业务场景、提取测试点。"
---

# 用例设计引擎（qa-case-engine）

<!-- 激活回执（必须填写并放在产出最前）
skill: qa-case-engine
已读取: references/02-case-granularity-contract.md / 03-spec-model-schema.md /
        05-priority-taxonomy.md / 06-test-type-taxonomy.md / 07-traceability-rules.md
计量口径: 聚合用例口径 v1（1 用例 = 1 个可独立执行的业务操作场景）
上游: spec-model.json（模块 N / 功能点 N / 测试点 N / 场景 N）
本次承接: module=...
-->

## 0. 定位

| 项 | 内容 |
| --- | --- |
| **输入** | `spec-model.json`（**唯一输入，禁止绕过它直接读需求文档写用例**） |
| **输出** | 用例集（JSON + 可选 xlsx / CSV） |
| **不做** | 不修改 Spec Model（只读）；不算条数（条数由 Spec Model 场景数决定） |

**唯一计量单位**：`一条用例 = 一个可独立执行的业务操作场景`（`../../references/02-case-granularity-contract.md`）。
**Spec Model 的每个 `scenario` 恰好落地为一条用例**，不多不少。这是"售前 = 交付"的机制保证。

## 1. 必读

```
../../SKILL.md
../../references/02-case-granularity-contract.md   ★★ 计量单位（违反即产出无效）
../../references/03-spec-model-schema.md
../../references/05-priority-taxonomy.md
../../references/06-test-type-taxonomy.md
../../references/07-traceability-rules.md          ★ 追溯字段必填
```

## 2. 主流程：场景 → 用例

### Step 1 · 读取并核对上游

- 读 `spec-model.json`，确认 `meta.granularity_contract` 已声明。
- 统计：模块数 / 功能点数 / 测试点数 / 场景数。**场景数 = 本次要产出的用例数**。
- 若 Spec Model 缺失或机检未过 → **停止**，退回 `qa-spec-engine`（不允许自行补数）。

### Step 2 · 逐场景写用例

每个场景输出一条用例，字段规范：

| 字段 | 要求 |
| --- | --- |
| `id` | `TC-<模块短码>-<序号>` |
| `module` | 必须与 Spec Model 的模块名一致 |
| `point` | 该场景的 `point_ids` 原样填入（逗号分隔）。**必填** |
| `title` | `【<测试点类 group>】<测试目的>`。测试目的写**业务动作**，不写操作过程 |
| `priority` | 取场景的 `priority`（不得自行改档） |
| `test_type` | 按 `06` 第 2 节映射（承载多类型时取主导并写入 `note`） |
| `precondition` | **必填且具体**：环境、账号/角色与权限、数据状态、依赖服务。禁止"无/正常环境" |
| `steps` / `expected` | **严格一一对应**（第 N 步 ↔ 第 N 条预期），用 `\n` 分隔 |
| `note` | **必填**，含需求追溯（如 `对应需求 REQ-X`）+ 主导类型判定依据 |

### Step 3 · 校验聚合比

- 本模块 `测试点数 ÷ 用例数` 必须落在 **[1.5, 4.0]**。
- **< 1.5** → 你把校验维度单独成条了。合并回所属场景（见契约 1.2 节禁止清单）。
- **> 4.0** → 一条用例塞了多个业务意图。回 `qa-spec-engine` 拆场景。

### Step 4 · 机检

```bash
python3 "$SKILL_DIR/scripts/check_consistency.py" --estimate <spec-model.json> --cases <用例集.json>
```
必须 PASS（覆盖率 100%、无孤儿测试点、无孤儿用例）。

## 3. 严格禁止（违反即产出无效）

1. 为**单个字段必填校验**单独建用例 → 应是所属用例的一个步骤。
2. 为**单个边界值**（上界/下界/越界各一条）单独建用例 → 合并为并列步骤。
3. 为**单个错误提示文案**单独建用例 → 作为预期片段。
4. 为**纯 UI 样式**单独建用例（无业务语义）→ 不立条。
5. 自行增删场景（场景数由 Spec Model 决定）。
6. 自行改优先级档位。
7. `point` 或 `note` 留空。

## 4. 导出（xlsx / CSV）

结构化数据写入 `test-cases.json` 后：

```bash
python3 "$SKILL_DIR/subskills/qa-case-engine/scripts/generate_xlsx.py" test-cases.json <output.xlsx>
# 若提示缺 openpyxl： python3 -m pip install openpyxl
```

标准列（与公司用例模板一致）：

```
用例编号 | 所属模块 | 对应测试点 | 测试标题 | 优先级 | 测试类型 | 前置条件 | 测试步骤 | 预期结果 | 备注
```

- 生成 xlsx 时含「测试用例」与「测试点清单」两个工作表，表头冻结 + 自动筛选 + 优先级配色。
- CSV 导出：表头同上，逗号分隔、引号转义，UTF-8 with BOM。
- **不输出「测试数据」列**：输入值写入步骤文本，且**只表意不写死**（写"合法用户名""超长用户名"，不写 `testuser01`；仅边界必须精确时才写长度）。

## 5. 子流程 1 · 业务场景推理（可选，用户要"梳理场景/流程图"时）

以业务对象生命周期为主线，跨模块串联出场景清单：

1. **模块图构建**：从 Spec Model 取模块与业务对象。
2. **状态机建模**：每个核心业务对象（订单/任务/审批单…）建状态集合与合法/非法转移。
3. **场景发现四抓手**：状态机驱动 / 动词驱动 / 角色驱动 / 数据流追踪。
4. **分类输出**：基本流（端到端主场景）/ 备选流（场景变体）/ 异常流（异常场景）。
5. **输出**：场景清单 Markdown（含场景编号）+ **Mermaid 流程图**。

- 场景编号必须与 Spec Model 的 `scenarios[].id` 对应，不允许另起一套编号。
- 端到端 L0 主场景标记为 **P0**（作为冒烟来源，见 `05` R1）。

## 6. 子流程 2 · 测试点提取（可选，用户只要"测试点"时）

- 直接输出 Spec Model 的 `test_points[]`（按模块分组）。
- 表格列：`测试点编号 | 所属模块 | 测试点类(group) | 类别(正向/边界/异常/状态/权限) | 描述`。
- **测试点是测试点，不是用例**，不要混用条数口径。

## 7. 高发错误

| 错误 | 后果 | 正确做法 |
| --- | --- | --- |
| 绕过 Spec Model 直接读需求写用例 | 与售前口径脱节，偏差复现 | 必须消费 Spec Model |
| 把校验维度拆成独立用例 | 条数虚高、聚合比 < 1.5 | 合并为步骤 |
| 自行增删场景 | 破坏"售前=交付" | 只按场景落地 |
| `precondition` 写"无" | 不可复现 | 写清环境/角色/数据 |
| 步骤与预期不对应 | 用例不可执行 | 序号严格配对 |
| `note` 缺需求追溯 | 追溯断裂、核销 FAIL | 必填 |
| 优先级自行调整 | 与统计/报价不一致 | 取场景的 priority |
| 跳过机检 | 下游返工 | Step 4 必做 |

## 8. 交付格式

1. **激活回执头**
2. 用例集（JSON，可选 xlsx / CSV）
3. **模块覆盖概览**：模块 / 场景数 / 用例数 / 承载测试点数 / 聚合比
4. **机检结果**（原文输出）
5. 若存在无法落地的场景，逐条说明原因（不允许静默丢弃）