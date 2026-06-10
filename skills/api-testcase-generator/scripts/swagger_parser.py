#!/usr/bin/env python3
"""
Swagger/OpenAPI Parser
解析 Swagger JSON/YAML 文件，提取接口定义、模型与依赖关系。
"""

import json
import yaml
import re
import argparse
from urllib.parse import urlparse
from pathlib import Path


def load_spec(input_path):
    """加载 Swagger/OpenAPI 文件（JSON 或 YAML）"""
    path = Path(input_path)
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ('.yaml', '.yml'):
            return yaml.safe_load(f)
        return json.load(f)


def resolve_ref(spec, ref):
    """解析 $ref 引用"""
    if not ref.startswith('#/'):
        return {}
    parts = ref[2:].split('/')
    data = spec
    for part in parts:
        data = data.get(part, {})
    return data


def get_schema(spec, schema):
    """获取 Schema，自动解析 $ref"""
    if isinstance(schema, dict) and '$ref' in schema:
        return resolve_ref(spec, schema['$ref'])
    return schema or {}


def extract_parameters(spec, params):
    """提取参数定义"""
    result = []
    for p in params or []:
        if isinstance(p, dict) and '$ref' in p:
            p = resolve_ref(spec, p['$ref'])
        # OpenAPI 3.x 参数通过 schema 定义类型
        schema = p.get('schema', {})
        if isinstance(schema, dict) and '$ref' in schema:
            schema = resolve_ref(spec, schema['$ref'])
        param_type = schema.get('type', 'string') if schema else 'string'
        param = {
            'name': p.get('name'),
            'in': p.get('in'),  # query, path, header
            'required': p.get('required', False),
            'type': param_type,
            'description': p.get('description', ''),
            'schema': schema,
        }
        if 'enum' in p:
            param['enum'] = p['enum']
        if p.get('in') == 'header' and p.get('required'):
            param['auth_header'] = True
        result.append(param)
    return result


def extract_request_body(spec, request_body):
    """提取 OpenAPI 3.x requestBody"""
    if not request_body:
        return None
    if isinstance(request_body, dict) and '$ref' in request_body:
        request_body = resolve_ref(spec, request_body['$ref'])

    content = request_body.get('content', {})
    if not content:
        return None

    # 取第一个 content type
    content_type, body_def = next(iter(content.items()))
    body_schema = body_def.get('schema', {})
    if isinstance(body_schema, dict) and '$ref' in body_schema:
        body_schema = resolve_ref(spec, body_schema['$ref'])

    return {
        'content_type': content_type,
        'required': request_body.get('required', False),
        'schema': body_schema,
    }


def infer_id_field(schema):
    """从 Schema 推断 ID 字段名"""
    props = schema.get('properties', {})
    for name, prop in props.items():
        if name.lower() in ('id', 'uuid', 'userid', 'orderid', 'productid'):
            return name
    return None


def extract_responses(spec, responses):
    """提取响应定义，重点关注成功响应"""
    result = {}
    for code, resp in responses.items():
        if isinstance(resp, dict) and '$ref' in resp:
            resp = resolve_ref(spec, resp['$ref'])
        resp_data = {
            'description': resp.get('description', ''),
            'code': code,
        }
        if 'schema' in resp:
            schema = get_schema(spec, resp['schema'])
            resp_data['schema'] = schema
            resp_data['id_field'] = infer_id_field(schema)
        result[code] = resp_data
    return result


def parse_paths(spec):
    """解析所有接口路径"""
    paths = spec.get('paths', {})
    apis = []
    for path, methods in paths.items():
        for method, detail in methods.items():
            if method in ('parameters', 'summary', 'description'):
                continue
            # 安全：优先路径级 security，否则全局 security
            security = detail.get('security', spec.get('security', None))
            api = {
                'path': path,
                'method': method.upper(),
                'summary': detail.get('summary', ''),
                'description': detail.get('description', ''),
                'tags': detail.get('tags', []),
                'operation_id': detail.get('operationId', ''),
                'security': security,
                'consumes': detail.get('consumes', spec.get('consumes', [])),
                'produces': detail.get('produces', spec.get('produces', [])),
                'parameters': extract_parameters(spec, detail.get('parameters', [])),
                'request_body': extract_request_body(spec, detail.get('requestBody')),
                'responses': extract_responses(spec, detail.get('responses', {})),
            }
            # 提取路径参数名
            api['path_params'] = re.findall(r'\{(\w+)\}', path)
            # 提取可能的资源名（用于 CRUD/Create-Read-Update-Delete 识别）
            parts = [p for p in path.split('/') if p and not p.startswith('{')]
            api['resource'] = parts[-1] if parts else ''
            apis.append(api)
    return apis


def infer_dependencies(apis):
    """推断接口间的依赖关系"""
    deps = []
    # 建立资源创建接口索引
    creators = {}
    for api in apis:
        if api['method'] == 'POST' and not api['path_params']:
            creators[api['resource']] = api

    for api in apis:
        # GET/PUT/PATCH/DELETE 带路径参数且参数可能是某个资源的 ID
        if api['method'] in ('GET', 'PUT', 'PATCH', 'DELETE') and api['path_params']:
            param = api['path_params'][-1]
            resource = api['resource']
            # 查找对应的创建接口
            if resource in creators:
                deps.append({
                    'from': creators[resource]['operation_id'] or creators[resource]['path'],
                    'to': api['operation_id'] or api['path'],
                    'type': 'crud',
                    'resource': resource,
                    'param': param,
                    'note': f"创建 {resource} 后可用于 {api['method']} 操作"
                })
        # 认证相关：标记 login/auth 接口（排除 machine_auth 等非 OAuth 认证）
        path_lower = api['path'].lower()
        is_oauth_login = ('login' in path_lower and 'token' in api.get('operation_id', '')) or \
                         ('/login' in path_lower and api['method'] == 'POST') or \
                         ('/token' in path_lower and api['method'] == 'POST')
        if is_oauth_login or (api['method'] == 'POST' and 'login' in api['resource']):
            if api['method'] == 'POST':
                api['is_auth'] = True
                # 标记其他需要认证的接口
                for other in apis:
                    if other['path'] != api['path'] and other.get('security'):
                        deps.append({
                            'from': api['operation_id'] or api['path'],
                            'to': other['operation_id'] or other['path'],
                            'type': 'auth',
                            'note': '需要先登录获取 Token'
                        })

    return deps


def infer_scenarios(apis, deps):
    """推断常见测试场景"""
    scenarios = []
    resource_apis = {}
    for api in apis:
        r = api['resource']
        if r not in resource_apis:
            resource_apis[r] = []
        resource_apis[r].append(api)

    for resource, r_apis in resource_apis.items():
        methods = {a['method']: a for a in r_apis}
        # CRUD 场景
        if 'POST' in methods:
            chain = []
            if 'POST' in methods:
                chain.append(methods['POST'])
            if 'GET' in methods:
                chain.append(methods['GET'])
            if 'PUT' in methods or 'PATCH' in methods:
                chain.append(methods.get('PUT') or methods.get('PATCH'))
            if 'DELETE' in methods:
                chain.append(methods['DELETE'])
                # 删除后再查询确认 404
                if 'GET' in methods:
                    chain.append({**methods['GET'], '_assert_404': True})
            if len(chain) >= 2:
                scenarios.append({
                    'name': f'{resource}_crud_flow',
                    'type': 'crud',
                    'apis': [a['operation_id'] or a['path'] for a in chain],
                    'description': f'{resource} 完整 CRUD 流程'
                })

    # 认证场景 - 只包含 OAuth2-protected endpoints
    auth_apis = [a for a in apis if a.get('is_auth')]
    if auth_apis:
        # 过滤：只包含有 security 字段且明确需要使用 OAuth2PasswordBearer 的接口
        protected = [a for a in apis if
                     a.get('security') and
                     any('OAuth2PasswordBearer' in s for s in a['security'])]
        if protected:
            scenarios.append({
                'name': 'auth_business_flow',
                'type': 'auth',
                'apis': [auth_apis[0]['operation_id'] or auth_apis[0]['path']] + [
                    p['operation_id'] or p['path'] for p in protected[:3]
                ],
                'description': '登录后访问运营后台接口'
            })

    return scenarios


def extract_models(spec):
    """提取组件模型定义"""
    return spec.get('components', {}).get('schemas', {})


def parse_swagger(input_path):
    """主解析函数"""
    spec = load_spec(input_path)
    apis = parse_paths(spec)
    deps = infer_dependencies(apis)
    scenarios = infer_scenarios(apis, deps)
    models = extract_models(spec)

    result = {
        'info': spec.get('info', {}),
        'host': spec.get('host', ''),
        'basePath': spec.get('basePath', ''),
        'schemes': spec.get('schemes', ['https']),
        'apis': apis,
        'models': models,
        'security_schemes': spec.get('components', {}).get('securitySchemes', {}),
        'dependencies': deps,
        'scenarios': scenarios,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description='Parse Swagger/OpenAPI spec')
    parser.add_argument('--input', '-i', required=True, help='Input Swagger JSON/YAML file')
    parser.add_argument('--output', '-o', default='parsed_api.json', help='Output JSON file')
    args = parser.parse_args()

    result = parse_swagger(args.input)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Parsed {len(result['apis'])} APIs, {len(result['dependencies'])} dependencies, {len(result['scenarios'])} scenarios")
    print(f"Output saved to: {args.output}")


if __name__ == '__main__':
    main()
