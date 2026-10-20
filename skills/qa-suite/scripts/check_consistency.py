#!/usr/bin/env python3
"""qa-suite · 跨阶段一致性核销（check_consistency.py）

核销项 T1~T8 定义见 references/07-traceability-rules.md 第 3 节。
用途：验证「售前预估口径」与「交付用例」是否同源、同量纲、可追溯。

用法：
    python3 scripts/check_consistency.py --estimate spec-model.json --cases test-cases.json
    python3 scripts/check_consistency.py --estimate spec-model.json --cases test-cases.json --json
    python3 scripts/check_consistency.py --estimate spec-model.json --cases test-cases.json --tolerance 0.20

退出码：0 = PASS（可含 WARN），1 = FAIL
"""

import argparse
import json
import sys

AGG_MIN, AGG_MAX = 1.5, 4.0
DEFAULT_TOLERANCE = 0.20
MODULE_COVERAGE_MIN = 0.90


class Report:
    def __init__(self):
        self.fails = []
        self.warns = []

    def fail(self, rule, msg):
        self.fails.append({"rule": rule, "msg": msg})

    def warn(self, rule, msg):
        self.warns.append({"rule": rule, "msg": msg})


def norm(text):
    return str(text or "").replace(" ", "").replace("　", "").lower()


def module_keys(m):
    keys = []
    for k in ("name", "chapter", "id", "short_code"):
        v = m.get(k)
        if v:
            keys.append(norm(v))
    # aliases：模块的别名（同一模块在不同文档/口径下的其他叫法）
    for a in m.get("aliases") or []:
        keys.append(norm(a))
    return keys


def match_module(case_module, modules):
    """把用例的 module 字段匹配到 spec 模块，返回 module id 或 None"""
    cm = norm(case_module)
    if not cm:
        return None
    # 精确
    for m in modules:
        if cm == norm(m.get("name")) or cm == norm(m.get("chapter")):
            return m.get("id")
    # 包含（双向）
    best = None
    best_len = 0
    for m in modules:
        for k in module_keys(m):
            if len(k) < 2:
                continue
            if k in cm or cm in k:
                if len(k) > best_len:
                    best, best_len = m.get("id"), len(k)
    return best


def run(spec, cases, tolerance):
    rep = Report()
    modules = spec.get("modules") or []
    mod_by_id = {m.get("id"): m for m in modules}

    # spec 侧：测试点 -> 模块
    tp_module = {}
    tp_ids = set()
    for m in modules:
        for tp in m.get("test_points") or []:
            tpid = tp.get("id")
            tp_module[tpid] = m.get("id")
            tp_ids.add(tpid)
        for fp in m.get("feature_points") or []:
            if not any(
                tp.get("feature_point_id") == fp.get("id")
                for tp in (m.get("test_points") or [])
            ):
                rep.fail("T3", f"功能点 {fp.get('id')} 没有任何测试点（模块 {m.get('name')}）")

    tcs = cases.get("test_cases") or []
    if not tcs:
        rep.fail("T1", "用例集为空")
        return rep, {}

    # ---------- T1 point 可解析 ----------
    referenced = set()
    case_module_of = {}
    for tc in tcs:
        cid = tc.get("id") or "<无编号>"
        raw = tc.get("point") or ""
        pts = [p.strip() for p in str(raw).replace("，", ",").split(",") if p.strip()]
        if not pts:
            rep.fail("T1", f"用例 {cid} 的 point 为空")
            continue
        for p in pts:
            if p not in tp_ids:
                rep.fail("T1", f"用例 {cid} 引用了不存在的测试点：{p}")
            else:
                referenced.add(p)
        case_module_of[cid] = tc.get("module")

    # ---------- T2 测试点覆盖率 ----------
    orphan = tp_ids - referenced
    if orphan:
        sample = ", ".join(sorted(orphan)[:8])
        rep.fail("T2", f"存在 {len(orphan)} 个孤儿测试点（未被任何用例引用）：{sample} ...")

    # ---------- T5 模块匹配 ----------
    unmatched = []
    for cid, cmod in case_module_of.items():
        if match_module(cmod, modules) is None:
            unmatched.append((cid, cmod))
    if unmatched:
        sample = "; ".join(f"{c}->{m}" for c, m in unmatched[:8])
        rep.fail("T5", f"有 {len(unmatched)} 条用例的 module 无法匹配到 Spec Model：{sample}")

    # ---------- T6 note 追溯 ----------
    no_note = [tc.get("id") for tc in tcs if not (tc.get("note") or "").strip()]
    if no_note:
        rep.fail("T6", f"有 {len(no_note)} 条用例的 note 为空（缺需求追溯）：{', '.join(no_note[:8])}")

    # ---------- T4 / T7 模块覆盖率 ----------
    mod_rows = []
    covered_by_module = {}
    for p in referenced:
        mid = tp_module.get(p)
        covered_by_module.setdefault(mid, set()).add(p)

    for m in modules:
        mid = m.get("id")
        tps = [tp.get("id") for tp in (m.get("test_points") or [])]
        covered = covered_by_module.get(mid, set())
        cov = len(covered) / len(tps) if tps else 0.0
        cases_of_mod = [
            cid for cid, cmod in case_module_of.items() if match_module(cmod, modules) == mid
        ]
        if not cases_of_mod:
            rep.warn("T4", f"模块 {m.get('name')} 没有任何用例")
        if cov < MODULE_COVERAGE_MIN:
            rep.fail(
                "T7",
                f"模块 {m.get('name')} 覆盖率 {cov*100:.1f}% < {MODULE_COVERAGE_MIN*100:.0f}%"
                f"（{len(covered)}/{len(tps)}）",
            )
        mod_rows.append(
            {
                "module": m.get("name"),
                "chapter": m.get("chapter"),
                "feature_points": len(m.get("feature_points") or []),
                "test_points": len(tps),
                "cases": len(cases_of_mod),
                "scenarios_estimate": len(m.get("scenarios") or []),
                "coverage": round(cov * 100, 1),
            }
        )

    # ---------- T8 预估 vs 实际 ----------
    declared_total = 0
    for m in modules:
        if m.get("status") == "placeholder":
            continue
        cc = m.get("case_count")
        declared_total += int(cc) if cc is not None else len(m.get("scenarios") or [])
    actual_total = len(tcs)
    deviation = (actual_total - declared_total) / declared_total if declared_total else 0.0
    if declared_total and abs(deviation) > tolerance:
        rep.fail(
            "T8",
            f"预估 {declared_total} 条 vs 实际交付 {actual_total} 条，偏差 {deviation*100:+.1f}%"
            f" 超出容差 ±{tolerance*100:.0f}%（若无说明则不合格）",
        )

    # ---------- 聚合比 ----------
    overall_ratio = round(len(tp_ids) / actual_total, 2) if actual_total else 0.0
    if actual_total and not (AGG_MIN <= overall_ratio <= AGG_MAX):
        rep.warn(
            "AGG",
            f"整体聚合比 {overall_ratio} 超出 [{AGG_MIN}, {AGG_MAX}]（测试点 {len(tp_ids)} / 用例 {actual_total}）",
        )

    stats = {
        "estimate_total": declared_total,
        "actual_total": actual_total,
        "deviation_pct": round(deviation * 100, 1),
        "test_points": len(tp_ids),
        "covered_test_points": len(referenced),
        "overall_ratio": overall_ratio,
        "coverage_pct": round(len(referenced) / len(tp_ids) * 100, 1) if tp_ids else 0.0,
    }
    return rep, {"stats": stats, "modules": mod_rows}


def render_markdown(rep, data):
    lines = []
    stats = data["stats"]
    lines.append("## check_consistency.py · 一致性核销")
    lines.append("")
    lines.append(f"- 售前预估条数（Spec Model 场景/`case_count` 累计）：**{stats['estimate_total']}**")
    lines.append(f"- 实际交付条数：**{stats['actual_total']}**")
    lines.append(f"- 偏差：**{stats['deviation_pct']:+.1f}%**")
    lines.append(
        f"- 测试点覆盖率：**{stats['coverage_pct']}%**"
        f"（{stats['covered_test_points']}/{stats['test_points']}）"
    )
    lines.append(f"- 整体聚合比：**{stats['overall_ratio']}**（合规区间 [{AGG_MIN}, {AGG_MAX}]）")
    lines.append("")

    lines.append("### 双向核对表（模块级）")
    lines.append("")
    lines.append("| 模块 | 章节 | 功能点 | 测试点 | 预估用例 | 实际用例 | 覆盖率 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for m in data["modules"]:
        lines.append(
            f"| {m['module']} | {m['chapter']} | {m['feature_points']} | {m['test_points']}"
            f" | {m['scenarios_estimate']} | {m['cases']} | {m['coverage']}% |"
        )
    lines.append("")

    if rep.fails:
        lines.append(f"### FAIL（{len(rep.fails)} 项）")
        lines.append("")
        lines.append("| 规则 | 问题 |")
        lines.append("| --- | --- |")
        for f in rep.fails:
            lines.append(f"| {f['rule']} | {f['msg']} |")
        lines.append("")
    if rep.warns:
        lines.append(f"### WARN（{len(rep.warns)} 项）")
        lines.append("")
        lines.append("| 规则 | 提示 |")
        lines.append("| --- | --- |")
        for w in rep.warns:
            lines.append(f"| {w['rule']} | {w['msg']} |")
        lines.append("")

    verdict = "FAIL" if rep.fails else "PASS"
    lines.append(f"**结论：{verdict}**（FAIL {len(rep.fails)} / WARN {len(rep.warns)}）")
    if rep.fails:
        lines.append("")
        lines.append("> 门禁要求：FAIL 项必须在交付物中**显式登记**（原因 / 处置 / 残留风险），不允许口头放过。")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="qa-suite · 跨阶段一致性核销")
    parser.add_argument("--estimate", required=True, help="spec-model.json 路径")
    parser.add_argument("--cases", required=True, help="用例集 JSON 路径")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE, help="预估与实际偏差容差，默认 0.20")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = parser.parse_args()

    try:
        with open(args.estimate, "r", encoding="utf-8") as f:
            spec = json.load(f)
        with open(args.cases, "r", encoding="utf-8") as f:
            cases = json.load(f)
    except FileNotFoundError as e:
        print(f"文件不存在：{e.filename}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败：{e}", file=sys.stderr)
        sys.exit(1)

    rep, data = run(spec, cases, args.tolerance)

    if args.json:
        print(
            json.dumps(
                {
                    "stats": data.get("stats", {}),
                    "modules": data.get("modules", []),
                    "fails": rep.fails,
                    "warns": rep.warns,
                    "verdict": "FAIL" if rep.fails else "PASS",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(render_markdown(rep, data))

    sys.exit(1 if rep.fails else 0)


if __name__ == "__main__":
    main()