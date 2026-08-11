---
name: api-script-gen-with-apifoxmcp
description: 接口自动化脚本生成器。根据用户描述，基于接口索引 knowledge-base/02-api-docs/api-index.md 定位接口，通过 Apifox MCP 实时拉取最新接口详情，在 api-auto-test 框架的 api/services/tests 三层内编写接口自动化脚本。支持单接口用例和多接口串联场景用例（需用户提供串联顺序），异常用例仅在用户明确要求时生成。触发词："编写接口自动化"、"生成接口脚本"、"接口自动化用例"、"写个场景用例"、"接口串联"、"生成XX模块的自动化脚本"。
---

# 接口自动化脚本生成器

根据用户描述生成接口自动化脚本。接口索引、框架位置与编写边界全部固定，见下文。

## 固定路径

| 资源    | 路径                                                                   |
| ----- | -------------------------------------------------------------------- |
| 接口索引  | `knowledge-base/02-api-docs/api-index.md`（全部 ~270 个端点的路由→模块→ref 映射表） |
| 自动化框架 | `api-auto-test/`                                                     |
| 编码规范  | 本 skill 的 `references/coding_standards.md`（编写代码前必读）                  |

**重要**：

- 接口总数已超 270 个端点，**严禁一次性调用 `read_project_oas_ijy213` 读取全量接口**。
- 所有接口详情通过 Apifox MCP `read_project_oas_ref_resources_ijy213` 按 ref 路径**实时拉取**，确保参数和响应结构永远是最新的。
- 工作流程：**索引匹配 → MCP 拉取详情 → 编码**。

## 硬性规则（不可违反）

1. **编写范围只限三层**：只允许在 `api/`、`services/`、`tests/` 下新增或修改文件。
   `core/`、`config/`、`common/`、`utils/`、`conftest.py` 一律只读复用，禁止改动。
2. **默认只写正向/场景用例**：异常用例（非法参数、越权、非法状态流转等负向用例）
   **必须用户在本次请求中明确说出**（如"异常用例"、"负向用例"、"异常场景"）才生成；
   用户未提及时，只写正向单接口用例或场景串联用例，且不要主动追问"要不要异常用例"。
3. **场景用例（多接口串联）必须有用户提供的串联顺序**：
   - 用户已给出顺序（如"上架→维护→恢复→下架"）→ 按该顺序拼接流程，禁止自行增删或重排步骤；
   - 用户说"要场景"但没给顺序 → 必须先询问串联顺序，拿到顺序前不得动手编写；
   - 步骤间的数据传递（如上一步返回的 id 给下一步用）由 AI 依据接口文档自动衔接。
4. **复用优先**：同模块已有 `xxx_api.py` / `xxx_service.py` 时在原文件内追加方法，
   禁止新建重复文件；已有方法能满足需求时直接复用，禁止重写。
   在列表/响应中按字段查找或提取嵌套字段时，复用 `utils/jsonpath_utils`
   （`jsonpath_first_match` / `jsonpath_get` / `jsonpath_find`），
   **禁止在 service 层新增 `find_xxx_in_list` 这类专用查找方法**。
5. **管理员和匿名身份必须使用 conftest 提供的 fixture**：
   - 管理员上下文只能用 conftest 的 session 级 `admin` fixture，
     禁止在用例中自行 `AuthService().login(管理员账号)` 重复登录；
   - 匿名引导（注册/登录动态用户）只能用 conftest 的 `auth_service` fixture，
     禁止在用例中自行实例化 `AuthService()`。

## 工作流程

### 第 1 步：通过索引定位接口

从用户描述中提取关键词（业务动作、资源名、模块名），搜索 `knowledge-base/02-api-docs/api-index.md`：

- **按模块名搜索**：如"设备上架"→ 在 device-center 模块下匹配 `/api/devices/{id}/shelve`
- **按路径关键词搜索**：如"预约"→ 匹配 `/api/reservations/*` 相关接口
- **按描述搜索**：如"立即使用设备"→ 匹配 `immediate-use` 接口

确认：

- 用例类型：单接口正向 / 场景串联（需顺序，见硬性规则 3）/ 异常（需明确要求，见硬性规则 2）；
- 找到匹配后进入第 2 步拉取接口详情；
- 完全无法匹配时，列出最接近的候选接口让用户确认，不要凭空猜测接口契约。

### 第 2 步：按需拉取接口详情（全部从 Apifox MCP 实时获取）

对第 1 步匹配到的每个接口，调用 Apifox MCP 拉取最新详情：

```
调用 read_project_oas_ref_resources_ijy213
       path = 索引中 ref 列的值（如 /paths/_api_devices_shelve.json）

从返回的 OpenAPI schema 中提取：
       - operationId / summary（接口功能描述）
       - parameters（query/path/header 参数及必填性）
       - requestBody（JSON schema，注意 camelCase 字段名）
       - responses（成功响应的数据结构）
```

**注意**：

- 每次只拉取匹配到的 3-8 个接口的 ref 子文件，**严禁调用 `read_project_oas_ijy213` 全量读取**；
- 同时检查 `api/`、`services/` 下是否已有该模块文件及可复用方法；
- 阅读 `references/coding_standards.md`，严格按规范编码。

### 第 3 步：按层编写（api → services → tests）

- **api 层**：薄传输层，每方法对应一个端点，直接透传 service 拼好的 params/json，返回原始 Response；
- **services 层**：注入 `UserContext`，负责 snake_case→camelCase 字段映射、可选参数过滤、
  body 拼装、`parse_response` 解析、数据提取；
- **tests 层**：pytest + allure，测试文件放入对应业务目录：

| 接口索引模块                             | tests 目录        |
| ---------------------------------- | --------------- |
| user-auth                          | `tests/auth/`   |
| dashboard                          | `tests/home/`   |
| device-center（市场/查询类）              | `tests/market/` |
| device-center（生命周期/维护类）、operations | `tests/op/`     |
| my                                 | `tests/my/`     |
| system-settings                    | `tests/sys/`    |

归属不确定时，参考已有测试文件位置；仍无法判断再询问用户。

### 第 4 步：验证

在 `api-auto-test/` 目录下执行采集检查（不实际调接口）：

```bash
python -m pytest tests/<目录>/<新文件>.py --collect-only -q
```

采集通过（无导入/语法错误）即完成；如有报错先修复。除非用户明确要求，不要真正运行用例。

### 第 5 步：交付说明

简要列出：新增/修改的文件、覆盖的接口（method + path）、用例清单（allure title）、
场景用例的串联顺序；如有依赖环境数据的 `pytest.skip` 条件一并说明。
