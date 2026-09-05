#!/usr/bin/env python3
"""
知识库索引更新脚本
扫描 knowledge-base 目录，读取所有文档的 frontmatter，重建索引文件。

用法:
  python3 update_index.py <项目根目录>
"""

import sys
import os
import re
import argparse
from pathlib import Path
from datetime import date
from typing import Any


def parse_frontmatter(filepath: Path) -> dict[str, Any]:
    """解析 Markdown 文件的 YAML frontmatter"""
    content = filepath.read_text(encoding="utf-8")
    # 匹配 --- 之间的 YAML
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}

    yaml_text = match.group(1)
    data = {}

    # 简单 YAML 解析（不依赖 PyYAML，保持轻量）
    list_pattern = re.compile(r"^\s*-\s+(.+)$")
    current_key = None
    current_list = None

    for line in yaml_text.split("\n"):
        list_match = list_pattern.match(line)

        if list_match and current_key and current_list is not None:
            current_list.append(list_match.group(1).strip())
            continue

        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()

            if not value:
                current_key = key
                current_list = []
                data[key] = current_list
            else:
                current_key = None
                current_list = None
                # 尝试转换类型
                if value.lower() == "true":
                    data[key] = True
                elif value.lower() == "false":
                    data[key] = False
                elif value.isdigit():
                    data[key] = int(value)
                elif value.startswith("[") and value.endswith("]"):
                    items = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
                    data[key] = items
                else:
                    data[key] = value.strip("\"'")

    return data


def scan_documents(kb_root: Path, area_prefix: str, file_pattern: str) -> list[dict]:
    """扫描指定区域下的文档"""
    area_dir = kb_root / area_prefix
    if not area_dir.exists():
        return []

    docs = []
    for filepath in sorted(area_dir.rglob(file_pattern)):
        if filepath.name.startswith("_"):
            continue
        if "_archived" in str(filepath):
            continue

        meta = parse_frontmatter(filepath)
        docs.append({
            "filepath": filepath.relative_to(kb_root),
            "meta": meta,
        })
    return docs


def get_module_from_path(filepath: Path, area: str) -> str:
    """从文件路径提取模块名"""
    parts = str(filepath).split("/")
    try:
        area_index = parts.index(area)
        if area_index + 1 < len(parts):
            return parts[area_index + 1]
    except ValueError:
        pass
    return "unknown"


def update_index(kb_root_str: str):
    """更新知识库索引"""
    kb_root = Path(kb_root_str)
    if not kb_root.exists() or not kb_root.is_dir():
        print(f"❌ 错误: 知识库目录不存在: {kb_root}")
        return

    today = date.today().isoformat()

    # 扫描各区域
    areas = {
        "01-requirements": "REQ-*.md",
        "02-api-docs": "API-*.md",
        "03-defects": "BUG-*.md",
    }

    all_docs = {}
    for area, pattern in areas.items():
        docs = scan_documents(kb_root, area, pattern)
        all_docs[area] = docs
        print(f"  📄 {area}: {len(docs)} 个文档")

    # ========== 构建模块维度数据 ==========
    modules_map: dict[str, dict] = {}

    for area, docs in all_docs.items():
        for doc in docs:
            module = doc["meta"].get("module", get_module_from_path(doc["filepath"], area.split("/")[0]))
            if module not in modules_map:
                modules_map[module] = {"requirements": [], "api_docs": [], "defects": []}

            area_key = {
                "01-requirements": "requirements",
                "02-api-docs": "api_docs",
                "03-defects": "defects",
            }.get(area, "other")

            modules_map[module][area_key].append(doc)

    # ========== 生成全局索引 _index.md ==========
    index_lines = [
        f"# 知识库全局索引",
        f"",
        f"> 自动生成时间: {today} | 请勿手动编辑",
        f"",
        f"## 模块概览",
        f"",
        f"| 模块 | 需求数 | 接口数 | 缺陷数 | 说明 |",
        f"|------|--------|--------|--------|------|",
    ]

    for module_name in sorted(modules_map.keys()):
        mod = modules_map[module_name]
        desc = "见模块索引"
        index_lines.append(
            f"| {module_name} | {len(mod['requirements'])} | {len(mod['api_docs'])} | {len(mod['defects'])} | {desc} |"
        )

    total_reqs = sum(len(m["requirements"]) for m in modules_map.values())
    total_apis = sum(len(m["api_docs"]) for m in modules_map.values())
    total_bugs = sum(len(m["defects"]) for m in modules_map.values())
    index_lines.extend([
        f"| **合计** | **{total_reqs}** | **{total_apis}** | **{total_bugs}** | - |",
        "",
        "## 最近更新",
        "",
    ])

    # 从变更日志获取最近的更新
    upgrade_log = kb_root / "_upgrade_log.md"
    if upgrade_log.exists():
        log_content = upgrade_log.read_text(encoding="utf-8")
        log_lines = log_content.strip().split("\n")
        recent_logs = [l for l in log_lines if "|" in l and "日期" not in l]
        for log_line in recent_logs[-10:]:  # 最近10条
            index_lines.append(log_line)

    (kb_root / "_index.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"  ✅ 更新全局索引: {kb_root / '_index.md'}")

    # ========== 生成模块级别索引 ==========
    for module_name, mod in modules_map.items():
        for area, area_prefix in [("01-requirements", "需求"), ("02-api-docs", "接口"), ("03-defects", "缺陷")]:
            docs = {
                "01-requirements": mod["requirements"],
                "02-api-docs": mod["api_docs"],
                "03-defects": mod["defects"],
            }.get(area, [])

            if not docs:
                continue

            # 找到该模块对应的目录
            area_dir = kb_root / area / module_name
            if not area_dir.exists():
                # 尝试在子目录下找
                for sub_dir in (kb_root / area).iterdir():
                    if sub_dir.is_dir() and sub_dir.name == module_name:
                        area_dir = sub_dir
                        break
                else:
                    continue

            module_index_path = area_dir / "_module-index.md"
            module_index_content = [
                f"# {module_name} - {area_prefix}文档索引",
                "",
                f"> 自动生成时间: {today} | 请勿手动编辑",
                "",
                f"| ID | 标题 | 版本 | 状态 | 优先级/严重程度 | 关联需求 | 关联接口/缺陷 |",
                f"|----|------|------|------|----------------|----------|---------------|",
            ]

            for doc in docs:
                m = doc["meta"]
                doc_id = m.get("id", doc["filepath"].stem)
                title = m.get("title", doc["filepath"].stem)
                version = m.get("version", "-")
                status = m.get("status", "-")
                priority = m.get("priority", m.get("severity", "-"))
                related_reqs = ",".join(m.get("related_requirements", [])) or "-"
                related_others = ",".join(
                    m.get("related_apis", []) + m.get("related_bugs", [])
                ) or "-"

                module_index_content.append(
                    f"| [{doc_id}]({doc['filepath']}) | {title} | {version} | {status} | {priority} | {related_reqs} | {related_others} |"
                )

            module_index_content.append("")
            module_index_path.write_text("\n".join(module_index_content) + "\n", encoding="utf-8")
            print(f"  ✅ 更新模块索引: {module_index_path}")

    # ========== 生成缺陷统计 _stats.md ==========
    defects = all_docs.get("03-defects", [])
    if defects:
        severity_count = {"critical": 0, "major": 0, "minor": 0, "trivial": 0}
        status_count = {}

        for d in defects:
            sev = d["meta"].get("severity", "unknown").lower()
            if sev in severity_count:
                severity_count[sev] += 1
            else:
                severity_count[sev] = 1

            st = d["meta"].get("status", "unknown")
            status_count[st] = status_count.get(st, 0) + 1

        # 按 root_cause 分析
        root_causes = {}
        for d in defects:
            rc = d["meta"].get("root_cause", "未知")
            root_causes[rc] = root_causes.get(rc, 0) + 1

        top_root_causes = sorted(root_causes.items(), key=lambda x: -x[1])[:10]

        stats_path = kb_root / "03-defects" / "_stats.md"
        stats_content = [
            f"# 缺陷统计分析",
            "",
            f"> 自动生成时间: {today}",
            "",
            "## 严重程度分布",
            "",
            "| 严重程度 | 数量 |",
            "|---------|------|",
        ]

        for sev, count in sorted(severity_count.items()):
            stats_content.append(f"| {sev} | {count} |")
        stats_content.extend([
            f"| **合计** | **{len(defects)}** |",
            "",
            "## 状态分布",
            "",
            "| 状态 | 数量 |",
            "|------|------|",
        ])
        for st, count in sorted(status_count.items()):
            stats_content.append(f"| {st} | {count} |")

        stats_content.extend([
            "",
            "## Top 根本原因",
            "",
            "| 根本原因 | 出现次数 |",
            "|---------|---------|",
        ])
        for rc, count in top_root_causes:
            stats_content.append(f"| {rc} | {count} |")

        stats_path.write_text("\n".join(stats_content) + "\n", encoding="utf-8")
        print(f"  ✅ 更新缺陷统计: {stats_path}")

    print(f"\n✅ 索引更新完成!")
    print(f"   📊 需求: {total_reqs} | 接口: {total_apis} | 缺陷: {total_bugs}")
    print(f"   📁 模块数: {len(modules_map)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="更新知识库索引")
    parser.add_argument("project_root", help="项目根目录路径")
    args = parser.parse_args()

    if not os.path.isdir(args.project_root):
        print(f"❌ 错误: 目录不存在: {args.project_root}")
        sys.exit(1)

    update_index(args.project_root)
