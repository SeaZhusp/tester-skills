# 断言规则库

## 默认断言

所有接口用例默认包含以下断言：

| 断言项 | 说明 |
|-------|------|
| HTTP 状态码 | 根据方法推断（POST→201, DELETE→204, GET/PUT/PATCH→200）|
| Content-Type | 校验响应 Content-Type 与 Produces 声明一致 |
| 响应时间 | 可选：响应时间 < 5s（性能基线）|

## 业务断言模式

### 创建类接口 (POST)

**目标**：验证资源创建成功且数据正确持久化。

| 断言点 | 示例 |
|-------|------|
| 状态码 201/200 | `assert response.status_code == 201` |
| 响应体包含 id | `assert 'id' in response.json()` |
| 关键字段匹配请求 | `assert response.json()['name'] == payload['name']` |
| 二次查询确认 | 调用 GET 接口，确认资源存在且字段一致 |
| 列表包含新资源 | 调用 LIST 接口，确认返回数组包含该资源 |

### 查询类接口 (GET)

**目标**：验证资源查询返回正确数据。

| 断言点 | 示例 |
|-------|------|
| 状态码 200 | `assert response.status_code == 200` |
| 响应体非空 | `assert response.json() is not None` |
| 关键字段存在 | `assert 'id' in data and 'name' in data` |
| 字段类型正确 | `assert isinstance(data['id'], (int, str))` |
| 列表分页正确 | `assert len(data['items']) <= page_size` |

### 更新类接口 (PUT/PATCH)

**目标**：验证资源更新成功且变更已生效。

| 断言点 | 示例 |
|-------|------|
| 状态码 200 | `assert response.status_code == 200` |
| 响应体字段已更新 | `assert response.json()['status'] == 'updated'` |
| 二次查询确认 | 调用 GET 接口，确认字段值已变更 |
| 未变更字段保持 | `assert response.json()['id'] == original_id` |

### 删除类接口 (DELETE)

**目标**：验证资源删除成功且不可再访问。

| 断言点 | 示例 |
|-------|------|
| 状态码 200/204 | `assert response.status_code in (200, 204)` |
| 二次查询返回 404 | 调用 GET 接口，确认返回 404 或 Not Found |
| 列表不包含已删资源 | 调用 LIST 接口，确认返回数组不包含该资源 |

### 认证类接口 (Login/Auth)

**目标**：验证登录成功且 Token 有效。

| 断言点 | 示例 |
|-------|------|
| 状态码 200 | `assert response.status_code == 200` |
| 响应包含 Token | `assert 'token' in response.json()` |
| Token 非空 | `assert len(response.json()['token']) > 0` |
| 使用 Token 可访问受保护接口 | 携带 Token 访问业务接口，确认返回 200 |
| 无 Token 访问被拒 | 不带 Token 访问，确认返回 401/403 |

## 异常断言模式

| 场景 | 状态码 | 断言内容 |
|------|-------|---------|
| 参数缺失 | 400 | 响应包含错误信息，指明缺失字段 |
| 参数类型错误 | 400 | 响应包含格式错误提示 |
| 资源不存在 | 404 | 状态码 404，响应包含 Not Found |
| 无权限访问 | 403 | 状态码 403 |
| 未认证访问 | 401 | 状态码 401 |
| 数据冲突 | 409 | 状态码 409（如重复创建）|

## 扩展规则

用户可通过以下方式扩展断言：
1. 在 Swagger 的 `x-test-assertions` 扩展字段中声明自定义断言
2. 提供 `assertion-config.json` 文件覆盖默认规则
