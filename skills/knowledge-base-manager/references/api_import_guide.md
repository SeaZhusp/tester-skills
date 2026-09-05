# Swagger/Postman 接口文档导入指南

## 概述

本指南定义了如何从 Swagger/OpenAPI 规格文件和 Postman 集合中解析接口定义，结构化写入知识库的 `02-api-docs/` 目录。

## 支持的输入格式

| 格式 | 说明 | 规格版本 |
|------|------|---------|
| `swagger.json` | Swagger 2.0 JSON 格式 | 2.0 |
| `swagger.yaml` / `swagger.yml` | Swagger 2.0 YAML 格式 | 2.0 |
| `openapi.json` | OpenAPI 3.x JSON 格式 | 3.0 / 3.1 |
| `openapi.yaml` / `openapi.yml` | OpenAPI 3.x YAML 格式 | 3.0 / 3.1 |
| Postman Collection v2.1 JSON | Postman 集合导出格式 | v2.1 |
| Postman Collection v2.0 JSON | Postman 集合导出格式 | v2.0 |

## 一、Swagger/OpenAPI 解析

### 关键字段映射

#### 全局信息

| Swagger/OpenAPI 字段 | 映射到知识库 |
|----------------------|-------------|
| `info.title` | `_overview.md` 模块标题 |
| `info.description` | `_overview.md` 模块描述 |
| `info.version` | 每个 API 文件的 version 字段 |
| `servers[0].url` / `host+basePath` | API 基础 URL，存到 index |
| `tags[]` | 模块划分依据（默认） |
| `components.schemas` / `definitions` | 作为参考保留在 API 文档中 |

#### 接口（Path Item）

| Swagger/OpenAPI 字段 | 映射到知识库 API 文件 |
|----------------------|----------------------|
| `paths.{path}.{method}.operationId` | 语义化接口名（默认生成 API ID） |
| `paths.{path}.{method}.summary` | `title` 字段 |
| `paths.{path}.{method}.description` | 接口描述 |
| `paths.{path}.{method}.tags[]` | 所属模块 |
| `paths.{path}.{method}.parameters[]` | 请求参数字段表 |
| `paths.{path}.{method}.requestBody` | 请求体说明 |
| `paths.{path}.{method}.responses.{code}` | 响应说明（成功+错误） |
| `paths.{path}.{method}.security[]` | 鉴权要求，映射到 `auth_required` |
| `paths.{path}.{method}.deprecated` | 标记为废弃 |

#### 参数解析规则

将 Swagger parameter 对象映射为知识库的请求参数字段表：

| Swagger parameter 属性 | 知识库表格列 |
|------------------------|-------------|
| `name` | 字段 |
| `schema.type` | 类型 |
| `required` | 必填 |
| `schema.minLength` / `schema.maxLength` | 约束 |
| `schema.example` | 示例 |
| `description` | 说明 |
| `in` | 标注在参数名后如 `(header)` / `(query)` |

#### 响应解析规则

**成功响应**：`responses.200` 或 `responses.default`

- 提取 `content.application/json.schema` 中的字段定义
- 生成示例 JSON（如有 `example` 或 `examples`）
- 如果没有 schema，用 `description` 代替

**错误响应**：`responses.{4xx|5xx}`

- 收集所有非 2xx 的响应状态码
- 提取每个错误响应的 `description` 或 schema
- 构建错误码表（HTTP 状态码 + 错误描述）

### API ID 生成规则

```
API-{tag}_{operationId 或 path简写}
```

示例：
- tag=`user-auth`, operationId=`loginUser` → `API-user-auth_loginUser`
- 没有 operationId 时：tag=`user-auth`, path=`/api/v1/auth/login` → `API-user-auth_login`

### 模块划分

1. **优先使用 tags**：Swagger 的 tags 天然对应业务模块，直接作为目录名
2. **无 tags 时按路径前缀**：`/api/v1/auth/*` → `auth` 模块
3. **用户自定义**：让用户指定或调整模块映射

### 请求体处理（OpenAPI 3.x）

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          username:
            type: string
            description: 用户名
```

→ 映射到请求体说明和请求参数字段表

### 错误码提取策略

```yaml
responses:
  '200':
    description: 成功
  '400':
    description: 请求参数错误
  '401':
    description: 未授权
  '500':
    description: 服务器内部错误
```

→ 构建为标准错误码表

- 如果每个错误码有详细 schema，尽可能提取 `code` 字段
- 如果没有详细错误结构，使用 HTTP 状态码 + description 作为最小错误码信息

### 示例值生成

- 优先使用 schema 中的 `example` 字段
- 如果没有 example，根据 `schema.type` 生成合理的示例值：
  - `string` → `"example_string"`
  - `integer` → `1`
  - `boolean` → `true`
  - `array` → `[]`
  - 枚举类型 → 使用第一个枚举值

---

## 二、Postman 集合解析

### Postman 集合结构

```
collection/
├── info (name, description, schema)
├── item[]                    # 根级请求或文件夹
│   ├── name                  # 请求名称
│   ├── request               # 请求定义
│   │   ├── method
│   │   ├── url
│   │   │   ├── raw           # 完整 URL
│   │   │   ├── host/path/query
│   │   ├── header[]
│   │   ├── body
│   │   │   ├── mode          # raw/urlencoded/formdata
│   │   │   └── raw/urlencoded/formdata
│   │   ├── auth
│   ├── response[]            # 已保存的响应示例
│   └── item[]                # 子文件夹（嵌套结构）
```

### 关键字段映射

| Postman 字段 | 映射到知识库 API 文件 |
|-------------|----------------------|
| `info.name` | 用于 `_source/postman/` 文件名 |
| `item[].name` | `title` 字段或 `API ID` 的后缀 |
| `item[].request.method` | `method` 字段 |
| `item[].request.url.raw` | 提取 path 部分（去掉 base URL） |
| `item[].request.header[]` | 请求头表 |
| `item[].request.body` | 请求体说明 + 示例 JSON |
| `item[].response[]` | 响应示例，提取成功/失败结构 |

### 模块划分

1. **按文件夹结构**：Postman 的顶层文件夹对应知识库的模块目录
2. **扁平结构**：如果没有文件夹，将所有接口归入 `default` 模块，让用户重命名

### 需要注意的特殊点

- Postman 的 URL 可能是完整 URL（含 base URL），需要与 path 分离
- Postman 支持 `{{variables}}` 模板变量，在导入时标注为变量而非实际值
- Postman 的 body 可能是 raw JSON / form-data / x-www-form-urlencoded，需要分别处理
- Postman 的 auth 配置（Bearer token / Basic Auth / API Key）映射到 `auth_required`

---

## 三、通用处理规则

### source_link 字段

所有从 Swagger/Postman 导入的 API 文档，frontmatter 中应增加：

```yaml
---
source: openapi_v3.json      # 源文件名，指向 _source/ 目录
source_type: swagger         # swagger | openapi3 | postman
original_path: /api/v1/auth/login  # 原始路径
---
```

### 文档覆盖检查

导入前检查目标模块是否有同名接口文档，避免重复：

- 通过 `original_path` + `method` 判断是否已存在
- 如果存在，提示用户是否覆盖或新增版本
- 版本号自动 +1

### 导入摘要输出

导入完成后输出摘要：

```
✅ Swagger 导入完成！
源文件：openapi_v3.json（已保存在 _source/）
解析接口：共 24 个
生成接口文档：
- API-user-auth_login (POST /api/v1/auth/login)
- API-user-auth_register (POST /api/v1/auth/register)
...
模块划分：
- user-auth (8 个接口)
- payment (10 个接口)
- order (6 个接口)
```
