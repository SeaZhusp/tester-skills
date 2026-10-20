#!/usr/bin/env python3
"""qa-suite · 模拟计数（count_cases.py）

对 Spec Model 做「模拟计数」：用例条数 = 场景枚举结果。
售前评估与交付使用**同一段代码**得出条数，从而保证口径一致（见
references/04-counting-and-conversion.md 第 2 节）。

用法：
    python3 scripts/count_cases.py spec-model.json
    python3 scripts/count_cases.py spec-model.json --modules 3.1,3.2
    python3 scripts/count_cases.py spec-model.json --json

退出码：0 = 正常，1 = 输入非法
"""

import argparse
import json
import sys

AGG_MIN, AGG_MAX = 1.5, 4.0
VALID_PRIORITY = ("P0", "P1", "P2", "P3")
# P0 定性约束（见 references/05-priority-taxonomy.md 第 2 节）：低于下限疑漏主流程，高于上限疑滥标
P0_MIN, P0_MAX = 0.05, 0.35


def count(spec, module_filter=None):
    modules = spec.get("modules") or []
    rows = []
    total_tp = total_sc = total_fp = 0
    priority_counter = {p: 0 for p in VALID_PRIORITY}
    placeholders = []

    for m in modules:
        if module_filter:
            key = str(m.get("chapter") or "") + "|" + str(m.get("name") or "")
            if not any(f in key or f == m.get("id") for f in module_filter):
                continue

        fps = m.get("feature_points") or []
        tps = m.get("test_points") or []
        scs = m.get("scenarios") or []

        n_fp, n_tp, n_sc = len(fps), len(tps), len(scs)
        ratio = (n_tp / n_sc) if n_sc else 0.0

        declared = m.get("case_count")
        consistent = declared is None or int(declared) == n_sc

        for sc in scs:
            p = sc.get("priority")
            if p in priority_counter:
                priority_counter[p] += 1

        if m.get("status") == "placeholder":
            placeholders.append(
                {"module": m.get("name"), "id": m.get("id"), "cases": n_sc}
            )

        rows.append(
            {
                "module": m.get("name"),
                "chapter": m.get("chapter"),
                "id": m.get("id"),
                "status": m.get("status", "estimated"),
                "feature_points": n_fp,
                "test_points": n_tp,
                "cases": n_sc,
                "ratio": round(ratio, 2),
                "ratio_ok": (AGG_MIN <= ratio <= AGG_MAX) if n_sc else None,
                "case_count_consistent": consistent,
            }
        )
        total_fp += n_fp
        total_tp += n_tp
        total_sc += n_sc

    overall_ratio = round(total_tp / total_sc, 2) if total_sc else 0.0

    p0_ratio = (priority_counter["P0"] / total_sc) if total_sc else 0.0
    if not total_sc:
        p0_hint = None
    elif p0_ratio < P0_MIN:
        p0_hint = "P0 占比过低，疑漏核心主流程"
    elif p0_ratio > P0_MAX:
        p0_hint = "P0 占比过高，疑滥标 P0（什么都重要等于都不重要）"
    else:
        p0_hint = None
    p0_check = {
        "p0_ratio": round(p0_ratio * 100, 1),
        "range": [int(P0_MIN * 100), int(P0_MAX * 100)],
        "in_range": p0_hint is None,
        "hint": p0_hint,
    }

    return {
        "total_cases": total_sc,
        "total_test_points": total_tp,
        "total_feature_points": total_fp,
        "overall_ratio": overall_ratio,
        "priority_counts": priority_counter,
        "priority_ratio": {
            p: round(n / total_sc * 100, 1) if total_sc else 0.0
            for p, n in priority_counter.items()
        },
        "p0_check": p0_check,
        "placeholder_modules": placeholders,
        "modules": rows,
    }


def render_markdown(r, spec_path):
    lines = []
    lines.append("## count_cases.py · 模拟计数结果")
    lines.append("")
    lines.append(f"- 输入：`{spec_path}`")
    lines.append(f"- 口径：聚合用例口径 v1（1 用例 = 1 个可独立执行的业务操作场景）")
    lines.append("")
    lines.append(f"**功能用例总数：{r['total_cases']} 条**")
    lines.append("")
    lines.append(
        f"- 功能点 {r['total_feature_points']} / 测试点 {r['total_test_points']}"
        f" / 场景(=用例) {r['total_cases']}"
    )
    lines.append(f"- 整体聚合比（测试点÷用例）：**{r['overall_ratio']}**（合规区间 [{AGG_MIN}, {AGG_MAX}]）")
    lines.append("")

    lines.append("### 优先级分布（真实统计）")
    lines.append("")
    lines.append("| 优先级 | 用例数 | 占比 |")
    lines.append("| --- | --- | --- |")
    for p in VALID_PRIORITY:
        lines.append(f"| {p} | {r['priority_counts'][p]} | {r['priority_ratio'][p]}% |")
    lines.append("")
    pc = r["p0_check"]
    if pc["in_range"]:
        lines.append(f"> P0 占比 {pc['p0_ratio']}%，落在约束区间 {pc['range'][0]}%~{pc['range'][1]}% 内。")
    else:
        lines.append(f"> ⚠️ P0 占比 {pc['p0_ratio']}%，超出约束区间 {pc['range'][0]}%~{pc['range'][1]}%：{pc['hint']}")
    lines.append("")

    lines.append("### 模块级明细（证据链）")
    lines.append("")
    lines.append("| 模块 | 章节 | 状态 | 功能点 | 测试点 | 用例数 | 聚合比 | 合规 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for m in r["modules"]:
        ok = "—" if m["ratio_ok"] is None else ("✓" if m["ratio_ok"] else "✗ 越界")
        warn = "" if m["case_count_consistent"] else " ⚠️case_count不一致"
        lines.append(
            f"| {m['module']} | {m['chapter']} | {m['status']} | {m['feature_points']}"
            f" | {m['test_points']} | {m['cases']}{warn} | {m['ratio']} | {ok} |"
        )
    lines.append(
        f"| **合计** | — | — | **{r['total_feature_points']}**"
        f" | **{r['total_test_points']}** | **{r['total_cases']}** | {r['overall_ratio']} | — |"
    )
    lines.append("")

    if r["placeholder_modules"]:
        lines.append("### 占位模块（文档缺口，默认不计入基准）")
        lines.append("")
        for p in r["placeholder_modules"]:
            lines.append(f"- {p['module']}（{p['id']}）：占位 {p['cases']} 条")
        lines.append("")

    bad = [m for m in r["modules"] if m["ratio_ok"] is False]
    if bad:
        lines.append("### ⚠️ 聚合比越界模块（粒度契约第 2 节）")
        lines.append("")
        for m in bad:
            hint = "疑过度拆分，应把校验维度合并回场景" if m["ratio"] < AGG_MIN else "疑过度聚合，应拆分为多个业务意图"
            lines.append(f"- {m['module']}：{m['ratio']} —— {hint}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="qa-suite · 模拟计数")
    parser.add_argument("spec", help="spec-model.json 路径")
    parser.add_argument("--modules", help="只统计指定模块（章节号/名称片段，逗号分隔）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = parser.parse_args()

    try:
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
    except FileNotFoundError:
        print(f"文件不存在：{args.spec}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败：{e}", file=sys.stderr)
        sys.exit(1)

    if not spec.get("modules"):
        print("spec-model.json 中 modules 为空，无法计数", file=sys.stderr)
        sys.exit(1)

    module_filter = None
    if args.modules:
        module_filter = [s.strip() for s in args.modules.split(",") if s.strip()]

    result = count(spec, module_filter)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result, args.spec))


if __name__ == "__main__":
    main()