# 测试用例 Excel / CSV 导出参考

当用户要求导出 Excel（.xlsx）或 CSV 时，按本文件将结构化数据落盘。

## 标准列（与测试用例模板保持一致）

用例编号 | 所属模块/需求 | 对应测试点 | 测试标题 | 测试类型 | 优先级 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 | 备注

## 生成 xlsx

1. 将测试点与用例写成 JSON 文件（schema 见下），保存到当前工作区的临时或交付目录（如 `test-cases.json`）。
2. 运行生成脚本：
   ```bash
   python3 scripts/generate_xlsx.py <input.json> <output.xlsx>
   ```
   - 若提示 `openpyxl` 缺失，安装依赖后重试：`python3 -m pip install openpyxl`。
3. 返回 xlsx 路径，并说明文件含「测试用例」与「测试点清单」两个工作表、已做表头冻结与自动筛选、优先级配色。

## JSON Schema

```json
{
  "meta": { "title": "示例功能 测试用例集" },
  "test_points": [
    { "id": "TP-LOGIN-01", "dimension": "功能", "desc": "正确账号密码可登录" }
  ],
  "test_cases": [
    {
      "id": "TC-LOGIN-01",
      "module": "登录",
      "point": "TP-LOGIN-01",
      "title": "正确账号密码登录成功",
      "type": "功能",
      "priority": "P0",
      "precondition": "已注册账号 test/Passw0rd",
      "steps": "1. 打开登录页\n2. 输入账号与密码\n3. 点击登录",
      "data": "test / Passw0rd",
      "expected": "跳转首页，右上角显示用户名",
      "note": ""
    }
  ]
}
```

- `test_points` 与 `test_cases` 均可为空数组；仅当 `test_points` 非空时才生成「测试点清单」工作表。
- `priority` 取值 P0/P1/P2/P3，对应不同底色，便于一眼区分重要性。
- `steps`、`expected` 支持用 `\n` 换行，生成后会在单元格内自动换行。

## CSV 导出

若用户只要 CSV（纯文本表格），在生成 xlsx 的同目录用 Python 把用例写出为 `test-cases.csv`：表头同标准列，逗号分隔、引号转义，同样满足「表格文件」需求。示例：

```bash
python3 - <<'PY'
import csv, json
data = json.load(open("test-cases.json", encoding="utf-8"))
cols = ["用例编号","所属模块/需求","对应测试点","测试标题","测试类型","优先级","前置条件","测试步骤","测试数据","预期结果","备注"]
with open("test-cases.csv","w",newline="",encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for tc in data.get("test_cases", []):
        w.writerow({
            "用例编号": tc.get("id",""),"所属模块/需求": tc.get("module",""),
            "对应测试点": tc.get("point",""),"测试标题": tc.get("title",""),
            "测试类型": tc.get("type",""),"优先级": tc.get("priority",""),
            "前置条件": tc.get("precondition",""),"测试步骤": tc.get("steps",""),
            "测试数据": tc.get("data",""),"预期结果": tc.get("expected",""),
            "备注": tc.get("note",""),
        })
print("✅ 已生成 test-cases.csv")
PY
```
