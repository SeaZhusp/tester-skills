# 知识库对外接口规范（其他 Skill 使用指南）

本文档定义知识库的结构化数据接口，供其他 Skill（如功能测试用例生成、接口自动化、UI 自动化等）使用。任何 Skill 只需遵循本规范即可读取和使用知识库中的数据。

## 一、知识库的核心契约

知识库本质上是**按约定组织的 Markdown 文件集合**，所有 Skill 都可以通过文件系统直接读取。关键契约如下：

### 目录结构契约

```
knowledge-base/
├── _index.md                        # 全局索引：模块概览 + 文档数量统计
├── _glossary.md                     # 业务术语表
├── _architecture.md                 # 系统架构说明
├── 01-requirements/                 # 需求文档
│   ├── _module-index.md             # 需求模块索引（含ID/标题/版本/关联关系）
│   └── {module}/
│       ├── _overview.md             # 模块概述
│       └── REQ-*.md                 # 单个需求文档
├── 02-api-docs/                     # 接口文档
│   ├── _module-index.md             # 接口模块索引
│   └── {module}/
│       ├── _overview.md
│       └── API-*.md                 # 单个接口文档
├── 03-defects/                      # 缺陷库
│   ├── _module-index.md
│   ├── _stats.md                    # 缺陷统计分析
│   └── {module}/
│       ├── _overview.md
│       └── BUG-*.md                 # 单个缺陷记录
├── 04-test-cases/                   # 【输出】测试用例
└── 05-automation-scripts/           # 【输出】自动化脚本
```

### 通用 frontmatter 字段（所有文档都可用）

| 字段 | 说明 | 可用于 |
|------|------|--------|
| `id` | 文档唯一标识 | 索引、关联、引用 |
| `title` | 文档标题 | 显示、搜索 |
| `module` | 所属模块 | 分组、过滤 |
| `version` | 版本号 | 版本管理 |
| `status` | 状态: draft/approved/deprecated | 过滤有效文档 |
| `tags` | 标签数组 | 搜索、聚类 |
| `priority` 或 `severity` | 优先级/严重程度 | 测试排序 |
| `related_requirements` | 关联需求 ID 列表 | 需求追踪 |
| `related_apis` | 关联接口 ID 列表 | 接口追踪 |
| `related_bugs` | 关联缺陷 ID 列表 | 缺陷回溯 |

## 二、知识库查询方法

### 方法 1：通过索引文件快速定位

索引文件提供了文档的完整列表和关联关系：

| 索引文件 | 内容 | 适合场景 |
|---------|------|---------|
| `_index.md` | 所有模块概览 + 文档数量 + 最近更新 | 了解全局 |
| `01-requirements/_module-index.md` | 所有需求的 ID/标题/版本/状态/关联 | 找需求 |
| `02-api-docs/_module-index.md` | 所有接口的 ID/标题/方法/路径/关联 | 找接口 |
| `03-defects/_module-index.md` | 所有缺陷的 ID/标题/严重程度/关联 | 找缺陷 |
| `{module}/_module-index.md` | 单个模块的文档列表 | 聚焦模块 |
| `03-defects/_stats.md` | 缺陷统计分析（按严重程度/root_cause） | 风险分析 |

### 方法 2：按文档关联关系遍历

```
需求(REQ-001) → related_apis → [API-auth_login, API-auth_refresh]
需求(REQ-001) → related_bugs → [BUG-001]
接口(API-auth_login) → related_requirements → [REQ-001]
缺陷(BUG-001) → related_requirements → [REQ-001]
缺陷(BUG-001) → related_apis → [API-auth_login]
```

**遍历示例**：生成"用户登录"功能的测试用例时：
1. 从 `_index.md` 找到 `user-auth` 模块
2. 读取 `01-requirements/user-auth/REQ-001_用户登录功能.md` 获取业务流程和规则
3. 从 REQ-001 的 `related_apis` 找到 `API-auth_login`，读取接口文档获取请求/响应/错误码
4. 从 REQ-001 的 `related_bugs` 找到 `BUG-001`，读取缺陷详情了解历史问题
5. 综合以上信息生成测试用例

### 方法 3：脚本查询方式

```python
# scripts/query_kb.py - 供其他 Skill 调用的知识库查询接口

import os
import re
from pathlib import Path
from typing import Any

class KnowledgeBase:
    """知识库查询接口"""
    
    def __init__(self, project_root: str):
        self.kb_root = Path(project_root) / "knowledge-base"
    
    def get_module_list(self) -> list[str]:
        """获取所有模块列表"""
        req_dir = self.kb_root / "01-requirements"
        return sorted([d.name for d in req_dir.iterdir() 
                      if d.is_dir() and not d.name.startswith("_")])
    
    def get_requirements_by_module(self, module: str) -> list[dict]:
        """获取指定模块的所有需求文档"""
        module_dir = self.kb_root / "01-requirements" / module
        return self._scan_docs(module_dir, "REQ-*.md")
    
    def get_apis_by_module(self, module: str) -> list[dict]:
        """获取指定模块的所有接口文档"""
        module_dir = self.kb_root / "02-api-docs" / module
        return self._scan_docs(module_dir, "API-*.md")
    
    def get_defects_by_module(self, module: str) -> list[dict]:
        """获取指定模块的所有缺陷记录"""
        module_dir = self.kb_root / "03-defects" / module
        return self._scan_docs(module_dir, "BUG-*.md")
    
    def get_requirement(self, req_id: str) -> dict | None:
        """按 ID 获取单个需求文档"""
        return self._find_doc_by_id("01-requirements", req_id)
    
    def get_api(self, api_id: str) -> dict | None:
        """按 ID 获取单个接口文档"""
        return self._find_doc_by_id("02-api-docs", api_id)
    
    def get_defect(self, bug_id: str) -> dict | None:
        """按 ID 获取单个缺陷记录"""
        return self._find_doc_by_id("03-defects", bug_id)
    
    def get_related_docs(self, doc_id: str) -> dict:
        """获取与指定文档关联的所有文档（综合查询）"""
        # 先找到文档本身
        doc = (self.get_requirement(doc_id) or 
               self.get_api(doc_id) or 
               self.get_defect(doc_id))
        if not doc:
            return {"source": None, "related": {}}
        
        meta = doc["meta"]
        result = {"source": doc, "related": {"requirements": [], "apis": [], "defects": []}}
        
        for req_id in meta.get("related_requirements", []):
            r = self.get_requirement(req_id)
            if r: result["related"]["requirements"].append(r)
        
        for api_id in meta.get("related_apis", []):
            a = self.get_api(api_id)
            if a: result["related"]["apis"].append(a)
        
        for bug_id in meta.get("related_bugs", []):
            b = self.get_defect(bug_id)
            if b: result["related"]["defects"].append(b)
        
        return result
    
    def search_by_tags(self, tags: list[str]) -> dict:
        """按标签搜索所有相关文档"""
        results = {"requirements": [], "apis": [], "defects": []}
        for area in ["01-requirements", "02-api-docs", "03-defects"]:
            area_dir = self.kb_root / area
            for md_file in area_dir.rglob("*.md"):
                if md_file.name.startswith("_"):
                    continue
                meta = self._parse_frontmatter(md_file)
                doc_tags = meta.get("tags", [])
                if any(t in doc_tags for t in tags):
                    key = {"01-requirements": "requirements",
                           "02-api-docs": "apis",
                           "03-defects": "defects"}.get(area, "other")
                    results[key].append({
                        "id": meta.get("id", md_file.stem),
                        "title": meta.get("title", md_file.stem),
                        "filepath": str(md_file.relative_to(self.kb_root)),
                        "meta": meta,
                    })
        return results
    
    def _scan_docs(self, directory: Path, pattern: str) -> list[dict]:
        """扫描目录下的文档"""
        docs = []
        if not directory.exists():
            return docs
        for f in sorted(directory.glob(pattern)):
            if f.name.startswith("_"):
                continue
            meta = self._parse_frontmatter(f)
            docs.append({
                "id": meta.get("id", f.stem),
                "title": meta.get("title", f.stem),
                "filepath": str(f.relative_to(self.kb_root)),
                "content": f.read_text(encoding="utf-8"),
                "meta": meta,
            })
        return docs
    
    def _find_doc_by_id(self, area: str, doc_id: str) -> dict | None:
        """按 ID 查找文档"""
        area_dir = self.kb_root / area
        for f in area_dir.rglob("*.md"):
            if f.name.startswith("_"):
                continue
            meta = self._parse_frontmatter(f)
            if meta.get("id") == doc_id:
                return {
                    "id": doc_id,
                    "title": meta.get("title", f.stem),
                    "filepath": str(f.relative_to(self.kb_root)),
                    "content": f.read_text(encoding="utf-8"),
                    "meta": meta,
                }
        return None
    
    def _parse_frontmatter(self, filepath: Path) -> dict:
        """解析 frontmatter"""
        content = filepath.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return {}
        # 这里省略详细的 YAML 解析，实际使用 update_index.py 中的解析逻辑
        return self._simple_yaml_parse(match.group(1))
    
    def _simple_yaml_parse(self, yaml_text: str) -> dict:
        """简化 YAML 解析"""
        import json
        data = {}
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
                    if value.lower() == "true": data[key] = True
                    elif value.lower() == "false": data[key] = False
                    elif value.isdigit(): data[key] = int(value)
                    elif value.startswith("["):
                        items = [v.strip().strip("'\"") 
                                for v in value[1:-1].split(",") if v.strip()]
                        data[key] = items
                    else: data[key] = value.strip("\"'")
        return data
```

## 三、其他 Skill 的使用示例

### 场景1：功能测试用例生成 Skill 的使用方式

```
1. 项目根目录已知 → 找到 knowledge-base/
2. 读取 _index.md → 了解有哪些模块和文档
3. 定位目标模块（如 user-auth）
4. 读取 01-requirements/user-auth/_module-index.md → 获取需求清单
5. 读取 REQ-001.md → 获取业务流程、规则、验收标准
6. 从 REQ-001 的 related_apis → 读取 API-auth_login.md → 获取错误码
7. 从 REQ-001 的 related_bugs → 读取 BUG-001.md → 获取历史缺陷详情
8. 综合信息生成测试用例，输出到 04-test-cases/functional/
```

### 场景2：接口自动化脚本生成 Skill 的使用方式

```
1. 读取 02-api-docs/{module}/_module-index.md → 获取接口清单
2. 读取 API-auth_login.md → 提取 method/path/参数/错误码/响应结构
3. 按接口文档的请求参数字段表生成参数化测试数据
4. 按错误码表生成异常场景测试
5. 按业务逻辑说明补充场景测试
6. 输出到 05-automation-scripts/api/
```

### 场景3：UI 自动化脚本生成 Skill 的使用方式

```
1. 读取 01-requirements/{module}/_module-index.md → 获取需求清单
2. 读取 REQ-001.md → 提取业务流程、操作步骤
3. 读取 02-api-docs/{module}/关联API → 了解需要模拟的数据
4. 读取 03-defects/{module}/关联BUG → 增加回归场景
5. 输出到 05-automation-scripts/ui/
```

## 四、集成建议

### 在 SKILL.md 中引用知识库

其他 Skill 的 SKILL.md 中应包含类似以下描述，让 CodeBuddy 知道如何利用知识库：

```markdown
## 前置依赖

本 Skill 依赖于 `knowledge-base-manager` 管理的业务知识库。
知识库位于项目根目录的 `knowledge-base/` 目录下。

## 数据来源说明

生成测试用例前，按以下顺序读取知识库数据：
1. `knowledge-base/_index.md` - 了解模块概览
2. `knowledge-base/01-requirements/{module}/` - 读取需求文档
3. `knowledge-base/02-api-docs/{module}/` - 读取接口文档（按需求关联关系）
4. `knowledge-base/03-defects/{module}/` - 读取历史缺陷（按需求关联关系）

## 知识库查询接口

可直接调用 `scripts/query_kb.py` 的 `KnowledgeBase` 类进行程序化查询。
```

### 在 SKILL.md 的触发词中说明

```yaml
---
name: testcase-generator
description: 根据知识库中的需求文档生成功能测试用例的 Skill。
  依赖 knowledge-base-manager 维护的 knowledge-base/ 目录。
  触发：当用户说"根据知识库生成测试用例"、"为 user-auth 模块生成测试用例"、
  "基于 REQ-001 生成测试用例"、"为登录功能写测试用例"等。
---
```
