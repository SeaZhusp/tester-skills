---
name: api-index-sync-apifoxmcp
description: 接口索引同步器。当 Apifox 端新增/修改/删除接口后，将 knowledge-base/02-api-docs/api-index.md 这层轻量缓存与 Apifox 最新 OpenAPI Spec 对齐。支持全量刷新与差异刷新（仅同步新增/变更的接口）。触发词："更新接口索引"、"同步接口索引"、"刷新接口索引"、"接口索引落后了"、"apifox 新增了接口"、"重建接口索引"、"对一下接口索引"。
---

# 接口索引同步器

`knowledge-base/02-api-docs/api-index.md` 是 Apifox 全量接口的**轻量缓存索引**（路由→模块→ref 映射表），
供 `api-script-gen-with-apifoxmcp` 等 skill 做关键词匹配用。本 skill 负责把它与 Apifox 最新数据对齐。

## 固定路径

| 资源 | 路径 |
|------|------|
| 接口索引（待刷新/生成） | `knowledge-base/02-api-docs/api-index.md` |
| Apifox 项目 | project-id `8658258`（"默认模块"） |
| MCP server | `Apifox接口文档` |

## ⚠️ 工具名探测（每次执行前必做，避免后缀失效）

Apifox MCP 工具名带**连接相关后缀**（如 `319je6`），该后缀随 MCP server 重连 / 换 project / 重新授权可能变化，
**不要假定固定为某个值**。执行任何读取前，先探测当前 `Apifox接口文档` server 上实际可用的三个工具：

```
调用 mcp_get_tool_description，依次尝试（以 server 名 "Apifox接口文档" 为准）：
  - read_project_oas_<suffix>                  // 读全量 OpenAPI Spec
  - refresh_project_oas_<suffix>               // 强制从服务器刷新 Spec
  - read_project_oas_ref_resources_<suffix>    // 按 $ref 读单个接口详情
```

- 若 `319je6` 后缀可用 → 直接使用（当前环境已知可用）。
- 若 `319je6` 返回 "not found" → 改用探测到的真实后缀，并将下文所有 `read_project_oas_319je6` /
  `refresh_project_oas_319je6` / `read_project_oas_ref_resources_319je6` **统一替换为实际后缀**后再调用。
- 三个工具的后缀在同一 server 上保持一致，探测一次即可。

> 探测失败（三个后缀都找不到）时，停止并提示用户检查 MCP server `Apifox接口文档` 是否已连接。

## 关键约束（不可违反）

1. **绝对禁止一次性全量读取 OpenAPI Spec 来"记忆"所有接口**。
   索引生成/对齐所需的全量路径与摘要信息，必须通过探测到的 `read_project_oas_<suffix>` 获取；
   单个接口详情才用探测到的 `read_project_oas_ref_resources_<suffix>`。
2. **索引只是缓存，不存接口详情**。
   api-index.md 中每个接口只保留：`方法 / 路径 / 描述 / ref` 四列，详见下方模板。
   接口的请求/响应 schema 永远由下游 skill 实时从 Apifox 拉取，索引里**不要**写参数结构。
3. **internal API 单独折叠**。
   路径以 `/api/internal/` 开头的接口归入 `Internal API（仅内部调用）` 折叠区，且不含 ref 列，
   标记为"不对外暴露、不参与自动化测试"。
4. **保留结构完整性**。
   刷新时保留模块总览表、每个模块的二级/三级标题分组、顶部"最后更新"时间戳、底部"使用说明/统计与维护"章节。
   新增接口若属于已有模块分组，插入对应分组表格；若属于新模块/新分组，按现有风格新增标题与表格。
5. **先刷新再读**。
   正式拉取前先调用探测到的 `refresh_project_oas_<suffix>`，确保拿到的是 Apifox 服务器最新 Spec。

## 模块分组约定（与现有索引保持一致）

| 模块 | 含义 | 索引锚点 |
|------|------|---------|
| user-auth | 认证、登录、注册 | `#user-auth` |
| device-center | 设备管理、分组、预约、会话、应用、采集、监控 | `#device-center` |
| my | 个人中心：我的预约、消息、收藏、使用统计 | `#my` |
| system-settings | 用户管理、角色、权限、系统偏好 | `#system-settings` |
| operations | 工单、告警、文件、日志、通知 | `#operations` |
| dashboard | 仪表盘、使用统计 | `#dashboard` |
| internal（折叠） | 内部微服务调用接口 | `#internal-api仅内部调用` |

device-center 模块内部按业务再分：设备管理 / 设备批量操作 / 设备收藏 / 设备市场 / 设备分组 /
设备预约 / 预约关联应用 / 会话（同屏）/ 截图录屏 / APP 文件管理 / 设备监控。新增接口优先归入最贴近的分组。

## 工作流程

### 第 0 步：确定刷新模式

向用户确认或根据上下文判断（用户未指定时默认"差异刷新"）：

- **全量刷新**：重建整份索引。使用场景：索引严重滞后、模块结构需重建。
- **差异刷新**：只把 Apifox 相对当前索引**新增/变更/删除**的部分同步过来。使用场景：用户说"apifox 新增了接口"。

> 全量刷新前先读取现有 `api-index.md` 作为结构模板，避免破坏已沉淀的分组与描述措辞。

### 第 1 步：拉取最新 Spec 摘要

```
调用 refresh_project_oas_<suffix>        # 先强制刷新到最新（探测到的后缀）
调用 read_project_oas_<suffix>           # 读取 OpenAPI Spec（含 paths / tags / info）
```

从 Spec 中提取：
- `paths`：每个路径对象下的 `get/post/put/delete` 等方法节点；
- 每个方法节点的 `summary` / `operationId` / `tags`（用于归类到模块与分组）；
- `servers` 或 `info` 中的 basePath（通常为 `/api`），拼出完整路径；
- 用以生成 ref：Apifox 规则为 `/paths/_{method}_{path}.json`，其中：
  - 前导 `/api` 去掉、其余 `/` 替换为 `_`；
  - `{id}` 形式转为 `%7Bid%7D`（URL 编码的大括号）；
  - 例：`POST /api/devices/{id}/shelve` → `/paths/_api_devices_%7Bid%7D_shelve.json`。

### 第 2 步：构建/对齐索引数据

- 以"方法 + 路径"为唯一键。
- 按 `tags`（或路径前缀）映射到模块与分组。
- 若某接口在当前索引已存在且 `summary`/ref 未变 → 保留原描述（维持人工润色过的措辞）；
  若 Apifox 端 `summary` 变化或有新增接口 → 采用 Apifox 最新 `summary`。
- internal 接口（路径含 `/api/internal/`）单独收集，不进入模块总览计数。

### 第 3 步：写回 api-index.md

- **全量刷新**：用 `write_to_file` 整体重写，保留顶部时间戳（更新为当天日期）、
  模块总览表、使用说明章节，重排所有模块表格。
- **差异刷新**：用 `replace_in_file` 仅修改受影响的表格行 / 新增分组标题，并只更新顶部时间戳。
- ref 列一律用 Apifox 生成的 `/paths/...json` 路径。

### 第 4 步：同步更新关联文件（如受影响）

- 若接口模块总数/端点数变化，更新 `knowledge-base/_index.md` 的"模块概览"接口数列与"最近更新"日志。
- 提醒用户：`api-script-gen-with-apifoxmcp` 等下游 skill 不受影响（它们实时拉取详情），无需改。

### 第 5 步：交付说明

简要汇报：刷新模式、新增/变更/删除的接口数量与清单（method + path）、
更新后的对外端点总数（不含 internal）、以及本次写入/修改的文件。

## ref 路径生成规则（速查）

```
原始:  POST /api/devices/{id}/shelve
步骤:
  1. 去掉 /api          → devices/{id}/shelve
  2. / 替换为 _         → devices_{id}_shelve
  3. {  → %7B  } → %7D  → devices_%7Bid%7D_shelve
  4. 加前缀 /paths/_    → /paths/_api_devices_%7Bid%7D_shelve.json
     （注意全量路径要保留 /api：去掉的是"方法归类"用的前缀，ref 文件名仍以 _api 开头）
```

> 实际 ref 以探测到的 `read_project_oas_<suffix>` 返回的 Spec 内 `$ref` 值为准；
> 若 Spec 已直接给出各 path 的 `$ref`，直接采用，不要手写推算。
