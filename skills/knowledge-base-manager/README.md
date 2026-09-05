# Knowledge Base Manager

建立和维护业务知识库的工具，支持从 PRD 文档（docx/pdf/md/图片）、Swagger/OpenAPI、Postman 集合自动导入需求文档和接口文档，并基于知识库生成功能测试用例、接口自动化脚本和 UI 自动化脚本。

## 快速开始

### 安装

将 `knowledge-base-manager` 解压到项目目录：

```bash
mkdir -p .codebuddy/skills/
cd .codebuddy/skills/
unzip /path/to/knowledge-base-manager.zip
```

### 初始化知识库

```bash
# 基础初始化
python3 .codebuddy/skills/knowledge-base-manager/scripts/init_kb.py .

# 指定功能模块初始化（推荐）
python3 .codebuddy/skills/knowledge-base-manager/scripts/init_kb.py . \
  --module user-auth payment order
```

执行后会在项目目录创建 `knowledge-base/` 目录结构。

---

## 一、如何初始化知识库

### 方式1：全新初始化

```bash
python3 scripts/init_kb.py <项目根目录> --module <模块1> <模块2> ...
```

**示例**：

```bash
cd /path/to/your-project
python3 .codebuddy/skills/knowledge-base-manager/scripts/init_kb.py . \
  --module user-auth payment order admin
```

这会创建以下目录结构：

```
knowledge-base/
├── _index.md               # 全局索引
├── _glossary.md            # 业务术语表
├── _architecture.md        # 系统架构说明
├── _upgrade_log.md         # 变更日志
├── 01-requirements/
│   ├── _source/            # PRD 源文件存档
│   ├── user-auth/
│   │   └── _overview.md
│   ├── payment/
│   │   └── _overview.md
│   └── ...
├── 02-api-docs/
│   ├── _source/            # Swagger/Postman 源文件存档
│   └── ...
├── 03-defects/
├── 04-test-cases/
└── 05-automation-scripts/
```

### 方式2：从 PRD 文档导入

向 CodeBuddy 提交 PRD 文档，说 **"帮我导入这个 PRD 文档"**，CodeBuddy 会：

1. 将原始文件保存到 `01-requirements/_source/`
2. 解析文档内容（docx/pdf/md/图片 → 文本）
3. 提取功能模块、业务流程、业务规则、验收标准
4. 按模块拆分为多个 `REQ-*.md` 文件
5. 更新 `_glossary.md` 和 `_architecture.md`
6. 运行索引更新

### 方式3：从 Swagger/OpenAPI 导入

```bash
python3 scripts/import_swagger.py <项目根目录> <swagger文件路径>
```

**示例**：

```bash
cd /path/to/your-project
python3 .codebuddy/skills/knowledge-base-manager/scripts/import_swagger.py . \
  openapi_v3.json
```

CodeBuddy 会自动：
1. 保存源文件到 `02-api-docs/_source/`
2. 按 tags 分模块
3. 每个 API 生成独立的 `API-{module}_{name}.md` 文档
4. 构建错误码表和示例请求/响应
5. 生成 `_overview.md` 模块概述

### 方式4：从 Postman 集合导入

向 CodeBuddy 提交 Postman 集合 JSON 文件，说 **"帮我导入这个 Postman 集合"**，CodeBuddy 会：

1. 保存源文件到 `02-api-docs/_source/`
2. 按文件夹结构分模块
3. 每个请求生成独立的 API 文档
4. 提取请求参数、响应示例

---

## 二、如何新增知识

### 新增需求文档（手动）

向 CodeBuddy 描述需求，说 **"帮我添加登录功能的需求文档"**，CodeBuddy 会按标准模板创建：

```markdown
---
id: REQ-001
title: 用户登录功能
module: user-auth
version: 1.0
status: draft
priority: P0
created: 2026-06-16
tags: [登录, 认证]
related_apis: []
related_bugs: []
---
# 用户登录功能
## 1. 业务概述
## 2. 前置条件
## 3. 业务流程
## 4. 业务规则
## 5. 输入/输出规格
## 6. 验收标准
## 7. 变更历史
```

### 新增接口文档（手动）

向 CodeBuddy 描述接口，说 **"帮我添加登录接口的文档"**，CodeBuddy 会按标准模板创建。

### 新增历史缺陷记录

说 **"记录一个缺陷：登录会话过期后页面未跳转"**，CodeBuddy 会按缺陷模板记录：

```markdown
---
id: BUG-001
title: 登录会话超时后未正确跳转
module: user-auth
severity: major
status: open
created: 2026-06-16
root_cause: 前端未检测 token 过期状态码
related_requirements: [REQ-001]
---
# BUG-001: 登录会话超时后未正确跳转
## 复现步骤
## 预期结果
## 实际结果
## 根本原因分析
## 修复方案
```

### 补充业务术语

说 **"添加业务术语：Token 是用户认证后颁发的 JWT 令牌"**，CodeBuddy 会更新 `_glossary.md`。

---

## 三、如何更新知识

### 更新需求文档

直接告诉 CodeBuddy 要修改的内容，如 **"更新 REQ-001，增加一条业务规则：密码输错5次锁定30分钟"**。

CodeBuddy 会自动：
1. 读取原文档
2. 新增业务规则到 RULE 表
3. 升级 `version` 字段
4. 更新 `updated` 日期
5. 在变更历史中记录

### 更新接口文档

**"更新 API-auth_login，增加一个 429 限流错误码"**，CodeBuddy 会更新错误码表。

### 更新缺陷状态

**"BUG-001 已修复，修改状态为 verified"**，CodeBuddy 会更新 `status` 字段并记录关闭日期。

### 重新导入（版本升级）

当有新的 PRD 版本或 Swagger 版本时：
- CodeBuddy 会检测到已存在的文档
- 更新 `version` 字段（如 v1.0 → v2.0）
- 保留 `id` 不变
- 在变更历史中记录版本变化

### 重建索引

```bash
python3 scripts/update_index.py <项目根目录>
```

**示例**：

```bash
cd /path/to/your-project
python3 .codebuddy/skills/knowledge-base-manager/scripts/update_index.py .
```

索引更新包括：
- `_index.md`：全局模块统计和最近更新
- `01-requirements/{module}/_module-index.md`：需求索引
- `02-api-docs/{module}/_module-index.md`：接口索引
- `03-defects/{module}/_module-index.md`：缺陷索引
- `03-defects/_stats.md`：缺陷统计分析

---

## 四、常见问题

### Q: 知识库目录应该放在哪里？
A: 在项目根目录下创建 `knowledge-base/`，即与 `.codebuddy/` 同级。

### Q: 文档的 ID 如何命名？
A: `REQ-001`（需求，三位数字递增）、`BUG-001`（缺陷，三位数字递增）、`API-{模块}_{功能}`（接口，语义化命名）。

### Q: 如何处理废弃的文档？
A: 将 `status` 改为 `deprecated`，定期脚本迁移到 `_archived/` 目录，不直接删除文件。

### Q: 如何确保大模型能理解我的业务？
A: 关键在于：
1. 认真填写 `_glossary.md` 的业务术语定义
2. 需求文档的 `related_apis` 和 `related_bugs` 关联字段要完整
3. 缺陷记录务必填写 `root_cause`（根本原因）
4. 每次变更后更新索引

### Q: 支持哪些下游生成？
A: 基于知识库可以生成：
- 功能测试用例（正向/逆向/边界/业务规则/缺陷回归）
- 接口自动化脚本（pytest + requests，数据驱动）
- UI 自动化脚本（Playwright TypeScript）

---

## 五、其他 Skill 如何使用此知识库

知识库对其他 Skill 开放标准化的数据接口。任何 Skill（如功能测试用例生成、接口自动化、UI 自动化等）都可以直接读取和使用。

### 集成方式

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| 直接读文件 | 按目录路径读取 Markdown 文件，解析 frontmatter | 手动编写其他 Skill 的 SKILL.md |
| 程序化查询 | 使用 `KnowledgeBase` 查询类 | 自动化脚本、批量处理 |
| 索引定位 | 读取 `_module-index.md` 快速找到目标文档 | 快速浏览、定位 |

### 目录结构契约

任何 Skill 都可以信赖以下固定结构：

```
knowledge-base/
├── _index.md                  # 全局索引 + 模块数量统计
├── 01-requirements/
│   ├── _module-index.md       # 需求清单（ID/标题/版本/关联关系）
│   └── {module}/REQ-*.md      # 每个需求一个文件
├── 02-api-docs/
│   ├── _module-index.md       # 接口清单（ID/方法/路径/关联关系）
│   └── {module}/API-*.md      # 每个接口一个文件
├── 03-defects/
│   ├── _module-index.md       # 缺陷清单（ID/标题/严重程度/关联关系）
│   └── {module}/BUG-*.md      # 每个缺陷一个文件
└── 04-test-cases/             # 【输出目录】
└── 05-automation-scripts/     # 【输出目录】
```

### 文档关联遍历方式

所有文档通过 frontmatter 中的关联字段连接：

```
需求(REQ-001) ──related_apis──→ [API-auth_login, API-auth_refresh]
需求(REQ-001) ──related_bugs──→ [BUG-001]
接口(API-auth_login) ──related_requirements──→ [REQ-001]
缺陷(BUG-001) ──related_requirements──→ [REQ-001]
缺陷(BUG-001) ──related_apis──→ [API-auth_login]
```

### 示例：功能测试用例 Skill 的集成流程

```
1. 读取 _index.md → 了解模块概览
2. 定位目标模块 user-auth → 读取 _module-index.md 获取需求清单
3. 读取 REQ-001.md → 获取业务流程、业务规则、验收标准
4. 从 REQ-001 的 related_apis → 读取 API-auth_login.md → 获取错误码
5. 从 REQ-001 的 related_bugs → 读取 BUG-001.md → 了解历史缺陷
6. 综合信息生成测试用例，输出到 04-test-cases/functional/
```

### 示例：接口自动化 Skill 的集成流程

```
1. 读取 02-api-docs/{module}/_module-index.md → 获取接口清单
2. 读取 API-auth_login.md → 提取 method/path/参数/错误码/响应结构
3. 按请求参数字段表生成参数化测试数据
4. 按错误码表生成异常场景
5. 按业务逻辑说明补充场景
6. 输出到 05-automation-scripts/api/
```

### 在其他 Skill 的 SKILL.md 中声明依赖

```yaml
---
name: my-testcase-skill
description: 根据 {project_root}/knowledge-base/ 中的业务知识生成测试用例。
  依赖 knowledge-base-manager 维护的知识库目录结构和文档关联关系。
---
```

详细集成规范见 `references/kb_api.md`，其中还提供了完整的 `KnowledgeBase` 查询类代码。

---

## 六、查看完整文档

| 文件 | 说明 |
|------|------|
| `references/kb_structure.md` | 知识库目录结构详细定义 |
| `references/doc_templates.md` | 各类型文档模板和字段规范 |
| `references/workflows.md` | 各工作流程详细示例 |
| `references/prd_import_guide.md` | PRD 文档导入解析指南 |
| `references/kb_api.md` | 知识库对外接口规范（其他 Skill 集成指南） |
