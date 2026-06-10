---
name: api-testcase-generator
description: >
  API接口自动化测试用例生成器 - 根据Swagger/OpenAPI文档生成接口测试用例与自动化脚本。

  **核心能力**：解析Swagger JSON/YAML、自动分析接口依赖链路、支持多格式输出（Pytest/Postman/JMeter/Excel）、内置断言规则库、支持场景化用例生成。

  **触发词**：
  - "生成接口测试用例"、"API测试"、"Swagger测试"
  - "生成自动化脚本"、"接口场景用例"
  - "根据接口文档生成测试"
---

# API接口自动化测试用例生成器

## 快速参考

### 输入格式

| 类型 | 支持格式 |
|------|---------|
| Swagger/OpenAPI | `.json`, `.yaml`, `.yml` |
| 在线文档 | 任意可访问的Swagger URL |

### 输出格式

| 格式 | 文件后缀 | 适用场景 |
|------|---------|---------|
| Pytest + Requests | `.py` | Python自动化测试框架 |
| Postman Collection | `.json` | 手动/API测试 |
| JMeter | `.jmx` | 性能/接口测试 |
| Excel 用例 | `.xlsx` | 用例评审/管理 |

### 用例类型

| 类型 | 说明 |
|------|------|
| 单接口测试 | 每个接口独立测试 |
| 场景链路测试 | 多接口按业务链路串联 |
| 正向测试 | 正常业务流程验证 |
| 异常测试 | 错误参数、越权、超时等 |

---

## 核心功能

### 1. Swagger/OpenAPI 解析

自动解析 Swagger/OpenAPI 文档，提取：
- 接口路径 (Paths) 与 HTTP 方法
- 请求参数 (Query/Body/Path/Header)
- 响应状态码与 Schema
- 认证方式 (Bearer Token, API Key, OAuth2)

### 2. 场景链路生成

**自动分析**：
- 通过响应 Schema 中的 ID 字段与路径参数匹配推断依赖
- 识别 CRUD 模式（Create → Read → Update → Delete）
- 识别认证链路（Login → Business API → Logout）

**手动指定**：
- 执行过程中询问用户是否需要补充/调整场景链路
- 支持用户自定义接口调用顺序与数据传递规则

### 3. 断言策略

**默认断言**：
- HTTP 状态码匹配（2xx/4xx/5xx）
- 响应 Content-Type 校验

**业务断言规则库**（`references/assertion-rules.md`）：
- 创建资源 → 调用查询接口确认存在
- 更新资源 → 调用查询接口确认变更
- 删除资源 → 调用查询接口确认不存在（404）
- 列表查询 → 响应为数组且包含操作项
- 登录 → 响应包含 Token 且后续请求认证通过

**自定义断言**：
- 支持用户通过注释或规则文件扩展断言

### 4. 多格式输出

根据用户需求或项目现有框架选择输出格式：
- **Pytest**: 生成可直接运行的 Python 测试代码，支持 conftest.py 配置
- **Postman**: 生成 Collection v2.1 格式，含 Tests 断言脚本
- **JMeter**: 生成 JMX 文件，含断言与变量传递
- **Excel**: 生成标准测试用例文档，含步骤、预期结果、优先级

---

## 工作流程

```
1. 解析 Swagger → 提取接口定义与模型
2. 分析依赖 → 自动推断接口调用链路
3. 询问用户 → 确认/补充场景与输出格式
4. 加载断言规则 → 应用状态码与业务断言
5. 生成测试用例 → 按选定格式输出文件
```

### 详细步骤

#### 步骤 1：解析 Swagger

读取用户提供的 Swagger JSON/YAML 或 URL，调用脚本解析：

```bash
python scripts/swagger_parser.py --input swagger.json --output parsed_api.json
```

输出 `parsed_api.json` 包含：
- 接口列表（路径、方法、参数、响应）
- 模型定义（Schema）
- 自动推断的依赖关系

#### 步骤 2：分析与询问

加载 `parsed_api.json` 后，向用户展示：
1. 识别到的接口数量与模块分布
2. 自动推断的场景链路（如 CRUD、登录流程）
3. 询问是否需要：
   - 调整/补充场景链路
   - 选择输出格式（Pytest/Postman/JMeter/Excel）
   - 指定现有测试框架路径（用于适配）

#### 步骤 3：生成测试用例

确认需求后，调用生成脚本：

```bash
python scripts/generate_testcases.py \
  --input parsed_api.json \
  --format pytest \
  --scenarios scenarios.json \
  --output ./api_tests/
```

参数说明：
- `--input`: 解析后的 API JSON 文件
- `--format`: 输出格式（`pytest`, `postman`, `jmeter`, `excel`）
- `--scenarios`: 场景链路配置 JSON（可选，默认使用自动分析结果）
- `--output`: 输出目录

---

## 断言规则库

参考 `references/assertion-rules.md` 获取完整规则。

### 常见业务断言模式

| 操作类型 | 断言内容 |
|---------|---------|
| POST 创建 | 状态码 201/200；响应体包含创建字段；调用 GET 确认存在 |
| GET 查询 | 状态码 200；响应体为对象/数组；关键字段非空 |
| PUT/PATCH 更新 | 状态码 200；响应体字段已更新；调用 GET 确认变更 |
| DELETE 删除 | 状态码 200/204；调用 GET 返回 404 |
| LIST 列表 | 状态码 200；响应为数组；分页字段正确 |
| LOGIN 登录 | 状态码 200；响应包含 token；使用 token 访问受保护接口成功 |

---

## 场景链路模式

参考 `references/scenario-patterns.md` 获取完整模式。

### 常见场景

| 场景 | 链路示例 |
|------|---------|
| CRUD 完整流程 | Create → Get → Update → Get → Delete → Get(404) |
| 认证业务流 | Login → Create → List → Logout → AccessDenied |
| 数据准备流 | Login → CreateData → RunTest → DeleteData → Logout |
| 批量操作流 | Login → CreateA → CreateB → List → DeleteAll → Logout |

---

## 脚本说明

### swagger_parser.py

解析 Swagger/OpenAPI 文件，输出结构化 JSON。

```bash
python scripts/swagger_parser.py --input swagger.json --output parsed_api.json
```

### generate_testcases.py

根据解析结果生成指定格式的测试用例。

```bash
python scripts/generate_testcases.py \
  --input parsed_api.json \
  --format pytest \
  --output ./output/
```

---

## 适配现有框架

若用户项目已存在测试框架，Skill 支持：
1. **代码注入模式**：生成用例代码插入现有 `tests/` 目录
2. **配置文件模式**：读取现有 `pytest.ini` / `conftest.py` / `package.json` 适配配置
3. **基类继承模式**：生成的 Pytest 类继承项目现有的 BaseTest 类

询问用户时收集：
- 现有框架类型（Pytest/Unittest/JMeter/Postman）
- 基类/配置路径
- 认证方式与统一处理逻辑

---

## 依赖库

确保本地 Python 环境已安装：

| 库名 | 安装命令 |
|-----|---------|
| `requests` | `pip install requests` |
| `pyyaml` | `pip install pyyaml` |
| `openpyxl` | `pip install openpyxl` |
| `jinja2` | `pip install jinja2` |

---

## 示例

### 示例1：Swagger生成Pytest脚本

1. 用户提供 `swagger.json`
2. 解析并自动识别 CRUD 链路
3. 询问用户确认输出格式为 Pytest
4. 生成 `test_user_api.py`：
   - `test_create_user` → 创建用户并断言 201
   - `test_get_user` → 查询用户并断言存在
   - `test_update_user` → 更新用户并断言变更
   - `test_delete_user` → 删除用户并断言 404
5. 代码可直接运行：`pytest test_user_api.py`

### 示例2：生成场景化Excel用例

1. 用户提供在线 Swagger URL
2. 解析后识别登录与订单模块
3. 用户手动指定场景：`Login → CreateOrder → GetOrder → CancelOrder`
4. 生成 Excel 用例，含：
   - 步骤：接口调用顺序
   - 数据传递：Token、OrderId 变量传递说明
   - 断言：每步状态码与业务校验点

---

## 注意事项

1. **Swagger 完整性**：文档中未定义的字段或响应可能导致生成用例不完整
2. **安全认证**：生成的用例默认包含认证占位符，需用户补充真实 Token/密钥
3. **数据隔离**：场景链路中建议为每个测试生成独立数据，避免数据污染
4. **人工评审**：自动生成的场景链路建议人工确认业务逻辑正确性
5. **环境配置**：生成的脚本需配置 `base_url` 与认证信息后方可执行
