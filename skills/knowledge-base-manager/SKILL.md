---
name: knowledge-base-manager
description: 建立和维护业务知识库的 Skill，适用于需要让大模型理解自身业务以辅助测试的团队。知识库包含需求文档、接口文档、历史缺陷库等结构化内容。支持从多种输入源导入：PRD 文档（docx/pdf/md/图片）、Swagger/OpenAPI 规格、Postman 集合。触发场景包括：建立/初始化知识库、从 PRD 文档导入需求、从 Swagger/Postman 导入接口、添加/更新需求文档、添加/更新接口文档、添加缺陷记录、查询业务知识、根据知识库生成功能测试用例、生成接口自动化脚本、生成UI自动化脚本、更新索引、维护知识库结构。
---

# Knowledge Base Manager

## Overview

本 Skill 帮助团队建立和维护结构化的业务知识库，使大模型能够准确理解业务逻辑、接口规则和历史缺陷模式。知识库采用标准化的目录结构和文档模板，支持：

- **PRD 文档导入**：从 docx/pdf/md/图片 格式的 PRD 文档中自动提取需求、业务流程、业务规则等，结构化写入知识库
- **接口文档导入**：从 Swagger/OpenAPI (JSON/YAML) 和 Postman 集合中解析接口定义，结构化写入知识库
- **需求文档管理**：按模块组织业务需求，含前置条件、业务流程、业务规则、验收标准
- **接口文档管理**：标准化的 API 定义，含请求/响应结构、参数说明、错误码
- **历史缺陷库**：结构化的缺陷记录，关联需求和接口，便于分析和预防
- **知识库索引**：自动维护全局索引、模块索引、业务术语表
- **下游生成能力**：基于知识库生成功能测试用例、接口自动化脚本、UI 自动化脚本

## 核心目录

知识库根目录为 `{project_root}/knowledge-base/`，详细结构见 `references/kb_structure.md`。

## 文档模板规范

每种文档类型有标准化的 YAML frontmatter + Markdown body 结构，详见 `references/doc_templates.md`。

## 核心能力与工作流程

### 1. 初始化知识库

当用户说"帮我建立/初始化知识库"时：

1. 询问用户项目的名称、业务领域、主要功能模块
2. 询问用户是否有现有文档需要导入（PRD docx/pdf、Swagger、Postman 等）
3. 调用 `scripts/init_kb.py` 初始化目录结构（含 `_source/` 源文件目录）
4. 生成 `_index.md`、`_glossary.md`、`_architecture.md` 等基础文件
5. 如果有现有文档，按对应工作流程导入

### 2. 从 PRD 文档导入需求（新）

当用户提供 PRD 文档（.docx / .pdf / .md / 图片）时，**必须先阅读 `references/prd_import_guide.md` 中的核心原则**并严格遵守：

> **原则0**：业务逻辑是核心焦点 — 优先确保业务流程和业务规则的完整准确
> **原则1**：只写文档中有的，绝不编造
> **原则2**：信息不足时反问用户
> **原则3**：一次只入库一个模块

> 详细解析指南见 `references/prd_import_guide.md`

1. **保存源文件**：将原始文件复制到 `01-requirements/_source/` 目录，保留原始格式
2. **读取内容**：根据文件格式采用不同方式读取：
   - **.docx**：使用 `docx` skill 或 `python-docx` 读取
   - **.pdf**：使用 `pdf` skill 或 `PyMuPDF/pdfplumber` 读取
   - **.md**：直接读取 Markdown 内容
   - **图片（png/jpg等）**：使用大模型的视觉能力识别图中的文字内容
3. **识别模块**：通读 PRD，列出涉及的所有功能模块，**反问用户先处理哪一个**
4. **逐模块解析**：用户选定模块后，从 PRD 中只提取该模块的内容，**以业务逻辑为核心**：
   - **业务流程**（优先！有则提取，不完整则追问）→ 业务流程 section
   - **业务规则**（优先！每条规则的约束值必须明确）→ 业务规则表（RULE）
   - **前置条件**（功能可用需要的前提）→ 前置条件
   - 业务概述和背景（有则写，没有不写）
   - 验收标准（有则写，没有不写）
   - **输入/输出规格等可选章节**只在 PRD 有明确定义时才填写
   - **信息不足时反问**：规则值不明确、流程不完整等情况主动问用户
5. **生成结构化需求文档**：
   - 遵循 `references/doc_templates.md` 中的需求模板
   - 只写 PRD 中实际存在的章节，不存在的章节删除或留空
   - 提取业务术语更新 `_glossary.md`
   - 提取架构信息更新 `_architecture.md`
6. **逐项用户确认**：展示名称、描述、规则、验收标准，让用户逐项确认
7. **写入知识库**：确认后写入对应目录，调用 `scripts/update_index.py` 更新索引
8. **询问继续**：如果还有其他模块未处理，问用户是否继续处理下一个模块
9. **更新变更日志**：在 `_upgrade_log.md` 记录导入操作

### 3. 从 Swagger/OpenAPI 导入接口（新）

当用户提供 Swagger 2.0 / OpenAPI 3.x JSON/YAML 文件时：

> 详细解析指南见 `references/api_import_guide.md`

1. **保存源文件**：将原始文件复制到 `02-api-docs/_source/` 目录
2. **解析 API 定义**：
   - 读取所有 paths（路径+HTTP方法）
   - 解析每个 API 的 parameters、requestBody、responses
   - 提取 schema 定义（components/schemas 或 definitions）
   - 提取 tags 用于模块划分
   - 提取 servers/basePath 用于基础 URL
3. **按 tags 或自定义规则分模块**：
   - 以 Swagger tags 作为模块名（或让用户指定）
   - 为每个模块创建目录和 `_overview.md`
4. **生成结构化接口文档**：每个 API 生成单独的 `API-{module}_{name}.md`，遵循 `doc_templates.md`
5. **用户确认**：确认模块划分和是否关联已有需求
6. **写入知识库**，调用索引更新

### 4. 从 Postman 集合导入接口（新）

当用户提供 Postman 集合 JSON 文件时：

> 详细解析指南见 `references/api_import_guide.md`

1. **保存源文件**：将原始文件复制到 `02-api-docs/_source/` 目录
2. **解析 Postman 集合**：
   - 遍历 item 层级结构，提取每个 request
   - 解析 method、url、headers、body
   - 提取 auth 配置
   - 按 folder 结构映射到模块
3. **生成结构化接口文档**：每个 request 生成单独 `API-{module}_{name}.md`
4. **用户确认**后写入知识库，更新索引

### 5. 添加需求文档（手动）

当用户需要手动添加或更新需求时：

1. 读取 `references/doc_templates.md` 中的需求文档模板
2. 按模板格式整理用户提供的信息
3. 写入 `knowledge-base/01-requirements/{module}/REQ-{id}_{short_name}.md`
4. 如果需求涉及已有功能，建议同时读取已有知识和历史缺陷进行关联
5. 调用 `scripts/update_index.py` 更新索引

**ID 命名规则**：`REQ-三位数字序号`，如 `REQ-001`

### 6. 添加接口文档（手动）

当用户需要手动添加或更新接口文档时：

1. 读取 `references/doc_templates.md` 中的接口文档模板
2. 按模板格式整理接口信息（请求方法、路径、参数、响应等）
3. 写入 `knowledge-base/02-api-docs/{module}/API-{short_name}.md`
4. 自动关联到对应的需求文档（如有）
5. 调用 `scripts/update_index.py` 更新索引

**ID 命名规则**：`API-{模块}-{功能}`，如 `API-auth_login`

### 7. 添加缺陷记录

当用户需要记录缺陷时：

1. 读取 `references/doc_templates.md` 中的缺陷文档模板
2. 按模板记录缺陷信息（环境、步骤、预期/实际结果等）
3. 写入 `knowledge-base/03-defects/{module}/BUG-{id}_{short_name}.md`
4. 自动关联到对应的需求和接口文档
5. 调用 `scripts/update_index.py` 更新索引

**ID 命名规则**：`BUG-三位数字序号`，如 `BUG-001`

### 8. 查询/理解业务

当用户询问业务逻辑时：

1. 先读取 `knowledge-base/_glossary.md` 了解业务术语
2. 读取 `knowledge-base/_architecture.md` 了解系统架构
3. 根据用户问题，读取 `_index.md` 找到相关模块的文档
4. 读取相关需求、接口、缺陷文档，综合理解后回答

### 9. 生成功能测试用例

当用户要求"根据知识库生成功能测试用例"时：

1. 明确用户要测试的模块或功能
2. 读取对应模块的需求文档和 `_overview.md`
3. 读取 `03-defects/` 中关联的历史缺陷，关注高风险区域
4. 按照以下维度生成测试用例（输出到 `04-test-cases/functional/`）：
   - **正向用例**：覆盖正常业务流程
   - **逆向用例**：覆盖异常输入和操作
   - **边界用例**：覆盖边界值场景
   - **业务规则用例**：覆盖所有业务规则分支
   - **历史缺陷回归用例**：针对关联的历史缺陷
5. 每个用例使用标准格式：标题、前置条件、测试步骤、预期结果、优先级

### 10. 生成接口自动化脚本

当用户要求"生成接口自动化脚本"时：

1. 读取 `02-api-docs/` 中对应的接口文档
2. 基于接口定义生成接口自动化代码
3. 输出到 `05-automation-scripts/api/`

**脚本要求**：
- 支持数据驱动（从外部文件读取测试数据）
- 包含参数校验、响应校验
- 包含错误码场景
- 支持环境配置切换

### 11. 生成 UI 自动化脚本

当用户要求"生成 UI 自动化脚本"时：

1. 读取 `01-requirements/` 中对应的需求文档
2. 读取 `02-api-docs/` 中关联的接口文档（用于模拟数据）
3. 基于业务流程生成 UI 自动化脚本
4. 输出到 `05-automation-scripts/ui/`

## 维护规则

### 新增文档
- 严格按照 `references/doc_templates.md` 中的模板添加
- 确保填写完整的 frontmatter 元数据
- 确保填写 `related_apis`、`related_bugs`、`related_requirements` 等关联字段
- **从 PRD/Swagger/Postman 导入的文档**：自动填写 `source` / `source_type` 字段，指向 `_source/` 中的原始文件
- 添加后执行索引更新

### 更新文档
- 更新 `version` 字段
- 更新 `updated` 日期
- 在文档变更日志中记录变更内容
- 如果有新的源文件版本，更新 `source` 字段并重新导入
- 更新后执行索引更新

### 删除文档
- 不要直接删除文件，将 `status` 改为 `deprecated`
- 定期归档到对应目录的 `_archived/` 子目录下

### 源文件管理（`_source/`）
- `01-requirements/_source/` 和 `02-api-docs/_source/` 存放原始导入文件
- 命名规范：`{版本号}_{描述}.{ext}`，如 `v1.2_用户认证PRD.docx`
- 源文件保留原始格式，作为可追溯的参考
- 源文件不参与索引生成，仅作为文档溯源依据

### 索引维护
- 每次新增/更新/废弃文档后，调用 `scripts/update_index.py` 重建索引
- 索引文件包括：
  - `_index.md`：全局索引，按模块列出所有文档及其关联
  - `01-requirements/_module-index.md`：需求模块索引
  - `02-api-docs/_module-index.md`：接口模块索引
  - `03-defects/_module-index.md`：缺陷模块索引

## 其他 Skill 如何集成本知识库

知识库对其他 Skill 开放标准化的数据接口。任何 Skill（如功能测试用例生成、接口自动化、UI 自动化等）都可以通过以下方式使用知识库。

### 集成方式

1. **直接读取文件**：知识库是标准 Markdown 文件，任何 Skill 可直接按目录结构读取
2. **使用查询接口**：调用 `scripts/query_kb.py` 中的 `KnowledgeBase` 类进行程序化查询
3. **通过索引文件定位**：读取 `_module-index.md` 快速找到目标文档

### 该知识库对外提供的契约

- **目录结构**：固定不变的分区（01/02/03...），详见 `references/kb_structure.md`
- **frontmatter 字段**：所有文档的元数据字段格式一致，详见 `references/doc_templates.md`
- **关联关系**：通过 `related_requirements`、`related_apis`、`related_bugs` 字段建立文档间的联系
- **查询能力**：`KnowledgeBase` 类提供按模块/按ID/按标签/关联遍历等查询方法

### 其他 Skill 集成示例

**在其他 Skill 的 SKILL.md 中添加**：

```yaml
---
# 在 description 中声明依赖关系
description: 根据 {project_root}/knowledge-base/ 中的业务知识生成功能测试用例。
  依赖 knowledge-base-manager 维护的知识库目录结构。
---
```

```markdown
## 前置依赖

本 Skill 利用 `knowledge-base-manager` 建立的业务知识库作为数据源。
知识库位于项目根目录 `knowledge-base/`，结构和查询方式参见其 `references/kb_api.md`。
```

详细集成规范见 `references/kb_api.md`。

## 目录和文件说明

- `references/kb_structure.md`：知识库目录结构详细定义
- `references/doc_templates.md`：各类型文档模板和字段说明
- `references/workflows.md`：详细工作流程示例
- `references/prd_import_guide.md`：PRD 文档导入解析指南（docx/pdf/md/图片）
- `references/api_import_guide.md`：Swagger/Postman 接口文档导入指南
- `references/kb_api.md`：知识库对外接口规范（其他 Skill 集成指南）
- `scripts/init_kb.py`：知识库初始化脚本
- `scripts/update_index.py`：索引维护脚本
- `scripts/import_swagger.py`：Swagger/OpenAPI 导入脚本
