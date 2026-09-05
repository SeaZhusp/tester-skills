# 工作流程详细说明

## 1. 生成功能测试用例

### 工作流程

```
用户请求 → 读取需求文档 → 读取关联接口文档 → 读取关联缺陷 → 补全业务规则 → 生成测试用例
```

### 步骤详解

1. **确定测试范围**
   - 询问用户要测试的模块/功能/需求ID
   - 如果是回归测试，询问关联的历史缺陷版本范围

2. **读取知识库基础信息**
   - `_architecture.md`：了解系统架构和技术栈，确定测试策略
   - `_glossary.md`：确认术语理解正确

3. **读取需求文档**
   - 读取目标模块的 `_overview.md`
   - 读取具体需求的 `REQ-*.md` 文件
   - 特别关注：业务流程、业务规则（RULE表）、验收标准

4. **读取关联接口文档**
   - 根据需求中的 `related_apis` 读取对应接口文档
   - 关注：入参约束、错误码、业务逻辑说明

5. **读取关联历史缺陷**
   - 根据需求的 `related_bugs` 和模块下所有缺陷
   - 关注：复现步骤、根本原因、修复方案
   - **缺陷集中的模块/功能应增加测试覆盖**

6. **生成测试用例**

   每个测试用例使用以下格式：

   ```markdown
   ### TC-AUTH-001: 正确的账号密码能登录成功
   
   - **优先级**: P0
   - **类型**: 正向
   - **前置条件**: 用户已注册且账号状态正常
   - **测试数据**: {"username": "zhangsan", "password": "Abc12345", "captcha": "1234"}
   - **测试步骤**:
     1. 打开登录页面
     2. 输入正确的用户名、密码、验证码
     3. 点击"登录"按钮
   - **预期结果**:
     1. 登录成功，跳转至首页
     2. 返回有效 token
     3. 用户信息显示正确
   - **关联需求**: REQ-001
   - **关联缺陷回归**: 无
   ```

### 用例维度覆盖

| 维度 | 说明 | 数量建议 |
|------|------|---------|
| 正向用例 | 覆盖所有正常业务流程和分支 | 每个功能3-8个 |
| 逆向用例 | 错误输入、异常操作 | 每个约束1-2个 |
| 边界用例 | 边界值、最大/最小/空值 | 每个范围限制1个 |
| 业务规则 | 每条 RULE 至少1个用例 | RULE 数量 |
| 历史缺陷 | 已修复缺陷的回归验证 | 关联缺陷数量 |

### 输出格式

- 文件路径：`04-test-cases/functional/TC-{模块}-{功能描述}.md`
- 与需求文档命名对齐，便于关联查找

---

## 2. 生成接口自动化脚本

### 支持的语言/框架

| 语言 | 框架 | 适用场景 |
|------|------|---------|
| Python | pytest + requests | 通用，推荐 |
| Java | TestNG + RestAssured | Java 技术栈团队 |
| JavaScript | Jest + axios | 前端测试 |
| TypeScript | Playwright API | 可同时用于 UI 测试 |

### 脚本结构要求

```python
"""
API-auth_login.py - 用户登录接口自动化脚本
基于知识库: REQ-001, API-auth_login
生成时间: 2026-06-01
"""

import pytest
import requests
from config import BASE_URL, HEADERS

# 测试数据（数据驱动）
LOGIN_CASES = [
    {
        "case_id": "API-LOGIN-001",
        "desc": "正确的账号密码登录",
        "payload": {"username": "zhangsan", "password": "Abc12345", "captcha": "1234"},
        "expected_code": 0,
        "expected_status": 200
    },
    {
        "case_id": "API-LOGIN-002",
        "desc": "错误的密码",
        "payload": {"username": "zhangsan", "password": "wrong_pwd", "captcha": "1234"},
        "expected_code": 1001,
        "expected_status": 400
    },
    {
        "case_id": "API-LOGIN-003",
        "desc": "错误的验证码",
        "payload": {"username": "zhangsan", "password": "Abc12345", "captcha": "0000"},
        "expected_code": 1003,
        "expected_status": 400
    },
    {
        "case_id": "API-LOGIN-004",
        "desc": "连续5次失败后账号锁定",
        "payload": {"username": "lock_test", "password": "wrong_pwd", "captcha": "1234"},
        "expected_code": 1002,
        "expected_status": 403,
        "repeat": 5
    },
]

class TestUserLogin:

    @pytest.mark.parametrize("case", LOGIN_CASES)
    def test_login(self, case):
        """用户登录接口 - 数据驱动测试"""
        # 重试逻辑（用于测试锁定等状态变化）
        repeat_count = case.get("repeat", 1)
        for i in range(repeat_count):
            resp = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"username": case["payload"]["username"],
                       "password": "wrong_pwd" if repeat_count > 1 else case["payload"]["password"],
                       "captcha": case["payload"]["captcha"]},
                headers=HEADERS
            )
        
        # 验证
        assert resp.status_code == case["expected_status"]
        assert resp.json()["code"] == case["expected_code"]

    def test_login_without_captcha(self):
        """不传验证码"""
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "zhangsan", "password": "Abc12345"},
            headers=HEADERS
        )
        assert resp.status_code == 400
        assert resp.json()["code"] in [1003, 9999]

    def test_login_empty_password(self):
        """密码为空"""
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "zhangsan", "password": "", "captcha": "1234"},
            headers=HEADERS
        )
        assert resp.status_code == 400
```

### 生成要求

1. **数据驱动**：测试数据与代码分离，使用参数化
2. **覆盖错误码**：对照接口文档的错误码表，每个错误码至少1个用例
3. **参数校验**：覆盖必填项、类型、长度约束、格式校验
4. **业务规则**：覆盖 RULE 表中的每条规则
5. **环境配置**：支持通过环境变量切换 dev/test/staging
6. **输出路径**：`05-automation-scripts/api/{module}/{功能名}_test.py`

---

## 3. 生成 UI 自动化脚本

### 支持的框架

| 框架 | 语言 | 说明 |
|------|------|------|
| Playwright | TypeScript | 推荐，跨浏览器支持好 |
| Cypress | JavaScript | 适合前端测试 |
| Selenium | Python/Java | 传统方案 |

### 生成要求

以 Playwright + TypeScript 为例：

```typescript
// auth-login.spec.ts - 用户登录UI自动化
// 基于知识库: REQ-001, API-auth_login
// 基于缺陷: BUG-001

import { test, expect } from '@playwright/test';

test.describe('用户登录功能', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('TC-AUTH-001: 正确的账号密码能登录成功', async ({ page }) => {
    // 输入账号密码
    await page.fill('[data-testid="username"]', 'zhangsan');
    await page.fill('[data-testid="password"]', 'Abc12345');
    await page.fill('[data-testid="captcha"]', '1234');
    
    // 点击登录
    await page.click('[data-testid="login-btn"]');
    
    // 验证跳转到首页
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('[data-testid="user-info"]')).toContainText('张三');
  });

  test('TC-AUTH-005: Token过期后自动跳转登录页', async ({ page }) => {
    // 基于BUG-001: 验证Token过期处理
    // 先正常登录
    await page.fill('[data-testid="username"]', 'zhangsan');
    await page.fill('[data-testid="password"]', 'Abc12345');
    await page.fill('[data-testid="captcha"]', '1234');
    await page.click('[data-testid="login-btn"]');
    await expect(page).toHaveURL(/\/dashboard/);
    
    // 清除本地存储的token
    await page.evaluate(() => localStorage.removeItem('token'));
    
    // 执行需要登录的操作
    await page.goto('/dashboard');
    
    // 验证跳转回登录页，并显示提示
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('.toast-message')).toContainText('登录已过期');
  });

  test('TC-AUTH-002: 错误密码提示错误', async ({ page }) => {
    await page.fill('[data-testid="username"]', 'zhangsan');
    await page.fill('[data-testid="password"]', 'wrong_password');
    await page.fill('[data-testid="captcha"]', '1234');
    await page.click('[data-testid="login-btn"]');
    
    // 验证错误提示
    await expect(page.locator('.error-message')).toContainText('用户名或密码错误');
  });
});
```

### 生成要求

1. **基于业务流程**：测试步骤对应需求文档中的业务流程
2. **数据隔离**：每个测试独立准备和清理数据
3. **回归缺陷**：对每个相关缺陷编写回归测试
4. **元素定位**：优先使用 `data-testid`，其次是语义化选择器
5. **输出路径**：`05-automation-scripts/ui/{module}/{功能名}.spec.ts`

---

## 5. 从 PRD 文档导入需求

### 核心原则（必须先读）

0. **业务逻辑是核心焦点** — 业务流程和业务规则最优先
1. **只写文档中有的，绝不编造**
2. **信息不足时反问用户，不要自行决定**
3. **一次只入库一个模块**

### 工作流程

```
用户提供PRD文件 → 保存源文件 → 读取内容 → 列出模块让用户选择 → 处理单个模块（重点：业务逻辑）→ 逐项确认 → 入库 → 询问是否继续
```

### 详细步骤

1. **接收文件**：用户提供 PRD 文件路径，或拖拽文件到 IDE
2. **保存源文件**：复制原始文件到 `01-requirements/_source/`
   - 命名规范：`{版本号}_{简短描述}.{ext}`，如 `v1.2_用户认证PRD.docx`
3. **读取文档内容**（根据格式选择策略）：
   - **docx 文件**：使用 `docx` skill 或 `python-docx` 库读取，提取标题层级和表格
   - **pdf 文件**：使用 `pdf` skill 或 `PyMuPDF`/`pdfplumber` 提取文本和表格
   - **md 文件**：直接读取 Markdown 内容
   - **图片文件**：使用大模型的视觉能力识别图中的文字
4. **识别并列出模块**：
   - 通读 PRD，找出涉及的所有功能模块
   - 反问用户："我看到这个 PRD 涉及 user-auth 和 payment 两个模块，先处理哪一个？"
5. **处理选定模块**：
   - 从 PRD 中只提取选定模块的内容
   - 只写 PRD 中明确有的章节，没有的不要写
   - 信息不足时反问用户
6. **生成文档**：按 `doc_templates.md` 模板生成 REQ-*.md，只包含实际存在的章节
7. **逐项用户确认**：名称、描述、规则、验收标准逐项确认
8. **写入知识库**：写入 `01-requirements/{module}/` 目录
9. **询问继续**：完成后问用户"当前模块已入库，还有 payment 模块需要处理，要现在继续吗？"
10. **后处理**：调用 `scripts/update_index.py`，更新 `_upgrade_log.md`

### 错误做法示例

| ❌ 错误做法 | ✅ 正确做法 |
|-----------|-----------|
| PRD 没写规则，自行编造"验证码有效期5分钟" | 规则章节不写，或反问用户"验证码有没有有效期限制？" |
| PRD 涉及3个模块，一次性全部入库 | 列出模块让用户选择，逐个处理 |
| PRD 只写了"用户可登录"，编造业务流程步骤 | 反问用户"登录的具体流程是怎样的？" |

### 反问示例话术

- **模块选择**："这个 PRD 提到 {模块A} 和 {模块B} 两个功能，先处理哪个？"
- **业务流程不清**："登录功能的具体流程是什么？正常路径是怎么走的，异常情况怎么处理？"
- **规则值缺失**："文档提到了密码长度限制，但没写具体值，应该是多少？"
- **版本确认**："PRD 文件名看不出版本号，暂定 v1.0，可以吗？"
- **确认需求名**："这个功能文档的标题定为'用户登录功能'，是否正确？"
- **状态流转不清**："订单状态从'待支付'到'已支付'，中间有没有超时自动取消的逻辑？"
- **分支条件模糊**："哪些情况下需要触发审批流程？审批不通过怎么办？"

---

## 6. 从 Swagger/OpenAPI 导入接口

### 工作流程

```
用户提供Swagger文件 → 保存源文件 → 解析路径/方法/参数/响应 → 按tags分模块 → 生成API文档 → 更新索引
```

### 详细步骤

1. **接收文件**：用户提供 Swagger 2.0 / OpenAPI 3.x JSON 或 YAML 文件
2. **保存源文件**：复制到 `02-api-docs/_source/`
3. **解析规约文件**：
   - 读取 `info`、`servers`/`host`、`paths`、`components.schemas`/`definitions`
   - 注意区分 Swagger 2.0 和 OpenAPI 3.x 的结构差异（主要在 requestBody 和 schemas）
4. **按 tags 分模块**：
   - 遍历所有 path items
   - 按 `tags[0]` 分组（如果没有 tags，按 path 第一段分组）
   - 为每个 tag 创建模块目录和 `_overview.md`
5. **按 path 生成 API 文档**：
   - 每个 path + method 生成一个 `API-{module}_{name}.md`
   - 参考 `api_import_guide.md` 的字段映射规则
   - 成功生成示例请求和响应 JSON
   - 构建错误码表
6. **用户确认**：
   - 展示模块划分和接口数量
   - 确认模块名称
7. **写入知识库**，更新索引

### JSON 解析要点

对 JSON/YAML 中的 schema $ref 引用做解析：

- 解析 `#/components/schemas/xxx` 或 `#/definitions/xxx`
- 将引用替换为实际 schema 定义
- 处理嵌套 schema 和 allOf/oneOf/anyOf

### YAML 处理要点

- 使用 Python 的 `yaml` 库（PyYAML）解析
- 注意 YAML 的锚点（&anchor）和别名（*alias）

---

## 7. 从 Postman 集合导入接口

### 工作流程

```
用户提供Postman集合JSON → 保存源文件 → 解析请求定义 → 按文件夹分模块 → 生成API文档 → 更新索引
```

### 详细步骤

1. **接收文件**：用户提供 Postman Collection v2.1 或 v2.0 JSON
2. **保存源文件**：复制到 `02-api-docs/_source/`
3. **解析集合**：
   - 递归遍历 `item[]` 结构
   - 注意嵌套文件夹（Postman 支持无限层级嵌套）
   - 提取每个 `item` 中的 `request` 定义
4. **按文件夹分模块**：
   - 顶层文件夹 → 知识库模块
   - 嵌套文件夹 → 子模块或合并到父模块
   - 无文件夹 → 归入 `default` 模块
5. **生成 API 文档**：
   - 从 `request.url.raw` 中提取 path（去掉 base URL）
   - 从 `request.body` 中提取请求体结构和示例
   - 从 `request.response[]` 中提取响应示例（如果有）
   - 从 `request.auth` 中提取认证方式
6. **用户确认**后写入知识库，更新索引

### 变量处理

Postman 中的 `{{variable}}` 处理：

- 变量名保留在文档中，标注为可配置变量
- 在文档说明中添加："请根据实际环境替换 {{base_url}} 等变量"

---

## 8. 知识库定期维护

### 月度维护清单

- [ ] 更新 `_upgrade_log.md`：记录本月知识库变更
- [ ] 检查是否有 `status: draft` 的文档需要更新
- [ ] 检查缺陷状态是否需要同步更新
- [ ] 重新生成模块索引和统计分析
- [ ] 将 `status: deprecated` 的文件迁移到 `_archived/`

### 版本对接流程

当有新版本发布时：

1. 在需求文档中新增版本记录
2. 更新接口文档的变更历史
3. 将本次修复的缺陷状态更新为 `verified`
4. 生成新版本的回归测试用例包
