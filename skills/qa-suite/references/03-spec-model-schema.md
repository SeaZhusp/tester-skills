# 03 · Spec Model 数据模型（全链路唯一交接格式）

> **Spec Model = 需求解构的唯一产物，也是所有下游产物的唯一输入。**
> 不允许任何子技能自造中间格式。任何跨阶段交接都必须走本结构。

---

## 1. 数据流位置

```
需求文档 ──[qa-spec-engine]──► spec-model.json ──┬──[qa-estimate-engine]──► 评估报告 / 报价
                                                  ├──[qa-case-engine]─────► 用例集 (json/xlsx/csv)
                                                  └──[qa-audit-engine]────► 核销报告
```

---

## 2. 完整结构

```json
{
  "meta": {
    "title": "示例项目 测试需求解构",
    "source": "示例需求文档v1.0.pdf",
    "source_version": "v1.0",
    "granularity_contract": "02-case-granularity-contract.md@v1",
    "generated_at": "2026-10-20",
    "confidence": "medium",
    "total_modules": 8,
    "total_feature_points": 32,
    "total_test_points": 0,
    "total_scenarios": 0
  },

  "modules": [
    {
      "id": "M-3.1",
      "name": "画布编排（示例模块）",
      "chapter": "3.1",
      "short_code": "CV",
      "has_ui": true,
      "has_api": true,
      "has_state": true,
      "has_permission": true,
      "status": "estimated",
      "feature_points": [
        {
          "id": "FP-CV-003",
          "name": "画布节点编辑",
          "complexity": "medium",
          "complexity_reason": "可编辑字段 4 个（名称/类型/坐标/属性）",
          "verbs": ["编辑"],
          "objects": ["画布节点"]
        }
      ],
      "test_points": [
        {
          "id": "TP-CV-001",
          "group": "页面进入与基础展示",
          "desc": "从看板管理创建看板成功后跳转看板页面",
          "category": "正向",
          "feature_point_id": "FP-CV-001"
        }
      ],
      "scenarios": [
        {
          "id": "SC-CV-001",
          "title": "从看板管理创建成功后跳转并正确渲染看板",
          "handles": "入口",
          "point_ids": ["TP-CV-001", "TP-CV-002"],
          "priority": "P1"
        }
      ],
      "case_count": 12,
      "estimated_cases": 12
    }
  ],

  "dedup_log": [
    {
      "removed_from": "M-4.5 应用管理",
      "kept_in": "M-4.3.2 角色权限管理",
      "object": "应用冻结状态的角色可见性",
      "reason": "已在角色权限模块集中覆盖，业务模块仅引用"
    }
  ],

  "assumptions": [
    "接口文档以 Gitee 官方文档为准，字段命名与必传项以官方为准",
    "无性能专项测试需求"
  ],

  "gaps": [
    {
      "module": "M-4.4.8",
      "name": "编辑脚本",
      "issue": "章节正文缺失，仅有标题",
      "impact": "范围不确定，按 2 个中等功能点占位",
      "placeholder_cases": 16,
      "included_in_baseline": false
    }
  ],

  "non_functional": [
    {
      "id": "NF-01",
      "name": "数据备份与恢复验证",
      "category": "安全",
      "cases_hint": 4
    }
  ]
}
```

---

## 3. 字段约束

### 3.1 `meta`（必填）

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| `title` | string | 必填 |
| `source` | string | 必填，原始文档名（含文件名与版本） |
| `source_version` | string | 必填 |
| `granularity_contract` | string | **必填**，必须声明所遵循的粒度契约版本，如 `02-case-granularity-contract.md@v1` |
| `generated_at` | string | 必填，`YYYY-MM-DD` |
| `confidence` | enum | `high` / `medium` / `low` |
| `total_*` | int | 必填，汇总值必须与本文件实际计数一致（脚本核对） |

### 3.2 `modules[]`（必填，非空）

| 字段 | 约束 |
| --- | --- |
| `id` | 必填，唯一，`M-<章节号>` |
| `name` | 必填 |
| `chapter` | 必填 |
| `short_code` | 必填，用于测试点编号前缀，2~6 位大写字母 |
| `status` | `estimated`（正常解构）/ `placeholder`（文档缺口占位） |
| `feature_points[]` | **非空**（`validate_spec_model.py` 会 FAIL 空功能点的模块） |
| `test_points[]` | 非空 |
| `scenarios[]` | 非空；`point_ids` 必须能在本模块 `test_points` 中找到 |
| `case_count` | 必填，= `scenarios.length`，由 `count_cases.py` 核对 |

### 3.3 `feature_points[]`

| 字段 | 约束 |
| --- | --- |
| `id` | `FP-<短码>-<序号>`，全局唯一 |
| `name` | 必填，业务能力名（动宾结构） |
| `complexity` | 必填，**合法值只有 `simple` / `medium` / `complex`**（判据见 `01-requirement-decomposition.md` 第 3.2 节，多条命中取最高档） |
| `complexity_reason` | **必填**，写明触发该档的判据（否则定级不可复核） |
| `verbs` / `objects` | 必填，供场景枚举（抓手 B）使用 |

### 3.4 `test_points[]`

| 字段 | 约束 |
| --- | --- |
| `id` | `TP-<短码>-<序号>`，全局唯一 |
| `category` | 必填，`正向` / `边界` / `异常` / `状态` / `权限` |
| `feature_point_id` | 必填，必须指向存在的功能点 |
| `group` | 必填，测试点类（用于用例标题前缀） |

### 3.5 `scenarios[]`

| 字段 | 约束 |
| --- | --- |
| `id` | `SC-<短码>-<序号>`，全局唯一 |
| `handles` | 必填，来源抓手：`入口` / `动词` / `状态` / `角色` |
| `point_ids` | 必填，非空数组；**每条测试点必须至少被一个场景引用**（覆盖率 100%） |
| `priority` | 必填，P0~P3，依据 `05-priority-taxonomy.md` 推导（非拍比例） |

### 3.6 `gaps[]`（文档缺口）

| 字段 | 约束 |
| --- | --- |
| `placeholder_cases` | 必填，占位估计条数 |
| `included_in_baseline` | 必填，`true` 才计入基准；文档缺口默认 `false`（单列为"待澄清"） |

---

## 4. 校验规则（`validate_spec_model.py` 会机检）

| 编号 | 规则 | 违反后果 |
| --- | --- | --- |
| V1 | `meta` 必填字段齐全，`granularity_contract` 已声明 | FAIL |
| V2 | 每个模块 `feature_points` 非空 | FAIL |
| V3 | 每个功能点有 `complexity` 且取值合法、有 `complexity_reason` | FAIL |
| V4 | 所有 ID 全局唯一（模块/功能点/测试点/场景） | FAIL |
| V5 | 每个测试点的 `feature_point_id` 可解析 | FAIL |
| V6 | 每个场景的 `point_ids` 可解析且非空 | FAIL |
| V7 | **测试点覆盖率 = 100%**（无孤儿测试点） | FAIL |
| V8 | `case_count` == `scenarios.length` == `count_cases.py` 输出 | FAIL |
| V9 | `meta.total_*` 与实际计数一致 | WARN |
| V10 | 聚合比 `测试点/场景` 落在 [1.5, 4.0] | WARN（超区间告警） |

---

## 5. 使用纪律

1. **只读原则**：`qa-case-engine` / `qa-estimate-engine` 读取 Spec Model，**不得修改**。发现错误应退回 `qa-spec-engine` 修正后重跑。
2. **单文件交付**：Spec Model 是一个 JSON 文件，随任务一起交付，作为**可追溯证据**。
3. **版本声明**：`meta.granularity_contract` 必须声明，否则下游无法判断用的是哪一版粒度规则。
4. **禁止内联大文本**：Spec Model 只存结构与索引，不内联需求原文；需要原文时用 `source + chapter` 定位。