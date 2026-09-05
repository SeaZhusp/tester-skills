#!/usr/bin/env python3
"""
Swagger/OpenAPI 接口文档导入脚本
将 Swagger 2.0 / OpenAPI 3.x JSON/YAML 文件解析后生成结构化的 API 文档。

用法:
  python3 import_swagger.py <项目根目录> <swagger文件路径>

示例:
  python3 import_swagger.py /path/to/project swagger.json
  python3 import_swagger.py /path/to/project openapi_v3.yaml
"""

import sys
import os
import json
import re
import shutil
import argparse
from datetime import date
from pathlib import Path
from typing import Any


def load_spec(filepath: str) -> dict:
    """加载 Swagger/OpenAPI 规格文件（支持 JSON 和 YAML）"""
    path = Path(filepath)
    content = path.read_text(encoding="utf-8")

    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
            spec = yaml.safe_load(content)
        except ImportError:
            print("⚠️  PyYAML 未安装，尝试用 JSON 解析...")
            # YAML 是 JSON 的超集，极端情况下尝试 JSON 解析
            try:
                # 尝试修复常见的 YAML→JSON 差异
                import json
                spec = json.loads(content)
            except json.JSONDecodeError:
                print("❌ 需要 PyYAML 库来解析 YAML 文件，运行: pip install pyyaml")
                sys.exit(1)
    else:
        spec = json.loads(content)

    return spec


def detect_spec_version(spec: dict) -> tuple[str, str]:
    """检测规格版本，返回 (版本名, 友好名称)"""
    if "swagger" in spec:
        return ("swagger", f"Swagger {spec['swagger']}")
    elif "openapi" in spec:
        return ("openapi3", f"OpenAPI {spec['openapi']}")
    else:
        print("⚠️  无法识别规格版本，按 OpenAPI 3.x 处理")
        return ("openapi3", "OpenAPI unknown")


def resolve_ref(ref: str, spec: dict) -> dict | None:
    """解析 $ref 引用"""
    if not ref.startswith("#/"):
        return None

    parts = ref[2:].split("/")
    current = spec
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def resolve_schema(schema: dict, spec: dict, visited: set | None = None) -> dict:
    """递归解析 schema，展开 $ref"""
    if visited is None:
        visited = set()

    if not schema:
        return {}

    result = {}

    # 处理 $ref
    if "$ref" in schema:
        ref_id = schema["$ref"]
        if ref_id in visited:
            return {"type": "object", "description": f"[循环引用: {ref_id}]"}
        visited.add(ref_id)
        resolved = resolve_ref(ref_id, spec)
        if resolved:
            return resolve_schema(resolved, spec, visited)
        return {"type": "object", "description": f"[未解析的引用: {ref_id}]"}

    # 复制基本字段
    for key in ("type", "description", "example", "format", "minimum", "maximum",
                 "minLength", "maxLength", "minItems", "maxItems", "enum", "default"):
        if key in schema:
            result[key] = schema[key]

    # 处理 properties
    if "properties" in schema:
        result["properties"] = {}
        for prop_name, prop_schema in schema["properties"].items():
            result["properties"][prop_name] = resolve_schema(prop_schema, spec, visited)

    # 处理 items (array)
    if "items" in schema:
        result["items"] = resolve_schema(schema["items"], spec, visited)

    # 处理 allOf/oneOf/anyOf
    for key in ("allOf", "oneOf", "anyOf"):
        if key in schema:
            result[key] = [resolve_schema(s, spec, visited) for s in schema[key]]

    # 处理 required
    if "required" in schema:
        result["required"] = schema["required"]

    return result


def schema_to_field_table(schema: dict, required_list: list[str] | None = None) -> list[dict]:
    """将 schema properties 转换为字段表格行"""
    fields = []
    properties = schema.get("properties", {})

    for field_name, field_schema in properties.items():
        field_type = field_schema.get("type", "string")
        is_required = field_name in (required_list or [])
        constraints = _build_constraints(field_schema)
        example = field_schema.get("example", field_schema.get("default", ""))
        description = field_schema.get("description", "")

        fields.append({
            "field": field_name,
            "type": field_type,
            "required": "是" if is_required else "否",
            "constraints": constraints,
            "example": _format_example(example),
            "description": description,
        })

    return fields


def _build_constraints(schema: dict) -> str:
    """从 schema 构建约束描述"""
    parts = []
    if "minLength" in schema and "maxLength" in schema:
        parts.append(f"{schema['minLength']}-{schema['maxLength']}位")
    elif "minLength" in schema:
        parts.append(f"最少{schema['minLength']}位")
    elif "maxLength" in schema:
        parts.append(f"最多{schema['maxLength']}位")
    if "minimum" in schema and "maximum" in schema:
        parts.append(f"{schema['minimum']}-{schema['maximum']}")
    if "enum" in schema:
        parts.append(f"枚举: {', '.join(str(e) for e in schema['enum'])}")
    if "format" in schema:
        parts.append(f"格式: {schema['format']}")
    if "pattern" in schema:
        parts.append(f"正则: {schema['pattern']}")
    return "; ".join(parts) if parts else "-"


def _format_example(example: Any) -> str:
    """格式化示例值"""
    if example is None or example == "":
        return "-"
    if isinstance(example, str):
        return f'"{example}"'
    return str(example)


def extract_parameters(path_item: dict, spec: dict) -> list[dict]:
    """提取 path item 的参数"""
    params = []

    for param in path_item.get("parameters", []):
        param_schema = resolve_schema(param.get("schema", param), spec)
        param_in = param.get("in", "query")
        field_name = f"{param.get('name', '')} ({param_in})"
        constraints = _build_constraints(param_schema)

        params.append({
            "field": field_name,
            "type": param_schema.get("type", "string"),
            "required": "是" if param.get("required", False) else "否",
            "constraints": constraints,
            "example": _format_example(param_schema.get("example", param.get("example", ""))),
            "description": param.get("description", ""),
        })

    return params


def extract_request_body(method_item: dict, spec: dict) -> tuple[list[dict] | None, str | None]:
    """提取请求体定义（OpenAPI 3.x）"""
    request_body = method_item.get("requestBody")
    if not request_body:
        return None, None

    content = request_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = resolve_schema(json_content.get("schema", {}), spec)

    required_list = schema.get("required", [])
    fields = schema_to_field_table(schema, required_list) if schema.get("properties") else None

    # 生成示例 JSON
    example_json = _generate_example_json(schema)

    return fields, json.dumps(example_json, ensure_ascii=False, indent=2) if example_json else None


def extract_error_codes(responses: dict, spec: dict) -> list[dict]:
    """提取错误码表"""
    error_codes = []

    for status_code, response in responses.items():
        status_int = int(status_code) if status_code.isdigit() else 0
        if 200 <= status_int < 300:
            continue  # 跳过成功响应

        # 尝试从 response schema 中提取业务 code
        content = response.get("content", {})
        json_content = content.get("application/json", {})

        # Swagger 2.0 方式: response.schema
        schema = json_content.get("schema", response.get("schema", {}))
        schema = resolve_schema(schema, spec)

        # 如果 schema 中有 code 字段，提取
        code_value = "-"
        if schema.get("properties") and "code" in schema["properties"]:
            code_schema = schema["properties"]["code"]
            if "example" in code_schema:
                code_value = str(code_schema["example"])
            elif "enum" in code_schema:
                code_value = ", ".join(str(e) for e in code_schema["enum"])

        message = response.get("description", "")

        # 从 schema 中提取更详细的 message
        if schema.get("properties") and "message" in schema["properties"]:
            msg_schema = schema["properties"]["message"]
            if "example" in msg_schema:
                message = msg_schema["example"]

        error_codes.append({
            "code": status_code,
            "message": message,
            "condition": f"HTTP {status_code}",
        })

    return error_codes


def _generate_example_json(schema: dict) -> Any:
    """根据 schema 生成示例 JSON"""
    if not schema:
        return None

    schema_type = schema.get("type", "object")

    if schema_type == "object":
        result = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            result[prop_name] = _generate_example_json(prop_schema)
        return result

    elif schema_type == "array":
        items = schema.get("items", {})
        return [_generate_example_json(items)]

    elif schema_type == "string":
        if "example" in schema:
            return schema["example"]
        if "enum" in schema:
            return schema["enum"][0]
        return "string"

    elif schema_type == "integer" or schema_type == "number":
        if "example" in schema:
            return schema["example"]
        if "minimum" in schema:
            return schema["minimum"]
        return 0

    elif schema_type == "boolean":
        return True

    return None


def generate_api_doc(api_id: str, title: str, method: str, path: str,
                     module: str, spec: dict, path_item: dict,
                     method_item: dict, source_file: str, spec_version: str) -> str:
    """生成单个 API 的 Markdown 文档"""
    today = date.today().isoformat()

    # 提取参数
    params = extract_parameters(path_item, spec)
    method_params = extract_parameters(method_item, spec)
    all_params = params + [p for p in method_params if p not in params]

    # 提取请求体
    req_fields, req_example = extract_request_body(method_item, spec)

    # 提取错误码
    responses = method_item.get("responses", {})
    error_codes = extract_error_codes(responses, spec)

    # 构建文档内容
    lines = [
        "---",
        f"id: {api_id}",
        f"title: {title}",
        f"module: {module}",
        "version: 1.0",
        f"method: {method.upper()}",
        f"path: {path}",
        "content_type: application/json",
        f"source: {source_file}",
        f"source_type: {spec_version}",
        "auth_required: true" if "security" in method_item or "security" in spec else "auth_required: false",
        f"tags: [{module}]",
        "---",
        "",
        f"# {title}",
        "",
        "## 1. 接口描述",
        "",
        method_item.get("description", method_item.get("summary", "")),
        "",
        "## 2. 请求说明",
        "",
        f"### 请求地址",
        "",
        f"`{method.upper()} {path}`",
        "",
    ]

    # 请求头
    if any(p.get("in") == "header" for p in path_item.get("parameters", [])) or \
       any(p.get("in") == "header" for p in method_item.get("parameters", [])):
        lines.extend([
            "### 请求头",
            "",
            "| 参数名 | 必填 | 说明 |",
            "|--------|------|------|",
            "| Content-Type | 是 | application/json |",
            "",
        ])

    # 请求参数
    if all_params:
        lines.extend([
            "### 请求参数",
            "",
            "| 字段 | 类型 | 必填 | 约束 | 示例 | 说明 |",
            "|------|------|------|------|------|------|",
        ])
        for p in all_params:
            lines.append(
                f"| {p['field']} | {p['type']} | {p['required']} | {p['constraints']} | {p['example']} | {p['description']} |"
            )
        lines.append("")

    # 请求体
    if req_fields:
        lines.extend([
            "### 请求体",
            "",
        ])
        if req_example:
            lines.extend([
                "```json",
                req_example,
                "```",
                "",
            ])
        lines.extend([
            "| 字段 | 类型 | 必填 | 约束 | 示例 | 说明 |",
            "|------|------|------|------|------|------|",
        ])
        for f in req_fields:
            lines.append(
                f"| {f['field']} | {f['type']} | {f['required']} | {f['constraints']} | {f['example']} | {f['description']} |"
            )
        lines.append("")

    # 成功响应
    success_response = None
    for code in ("200", "201", "default"):
        if code in responses:
            success_response = responses[code]
            break
    if success_response:
        content = success_response.get("content", {})
        json_content = content.get("application/json", {})
        schema = resolve_schema(json_content.get("schema", success_response.get("schema", {})), spec)

        lines.extend([
            "### 成功响应",
            "",
            f"**HTTP 状态码**: `{code} OK`",
            "",
        ])

        example = _generate_example_json(schema)
        if example:
            lines.extend([
                "```json",
                json.dumps(example, ensure_ascii=False, indent=2),
                "```",
                "",
            ])

        # 响应字段说明
        if schema.get("properties"):
            res_fields = schema_to_field_table(schema, schema.get("required", []))
            lines.extend([
                "### 响应字段说明",
                "",
                "| 字段 | 类型 | 说明 |",
                "|------|------|------|",
            ])
            for f in res_fields:
                lines.append(f"| {f['field']} | {f['type']} | {f['description']} |")
            lines.append("")

    # 错误码
    if error_codes:
        lines.extend([
            "### 错误响应",
            "",
            "| HTTP 状态码 | 说明 |",
            "|-------------|------|",
        ])
        for ec in error_codes:
            lines.append(f"| {ec['code']} | {ec['message']} |")
        lines.append("")

    # 变更历史
    lines.extend([
        "### 变更历史",
        "",
        "| 版本 | 日期 | 变更人 | 变更内容 |",
        "|------|------|--------|---------|",
        f"| v1.0 | {today} | import | 从 {source_file} 自动导入 |",
        "",
    ])

    return "\n".join(lines)


def generate_module_overview(module: str, api_ids: list[str], source_file: str) -> str:
    """生成模块概述 _overview.md"""
    today = date.today().isoformat()
    api_lines = "\n".join(f"- `{aid}`" for aid in api_ids)
    return f"""# {module} 模块

## 模块职责
[从 Swagger/OpenAPI 导入的接口模块]

## 接口列表
{api_lines}

## 维护记录
| 日期 | 操作 | 说明 |
|------|------|------|
| {today} | 导入 | 从 {source_file} 导入 |
"""


def import_swagger(project_root: str, filepath: str):
    """主导入函数"""
    spec_path = Path(filepath)
    if not spec_path.exists():
        print(f"❌ 文件不存在: {filepath}")
        return

    # 加载规格
    print(f"🚀 加载规范文件: {spec_path}")
    spec = load_spec(filepath)
    spec_type, spec_name = detect_spec_version(spec)
    print(f"   检测到: {spec_name}")

    # 保存源文件
    kb_source_dir = Path(project_root) / "knowledge-base" / "02-api-docs" / "_source"
    kb_source_dir.mkdir(parents=True, exist_ok=True)
    dest_file = kb_source_dir / spec_path.name
    shutil.copy2(spec_path, dest_file)
    print(f"   ✅ 源文件已保存: {dest_file}")

    # 提取基础信息
    info = spec.get("info", {})
    base_path = spec.get("basePath", "")
    if spec_type == "openapi3":
        servers = spec.get("servers", [{"url": ""}])
        base_path = servers[0].get("url", "") if servers else ""

    paths = spec.get("paths", {})
    tags = spec.get("tags", [])
    tag_names = [t.get("name", "") for t in tags] if tags else []

    print(f"   信息: {info.get('title', '')} v{info.get('version', '')}")
    print(f"   路径总数: {len(paths)}")
    print(f"   Tags: {', '.join(tag_names) if tag_names else '无'}")

    # 按 tag 分组缓存 API 文档内容
    module_apis: dict[str, list[tuple[str, str]]] = {}  # module -> [(api_id, content)]
    module_title_map: dict[str, str] = {}

    # 遍历所有接口
    for path, path_item in paths.items():
        for method in ("get", "post", "put", "delete", "patch", "head", "options"):
            if method not in path_item:
                continue

            method_item = path_item[method]

            # 确定模块：优先用 tags[0]
            api_tags = method_item.get("tags", tag_names)
            module = api_tags[0] if api_tags else "default"

            # 生成友好的 API 名称
            operation_id = method_item.get("operationId", "")
            summary = method_item.get("summary", "") or operation_id or path.strip("/").split("/")[-1]

            if operation_id:
                api_id = f"API-{module}_{operation_id}"
            else:
                short_path = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
                api_id = f"API-{module}_{method}_{short_path}"

            # 生成文档
            content = generate_api_doc(
                api_id=api_id,
                title=summary,
                method=method,
                path=path,
                module=module,
                spec=spec,
                path_item=path_item,
                method_item=method_item,
                source_file=spec_path.name,
                spec_version=spec_type,
            )

            if module not in module_apis:
                module_apis[module] = []
                module_title_map[module] = module

            module_apis[module].append((api_id, content))
            module_title_map[module] = summary

    # 写入知识库
    total_apis = 0
    for module, apis in sorted(module_apis.items()):
        module_dir = Path(project_root) / "knowledge-base" / "02-api-docs" / module
        module_dir.mkdir(parents=True, exist_ok=True)

        # 创建 _overview.md（如不存在）
        overview_path = module_dir / "_overview.md"
        if not overview_path.exists():
            api_ids = [aid for aid, _ in apis]
            overview_path.write_text(
                generate_module_overview(module, api_ids, spec_path.name),
                encoding="utf-8",
            )
            print(f"   📝 创建模块概述: {overview_path}")

        # 写入每个 API 文档
        for api_id, content in apis:
            api_path = module_dir / f"{api_id}.md"
            api_path.write_text(content, encoding="utf-8")
            print(f"   ✅ {api_id}.md")
            total_apis += 1

    # 更新 _upgrade_log.md
    today = date.today().isoformat()
    log_path = Path(project_root) / "knowledge-base" / "_upgrade_log.md"
    if log_path.exists():
        log_content = log_path.read_text(encoding="utf-8")
    else:
        log_content = "# 知识库变更日志\n\n| 日期 | 操作 | 内容 | 操作人 |\n|------|------|------|--------|\n"

    new_log = f"| {today} | 导入API | 从 {spec_path.name} 导入 {total_apis} 个接口 | import |\n"
    log_path.write_text(log_content + new_log, encoding="utf-8")

    # 更新索引
    print(f"\n📊 导入统计:")
    print(f"   源文件: {spec_path.name} ({spec_name})")
    print(f"   模块数: {len(module_apis)}")
    print(f"   接口数: {total_apis}")
    for module, apis in sorted(module_apis.items()):
        print(f"     - {module}: {len(apis)} 个接口")
    print(f"\n✅ Swagger/OpenAPI 导入完成！")
    print(f"   下一步: 运行 python3 scripts/update_index.py {project_root} 更新索引")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入 Swagger/OpenAPI 规格到知识库")
    parser.add_argument("project_root", help="项目根目录路径")
    parser.add_argument("spec_file", help="Swagger/OpenAPI 文件路径（JSON/YAML）")
    args = parser.parse_args()

    if not os.path.isdir(args.project_root):
        print(f"❌ 项目目录不存在: {args.project_root}")
        sys.exit(1)

    if not os.path.isfile(args.spec_file):
        print(f"❌ 规格文件不存在: {args.spec_file}")
        sys.exit(1)

    import_swagger(args.project_root, args.spec_file)
