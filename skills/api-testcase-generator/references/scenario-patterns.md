# 场景链路模式

## 模式定义

场景链路是一组按业务顺序调用的接口，接口间通过变量传递数据（如 Token、ID 等）。

### 变量传递规则

| 变量类型 | 传递方式 | 示例 |
|---------|---------|------|
| 认证 Token | Header: Authorization | `Bearer ${token}` |
| 资源 ID | Path 参数 | `/users/${user_id}` |
| 查询参数 | Query 参数 | `?page=${page}&size=${size}` |
| 关联数据 | Body 字段引用 | `{"parent_id": "${parent_id}"}` |

## 常见场景模式

### 1. CRUD 完整流程

**链路**：Create → Get → Update → Get → Delete → Get(404)

**适用**：单个资源的管理接口

**变量传递**：
- `Create` 返回 `id` → `Get/Update/Delete` 的 Path 参数

**断言重点**：
- 创建后查询存在
- 更新后查询字段已变更
- 删除后查询返回 404

### 2. 认证业务流

**链路**：Login → Business API → Logout → Access Denied

**适用**：需要认证的完整业务流程

**变量传递**：
- `Login` 返回 `token` → 后续请求 Header

**断言重点**：
- 登录成功获取 Token
- 带 Token 访问业务接口成功
- 登出后 Token 失效，再次访问返回 401

### 3. 数据准备-测试-清理流

**链路**：Login → Create Test Data → Run Tests → Delete Test Data → Logout

**适用**：需要前置数据准备的复杂测试

**变量传递**：
- `Login` → `token`
- `Create Test Data` → 多个资源 ID
- 资源 ID 用于测试步骤和清理

**断言重点**：
- 数据创建成功
- 测试步骤使用正确的数据
- 清理后数据不存在（避免污染）

### 4. 批量操作流

**链路**：Login → Create A → Create B → Create C → List All → Delete All → Logout

**适用**：批量创建和管理的业务场景

**断言重点**：
- 列表查询返回所有创建的资源
- 批量删除后所有资源不可访问

### 5. 状态流转流

**链路**：Create → Status:Pending → Approve → Status:Approved → Reject(失败) → Delete

**适用**：有状态机的业务流程（如订单、审批）

**断言重点**：
- 状态转换正确
- 非法状态转换被拒绝

## 场景配置格式

自定义场景使用 JSON 格式：

```json
{
  "scenarios": [
    {
      "name": "user_crud_flow",
      "type": "crud",
      "description": "用户完整 CRUD 流程",
      "apis": [
        {
          "ref": "createUser",
          "extract": [
            {"from": "response.json().id", "to": "user_id"}
          ]
        },
        {
          "ref": "getUserById",
          "path_params": {
            "id": "${user_id}"
          }
        },
        {
          "ref": "updateUser",
          "path_params": {
            "id": "${user_id}"
          }
        },
        {
          "ref": "deleteUser",
          "path_params": {
            "id": "${user_id}"
          }
        },
        {
          "ref": "getUserById",
          "path_params": {
            "id": "${user_id}"
          },
          "expected_status": 404
        }
      ]
    }
  ]
}
```

## 自动识别规则

Skill 自动识别场景的优先级：
1. 相同 resource 下的 POST → GET → PUT/PATCH → DELETE 识别为 CRUD
2. 路径含 login/auth/token 的 POST 接口识别为认证入口
3. 有 `security` 声明的接口自动关联到认证场景
4. 响应 Schema 含 id 字段且后续接口 Path 参数同名，识别为依赖关系
