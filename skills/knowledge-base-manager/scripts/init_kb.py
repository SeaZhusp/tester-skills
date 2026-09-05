#!/usr/bin/env python3
"""
知识库初始化脚本
用法: python3 init_kb.py <项目根目录> [--module 模块1 模块2 ...]

示例:
  python3 init_kb.py /path/to/project
  python3 init_kb.py /path/to/project --module user-auth payment order
"""

import sys
import os
import argparse
from datetime import date
from pathlib import Path


TEMPLATES_DIR = Path(__file__).parent.parent / "references"


def create_file(path: Path, content: str):
    """创建文件，自动创建父目录"""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"  ⏭  已存在: {path}")
        return False
    path.write_text(content, encoding="utf-8")
    print(f"  ✅ 创建: {path}")
    return True


def init_knowledge_base(project_root: str, modules: list[str] | None = None):
    """初始化知识库结构"""
    root = Path(project_root) / "knowledge-base"
    today = date.today().isoformat()

    if root.exists():
        print(f"⚠️  知识库目录已存在: {root}")
        print("  将补全缺失的文件，不会覆盖已有文件。")
    else:
        print(f"🚀 初始化知识库: {root}")

    # === 创建目录结构 ===
    kb_dirs = [
        "01-requirements/_source",   # PRD 源文件存档
        "01-requirements",
        "02-api-docs/_source",       # Swagger/Postman 源文件存档
        "02-api-docs",
        "03-defects/_archived",
        "04-test-cases/functional",
        "04-test-cases/api",
        "04-test-cases/ui",
        "05-automation-scripts/api",
        "05-automation-scripts/ui",
    ]

    # 如果指定了模块，创建模块子目录
    if modules:
        for module in modules:
            kb_dirs.extend([
                f"01-requirements/{module}",
                f"02-api-docs/{module}",
                f"03-defects/{module}",
            ])

    for dir_rel in kb_dirs:
        (root / dir_rel).mkdir(parents=True, exist_ok=True)
        print(f"  📁 目录: {root / dir_rel}")

    # === 创建基础文件 ===

    # _glossary.md
    create_file(root / "_glossary.md", f"""# 业务术语表

## 术语定义

| 术语 | 英文/别名 | 定义 | 使用场景 |
|------|-----------|------|---------|
| Token | 访问令牌 | 用户认证后颁发的令牌 | 接口鉴权 |

## 缩写说明

| 缩写 | 全称 | 说明 |
|------|------|------|
| API | Application Programming Interface | 应用程序编程接口 |
| UI | User Interface | 用户界面 |

## 初始化信息

- 创建日期: {today}
- 请根据实际业务补充术语定义
""")

    # _architecture.md
    create_file(root / "_architecture.md", f"""# 系统架构说明

> 请根据实际项目补充架构信息。

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | - | - |
| 后端 | - | - |
| 数据库 | - | - |
| 部署 | - | - |

## 模块依赖关系

| 模块 | 上游依赖 | 下游被依赖 |
|------|---------|-----------|
| - | - | - |

## 环境说明

| 环境 | 域名 | 说明 |
|------|------|------|
| dev | - | 开发环境 |
| test | - | 测试环境 |
| staging | - | 预发布环境 |
| prod | - | 生产环境 |

## 初始化信息

- 创建日期: {today}
""")

    # _upgrade_log.md
    create_file(root / "_upgrade_log.md", f"""# 知识库变更日志

| 日期 | 操作 | 内容 | 操作人 |
|------|------|------|--------|
| {today} | 初始化 | 创建知识库 | - |
""")

    # _index.md（全局索引）
    create_file(root / "_index.md", f"""# 知识库全局索引

> 此文件由 `scripts/update_index.py` 自动维护

## 模块概览

| 模块 | 需求数 | 接口数 | 缺陷数 | 说明 |
|------|--------|--------|--------|------|
| _(暂无)_ | 0 | 0 | 0 | - |

## 初始化信息

- 创建日期: {today}
- 知识库根目录: {root}
- 模块:{' ' + ', '.join(modules) if modules else ' 暂无模块'}
""")

    # 如果指定了模块，创建模块概述文件
    if modules:
        for module in modules:
            for area in ["01-requirements", "02-api-docs", "03-defects"]:
                create_file(
                    root / area / module / "_overview.md",
                    f"""# {module} 模块概览

## 模块职责
[请描述本模块的业务职责]

## 核心功能
- [功能1]
- [功能2]

## 维护记录
| 日期 | 操作 | 说明 |
|------|------|------|
| {today} | 初始化 | 创建模块 |
""",
                )

    print(f"\n✅ 知识库初始化完成!")
    print(f"   📂 根目录: {root}")
    print(f"\n下一步: 运行 python3 scripts/update_index.py <项目根目录> 生成索引")
    print(f"       开始填充需求文档、接口文档和历史缺陷")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初始化业务知识库")
    parser.add_argument("project_root", help="项目根目录路径")
    parser.add_argument(
        "--module",
        nargs="+",
        default=None,
        help="功能模块列表，如 user-auth payment order",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.project_root):
        print(f"❌ 错误: 目录不存在: {args.project_root}")
        sys.exit(1)

    init_knowledge_base(args.project_root, args.module)
