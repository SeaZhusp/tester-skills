# tester-skills

一个测试工程师技能共享社区项目。收集、整理、共享 AI IDE 测试相关技能，支持团队协作和开源共建。

## 支持的平台

CodeBuddy、Cursor、Claude Code、Trae 等主流 AI IDE

## 项目结构

```
tester-skills/
├── skills/                              # 技能目录
│   ├── testcase-generator/              # 测试用例编写与导出
│   ├── testcase-review/                 # 测试用例评审
│   ├── qa-suite/                        # 测试服务全流程总控
│   ├── api-testcase-generator/          # API 接口测试用例生成
│   ├── api-index-sync-apifoxmcp/        # 接口索引同步（Apifox）
│   ├── api-script-gen-with-apifoxmcp/   # 接口自动化脚本生成（Apifox）
│   ├── requirement-auditor/             # 需求审计
│   ├── knowledge-base-manager/          # 业务知识库管理
│   ├── defect-report-generator/         # 缺陷报告生成
│   ├── docx/                            # Word 文档处理
│   ├── pdf/                             # PDF 文档处理
│   ├── xlsx/                            # Excel 电子表格处理
│   ├── fireworks-tech-graph/            # 技术图表生成
│   ├── wechat-article-writer/           # 公众号技术文章创作
│   ├── wechat-article-rewriter/         # 公众号文章伪原创改写
│   ├── wechat-multi-article-rewriter/   # 公众号多篇热点整合改写
│   └── skill-creator/                   # 自定义技能创建指南
├── README.md
├── .gitignore
└── LICENSE
```

## 已有技能

| 技能名称 | 分类 | 说明 |
|----------|------|------|
| testcase-generator | 用例设计 | 针对 PRD/原型/接口文档/用户故事，提炼全维度测试点，编写并审核测试用例，导出 Excel/CSV 导入禅道、TestRail、飞书多维表格 |
| testcase-review | 用例评审 | 对比 Excel 测试用例与 Word/PDF/PRD/图片需求文档，识别功能覆盖缺口，输出补充建议 |
| qa-suite | 测试服务 | 测试服务全流程总控（1 总控 + 4 子技能），覆盖「需求解构 → 用例生成 → 售前评估/报价 → 一致性核销」全链路，自动路由到对应子技能 |
| api-testcase-generator | 接口测试 | 根据 Swagger/OpenAPI 生成接口测试用例与自动化脚本，支持 Pytest/Postman/JMeter/Excel 多格式输出 |
| api-index-sync-apifoxmcp | 接口测试 | 同步 Apifox 接口索引缓存，支持全量/差异刷新，与最新 OpenAPI Spec 对齐 |
| api-script-gen-with-apifoxmcp | 接口测试 | 基于 Apifox MCP 与接口索引，在 api-auto-test 框架内生成单接口/多接口串联自动化脚本 |
| requirement-auditor | 需求质量 | 提交 PRD/BRD/技术方案前审查逻辑漏洞、遗漏边界、歧义与业务/技术风险，输出结构化缺陷报告 |
| knowledge-base-manager | 知识库 | 建立并维护业务知识库（需求/接口/缺陷），支持 PRD、Swagger/OpenAPI、Postman 导入 |
| defect-report-generator | 质量报告 | 将缺陷/任务清单 CSV 一键生成自包含、离线可打开的 HTML 测试缺陷报告 |
| docx | 文档处理 | 创建、编辑和分析 Word 文档（目录、表格、修订跟踪、评论、图片等） |
| pdf | 文档处理 | PDF 处理（读取、合并、拆分、旋转、水印、表单、OCR、加密等） |
| xlsx | 文档处理 | 创建、编辑和分析 Excel（公式、图表、数据清洗、格式转换等） |
| fireworks-tech-graph | 图表 | 生成 SVG+PNG 技术图表（架构图、流程图、时序图、UML 等） |
| wechat-article-writer | 公众号 | 公众号爆款技术文章创作（选题、标题、封面图、多平台适配），10%引入+10%原理+80%实操 |
| wechat-article-rewriter | 公众号 | 公众号文章深度伪原创改写（去 AI 味、规避查重、爆款标题、推流适配） |
| wechat-multi-article-rewriter | 公众号 | 多篇同主题热点文章去重、提炼、重组为原创长文 |
| skill-creator | 工具 | 创建和维护自定义技能的指南（新增/更新 agent 技能，沉淀专业知识、工作流或工具集成） |

> 注：`docx`、`pdf`、`xlsx` 三个技能采用各自的专有许可（见对应目录下的 LICENSE.txt），其余技能遵循项目根目录的 MIT License。

## 开源协议

MIT License
