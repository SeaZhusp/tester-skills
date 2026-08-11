# api-auto-test 编码规范

编写任何代码前必读。所有新增/修改代码必须与下述规范及现有代码风格完全一致。

## 0. 框架总览与只读边界

```
api-auto-test/
├── api/          # 可写：薄传输层，一方法一端点
├── services/     # 可写：业务层，参数拼装 + 响应解析
├── tests/        # 可写：pytest 用例（auth/home/market/my/op/sys）
├── core/         # 只读：HttpClient、UserContext
├── config/       # 只读：settings、config.yaml
├── common/       # 只读：异常定义（ApiResponseError 等）
├── utils/        # 只读：DataGenerator（随机数据）、jsonpath_utils（JSONPath 提取）
└── tests/conftest.py  # 只读：session 级 admin fixture
```

身份模型：`UserContext` 持有 `HttpClient`，token / X-User-Id 在登录时一次性写入
client headers。api/services/tests 三层都不手动传身份头。

**身份获取硬性规则（必须走 conftest fixture）**：

- 管理员：只能用 conftest 的 session 级 `admin` fixture（全会话只登录一次），
  禁止在用例中自行 `AuthService().login(管理员账号)`；
- 匿名引导：只能用 conftest 的 function 级 `auth_service` fixture，
  禁止在用例中自行实例化 `AuthService()`；
- 其他动态用户：通过 `auth_service.register_and_login()` / `auth_service.login()` 产出
  `UserContext`，再注入业务 Service。

```python
def test_xxx(self, auth_service):
    user = auth_service.register_and_login()   # 匿名引导来自 conftest
    svc = AppService(user)
```

## 1. api 层规范（薄传输层）

文件命名 `{module}_api.py`，类名 `{Module}Api`，继承 `BaseApi`。

**职责边界（严格）**：

- 一个方法对应一个 RESTful 端点，只负责"向端点发请求"；
- 不做参数组装、字段映射、条件判断；`params` / `json` 必须是 service 拼好的最终形态；
- 返回原始 `requests.Response`，不解析状态码/JSON；
- 方法 docstring 写 `HTTP方法 /路径`，端点按业务分组用 `# ==== 分组名 ====` 注释分隔。

模板：

```python
"""XX模块 API 接口层（薄传输层）。"""
from typing import Optional

from api.base_api import BaseApi


class XxxApi(BaseApi):
    """XX相关接口集合（纯传输，无业务组装逻辑）。"""

    # ==================== 分组名 ====================

    def query_xxx(self, params: dict):
        """GET /api/xxx — params 已由 service 拼装好"""
        return self.get("/api/xxx", params=params)

    def update_xxx(self, xxx_id: int, body: dict):
        """PUT /api/xxx/{id}"""
        return self.put(f"/api/xxx/{xxx_id}", json=body)
```

`BaseApi` 已提供：`get/post/put/patch/delete`（返回 Response）、
`parse_json`、`check_status(expected=200)`、`parse_response(response, expected=200)`。

## 2. services 层规范（业务层）

文件命名 `{module}_service.py`，类名 `{Module}Service`（如 `DeviceService`）。

**职责**：字段名映射（snake_case 入参 → camelCase 请求字段）、可选参数过滤、
body 拼装、`parse_response` 校验+解析、数据提取、业务快捷方法。

**必须遵守**：

- 构造函数注入 `UserContext`：`def __init__(self, ctx: UserContext)`，
  内部 `self.ctx = ctx`、`self.api = XxxApi(ctx.client)`（AuthService 除外）；
- 方法签名面向业务，用 snake_case + 关键字参数 + `Optional` 类型标注；
- 可选参数用模块级 `_opt_set` 辅助函数过滤（仅非 None 时写入）：

```python
def _opt_set(target: dict, key: str, value) -> None:
    """仅当 value 非 None 时写入 target，用于构造可选查询参数/请求体。"""
    if value is not None:
        target[key] = value
```

- 分页查询返回记录列表，用 `_extract_records` 从 `{"data": {"records": [...]}}` 提取
  （兼容 data 直接为数组）；详情类返回 `Optional[dict]`；
- 提供业务快捷方法（如 `get_first_xxx`、`get_xxx_by_count`）方便用例取测试数据；
- 所有 docstring 用中文。

方法模板：

```python
def query_xxx(self, *, current: int = 1, size: int = 20,
              keyword: Optional[str] = None,
              os_type: Optional[str] = None,
              **extra_params) -> list[dict]:
    """分页查询XX列表。"""
    params = {"current": current, "size": size}
    _opt_set(params, "keyword", keyword)
    _opt_set(params, "osType", os_type)
    params.update(extra_params)
    body = self.api.parse_response(self.api.query_xxx(params))
    return self._extract_records(body)

def do_action(self, xxx_id: int, reason: str, force: bool = False):
    """执行XX操作。"""
    body = {"reason": reason}
    _opt_set(body, "force", force)
    return self.api.parse_response(self.api.do_action(xxx_id, body))
```

## 3. tests 层规范（pytest + allure）

文件命名 `test_{业务功能}.py`，放入对应业务目录（映射表见 SKILL.md）。

**结构约定**：

- 模块 docstring 用中文说明覆盖场景；
- 模块级 class 作用域 fixture 创建 service（注入全局 `admin`）：

```python
@pytest.fixture(scope="class")
def xxx_service(admin) -> XxxService:
    """以管理员身份操作的XX服务。"""
    return XxxService(admin)
```

- 响应字段提取写成模块级 `_xxx(dict)` 辅助函数（如 `_device_id`、`_shelve_status`），
  兼容字段别名，避免用例内重复取值逻辑；
- 在列表/响应中按字段值查找记录或提取嵌套字段时，**优先复用 `utils/jsonpath_utils`**
  （如 `jsonpath_first_match(records, "id", role_id)` 按 id 取一条、
  `jsonpath_get(resp, "$.code")` 取首个匹配），
  **不要在 service 层新增 `find_xxx_in_list` 这类专用查找方法**；
  简单带别名的字段取值仍用模块级 `_xxx(dict)` 辅助函数即可。
- 禁止跨文件重复定义相同逻辑的辅助函数：若某字段取值辅助函数（`_xxx(dict)`）
  已在多个测试文件中出现相同实现，应将其收敛到对应模块的 `service` 层或 `utils/` 公共工具，
  各测试文件改为调用统一实现，**避免用例层平行复制粘贴同样的取值逻辑**。
- 用例类按 story 分组：正向类 `TestXxx`，异常类 `TestXxxException`（仅用户明确要求时才写）；
- 每个类挂 `@allure.feature("XX模块")` + `@allure.story("...")`；
  每个用例挂 `@allure.title("正向 - ...")` / `@allure.title("异常 - ...")` / `@allure.title("场景 - ...")`；
- 测试数据依赖环境已有数据时，先查询、查不到用 `pytest.skip("环境中无...")`；
- 随机数据用 `utils.data_generator.DataGenerator`（如 `DataGenerator.random_string(6)`）；
- 断言必须带中文说明，格式 `assert 条件, f"期望..., 实际 {actual}"`；
- 操作后必须回查验证状态（如操作后 `get_xxx_by_id` 再断言状态字段）。

**异常用例写法**（仅用户明确要求时）：绕过 service 的 `parse_response`，
直接调 `service.api.xxx()` 拿原始 Response 断言状态码：

```python
resp = xxx_service.api.do_action(bad_id)
assert resp.status_code in (400, 409), f"期望 400/409，实际 {resp.status_code}"
```

**场景用例写法**（多接口串联，顺序必须来自用户）：

- 单个测试方法内按用户给定顺序依次调用 service 方法；
- 每步用 `with allure.step("步骤N：...")` 包裹；
- 上一步返回的数据（id、token 等）作为下一步入参；
- 每个关键步骤后回查断言中间状态，最后断言终态。

```python
@allure.title("场景 - 上架→维护→恢复")
def test_shelve_maintain_restore_flow(self, device_service):
    """场景串联：按用户指定顺序 上架→维护→恢复。"""
    device = device_service.get_first_device(status="1")
    if not device:
        pytest.skip("环境中无可用设备")
    did = _device_id(device)

    with allure.step("步骤1：上架设备"):
        device_service.shelve_device(did)
        assert _shelve_status(device_service.get_device_by_id(did)) == "2", "上架后应为已上架(2)"

    with allure.step("步骤2：标记维护"):
        device_service.maintain_device(did)
        assert _device_status(device_service.get_device_by_id(did)) == "3", "维护中状态应为3"

    with allure.step("步骤3：恢复上架"):
        device_service.restore_device(did)
        assert _device_status(device_service.get_device_by_id(did)) == "1", "恢复后应为空闲(1)"
```

## 4. 通用规范

- Python 3.9+ 语法，4 空格缩进，遵循 PEP 8；
- 所有注释、docstring、断言消息、skip 原因均用中文；
- 导入顺序：标准库 → 第三方（pytest/allure）→ 项目内（api/services/core/utils）；
- 禁止硬编码 base_url、账号密码（由 `config/settings` 与 conftest 管理）；
- 禁止在用例中直接使用 requests，一律经 api/service 层；
- 字段枚举值（如 status、shelveStatus 的取值含义）以接口文档参数表为准，
  断言消息中标注含义，如 `"上架后状态应为2(已上架)"`。
