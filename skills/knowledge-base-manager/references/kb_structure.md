# 知识库目录结构定义

## 根目录：`{project_root}/knowledge-base/`

```
knowledge-base/
│
├── _index.md                          # 【自动生成】全局索引：汇总所有模块及其文档
├── _glossary.md                       # 业务术语表：统一术语定义，消除歧义
├── _architecture.md                   # 系统架构说明：整体架构图、模块间关系
├── _upgrade_log.md                    # 知识库变更日志：记录每次更新的内容和原因
│
├── 01-requirements/                   # 【需求文档】按功能模块组织
│   ├── _source/                       # PRD 源文件存档（docx/pdf/md/图片原稿）
│   │   ├── v1.0_用户认证PRD.docx      # 原始 PRD 文档备份
│   │   └── v2.0_支付功能PRD.pdf
│   ├── _module-index.md               # 【自动生成】需求模块索引
│   ├── user-auth/                     # 示例：用户认证模块
│   │   ├── _overview.md               # 模块概述（模块职责、核心流程）
│   │   ├── REQ-001_用户登录功能.md
│   │   ├── REQ-002_用户注册功能.md
│   │   └── REQ-003_权限管理功能.md
│   ├── payment/                       # 示例：支付模块
│   │   ├── _overview.md
│   │   ├── REQ-004_商品下单功能.md
│   │   └── REQ-005_支付回调处理.md
│   ├── order/                         # 示例：订单模块
│   │   ├── _overview.md
│   │   ├── REQ-006_订单创建与管理.md
│   │   ├── REQ-007_订单退款流程.md
│   │   └── ...
│   ├── ...                            # 其他模块按需添加
│   └── _archived/                     # 归档的旧需求
│
├── 02-api-docs/                       # 【接口文档】按功能模块组织
│   ├── _source/                       # API 源文件存档（Swagger/Postman 原稿）
│   │   ├── openapi_v3.json            # Swagger/OpenAPI 规约
│   │   ├── swagger_v2.yaml
│   │   └── postman_collection.json    # Postman 集合
│   ├── _module-index.md               # 【自动生成】接口模块索引
│   ├── user-auth/
│   │   ├── _overview.md               # 模块接口概览
│   │   ├── API-auth_login.md          # POST /api/v1/auth/login
│   │   ├── API-auth_register.md       # POST /api/v1/auth/register
│   │   ├── API-auth_refresh.md        # POST /api/v1/auth/refresh
│   │   └── API-user_getProfile.md     # GET /api/v1/user/profile
│   ├── payment/
│   │   ├── _overview.md
│   │   ├── API-order_create.md        # POST /api/v1/orders
│   │   ├── API-payment_notify.md      # POST /api/v1/payment/callback
│   │   └── ...
│   └── _archived/
│
├── 03-defects/                        # 【历史缺陷库】按模块组织
│   ├── _module-index.md               # 【自动生成】缺陷模块索引
│   ├── _stats.md                      # 【自动生成】缺陷统计分析
│   ├── user-auth/
│   │   ├── _overview.md               # 模块缺陷概况
│   │   ├── BUG-001_登录会话超时未跳转.md
│   │   ├── BUG-002_注册验证码有效期异常.md
│   │   └── BUG-003_权限缓存未及时刷新.md
│   ├── payment/
│   │   ├── BUG-004_重复支付未拦截.md
│   │   └── BUG-005_退款金额计算错误.md
│   └── _archived/                     # 归档的旧缺陷（保留3年以上）
│
├── 04-test-cases/                     # 【生成目录】存放生成的测试用例
│   ├── functional/                    # 功能测试用例
│   ├── api/                           # 接口测试用例
│   └── ui/                            # UI 测试用例
│
└── 05-automation-scripts/             # 【生成目录】存放生成的自动化脚本
    ├── api/                           # 接口自动化脚本
    └── ui/                            # UI 自动化脚本（Playwright/Cypress等）
```

## 目录规范

### 模块划分原则

1. **按业务模块划分**，而非技术分层
2. 模块名使用小写字母+连字符：`user-auth`、`payment`
3. 每个模块目录下必须包含 `_overview.md` 概述文件
4. 一个需求/接口/缺陷只属于一个模块

### 文件命名规范

| 类型 | 命名模式 | 示例 |
|------|---------|------|
| 需求文档 | `REQ-{序号}_{简短描述}.md` | `REQ-001_用户登录功能.md` |
| 接口文档 | `API-{模块}_{功能名}.md` | `API-auth_login.md` |
| 缺陷记录 | `BUG-{序号}_{简短描述}.md` | `BUG-001_登录会话超时未跳转.md` |
| 模块概述 | `_overview.md` | 前缀下划线表示系统文件 |
| 模块索引 | `_module-index.md` | 自动生成 |
| 全局索引 | `_index.md` | 自动生成 |

### ID 生成规则

- **需求 ID**：`REQ-{三位数字}`，全局顺序递增，如 `REQ-001`
- **缺陷 ID**：`BUG-{三位数字}`，全局顺序递增，如 `BUG-001`
- **接口 ID**：`API-{模块}_{功能}`，语义化命名，如 `API-auth_login`

### 文档关联规则

所有文档通过 frontmatter 中的关联字段建立联系：

```
需求文档 → related_apis: [API-auth_login, API-auth_refresh]
需求文档 → related_bugs: [BUG-001, BUG-002]
接口文档 → related_requirements: [REQ-001]
缺陷记录 → related_requirements: [REQ-001]
缺陷记录 → related_apis: [API-auth_login]
```

### 更新维护原则

1. **新增**：按模板创建，填写完整关联字段
2. **修改**：更新 version + updated 日期，记录变更
3. **废弃**：status 改为 deprecated，不移除文件
4. **归档**：定期将 deprecated 文件移至 `_archived/` 目录
5. **索引**：每次变更后执行索引更新脚本
