#!/usr/bin/env python3
"""qa-suite · Spec Model 结构机检（validate_spec_model.py）

校验规则 V1~V10 定义见 references/03-spec-model-schema.md 第 4 节。

用法：
    python3 scripts/validate_spec_model.py spec-model.json
    python3 scripts/validate_spec_model.py spec-model.json --json

退出码：0 = PASS（可含 WARN），1 = FAIL
"""

import argparse
import json
import sys

VALID_COMPLEXITY = {"simple", "medium", "complex"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_STATUS = {"estimated", "placeholder"}
VALID_CATEGORY = {"正向", "边界", "异常", "状态", "权限"}
VALID_HANDLES = {"入口", "动词", "状态", "角色"}
VALID_PRIORITY = {"P0", "P1", "P2", "P3"}
AGG_MIN, AGG_MAX = 1.5, 4.0
META_REQUIRED = [
    "title",
    "source",
    "source_version",
    "granularity_contract",
    "generated_at",
    "confidence",
]


class Report:
    def __init__(self):
        self.fails = []
        self.warns = []

    def fail(self, rule, msg):
        self.fails.append({"rule": rule, "msg": msg})

    def warn(self, rule, msg):
        self.warns.append({"rule": rule, "msg": msg})


def run(spec):
    rep = Report()

    # ---------- V1 meta ----------
    meta = spec.get("meta")
    if not isinstance(meta, dict):
        rep.fail("V1", "meta 缺失或不是对象")
        meta = {}
    for k in META_REQUIRED:
        if not meta.get(k):
            rep.fail("V1", f"meta.{k} 缺失")
    if meta.get("confidence") and meta["confidence"] not in VALID_CONFIDENCE:
        rep.fail("V1", f"meta.confidence 取值非法：{meta['confidence']}")

    modules = spec.get("modules")
    if not isinstance(modules, list) or not modules:
        rep.fail("V1", "modules 缺失或为空")
        return rep, {}

    # ---------- 遍历 ----------
    ids = {}            # id -> 类型，用于 V4
    tp_to_fp = {}       # tp_id -> fp_id
    tp_of_module = {}   # module_id -> [tp_id]
    sc_of_module = {}   # module_id -> [scenario]
    all_tp = set()
    all_referenced = set()

    def claim(identifier, kind):
        if not identifier:
            rep.fail("V4", f"存在无 id 的 {kind}")
            return
        if identifier in ids:
            rep.fail("V4", f"id 重复：{identifier}（已作为 {ids[identifier]}，又作为 {kind}）")
        else:
            ids[identifier] = kind

    for m in modules:
        mid = m.get("id")
        name = m.get("name") or mid or "<未知模块>"
        claim(mid, "模块")
        if not m.get("name"):
            rep.fail("V1", f"模块 {mid} 缺少 name")
        if not m.get("chapter"):
            rep.warn("V1", f"模块 {mid} 缺少 chapter")
        if m.get("status") and m["status"] not in VALID_STATUS:
            rep.warn("V1", f"模块 {mid} status 取值非法：{m['status']}")

        fps = m.get("feature_points") or []
        tps = m.get("test_points") or []
        scs = m.get("scenarios") or []

        # V2 模块必须有功能点
        if not fps:
            rep.fail("V2", f"模块 {name} 没有任何功能点")

        fp_ids = set()
        for fp in fps:
            fpid = fp.get("id")
            claim(fpid, "功能点")
            fp_ids.add(fpid)
            # V3 复杂度定级
            cx = fp.get("complexity")
            if cx not in VALID_COMPLEXITY:
                rep.fail("V3", f"功能点 {fpid} 的 complexity 非法或缺失：{cx}")
            if not fp.get("complexity_reason"):
                rep.fail("V3", f"功能点 {fpid} 缺少 complexity_reason（定级不可复核）")
            if not fp.get("name"):
                rep.warn("V3", f"功能点 {fpid} 缺少 name")

        tp_ids = set()
        for tp in tps:
            tpid = tp.get("id")
            claim(tpid, "测试点")
            tp_ids.add(tpid)
            all_tp.add(tpid)
            fpid = tp.get("feature_point_id")
            # V5 测试点归属可解析
            if fpid not in fp_ids:
                rep.fail("V5", f"测试点 {tpid} 的 feature_point_id 无法解析：{fpid}")
            tp_to_fp[tpid] = fpid
            if tp.get("category") not in VALID_CATEGORY:
                rep.warn("V5", f"测试点 {tpid} 的 category 非法或缺失：{tp.get('category')}")
            if not tp.get("group"):
                rep.warn("V5", f"测试点 {tpid} 缺少 group（用例标题前缀来源）")

        referenced = set()
        for sc in scs:
            scid = sc.get("id")
            claim(scid, "场景")
            pids = sc.get("point_ids") or []
            # V6 场景必须引用测试点
            if not pids:
                rep.fail("V6", f"场景 {scid} 的 point_ids 为空")
            for p in pids:
                if p not in tp_ids:
                    rep.fail("V6", f"场景 {scid} 引用了本模块不存在的测试点：{p}")
                referenced.add(p)
                all_referenced.add(p)
            if sc.get("handles") and sc["handles"] not in VALID_HANDLES:
                rep.warn("V6", f"场景 {scid} 的 handles 非法：{sc['handles']}")
            if sc.get("priority") not in VALID_PRIORITY:
                rep.fail("V6", f"场景 {scid} 的 priority 非法或缺失：{sc.get('priority')}")

        # V7（模块内）本模块测试点未被本模块场景引用：多为跨模块引用，告警
        orphan = tp_ids - referenced
        if orphan:
            sample = ", ".join(sorted(orphan)[:5])
            rep.warn("V7", f"模块 {name} 有 {len(orphan)} 个测试点未被本模块场景引用：{sample} ...")

        # V8 case_count 一致
        cc = m.get("case_count")
        if cc is None:
            rep.warn("V8", f"模块 {name} 缺少 case_count")
        elif int(cc) != len(scs):
            rep.fail("V8", f"模块 {name} 的 case_count={cc} 与实际场景数 {len(scs)} 不一致")

        # V10 聚合比
        if scs:
            ratio = len(tp_ids) / len(scs)
            if ratio < AGG_MIN or ratio > AGG_MAX:
                rep.warn(
                    "V10",
                    f"模块 {name} 聚合比 {ratio:.2f} 超出 [{AGG_MIN}, {AGG_MAX}]"
                    f"（测试点 {len(tp_ids)} / 场景 {len(scs)}）",
                )

        tp_of_module[mid] = sorted(tp_ids)
        sc_of_module[mid] = scs

    # ---------- V7（全局）测试点覆盖率 100% ----------
    global_orphan = all_tp - all_referenced
    if global_orphan:
        sample = ", ".join(sorted(global_orphan)[:8])
        rep.fail(
            "V7",
            f"存在 {len(global_orphan)} 个全局孤儿测试点（未被任何场景引用）：{sample} ...",
        )

    # ---------- V9 汇总一致 ----------
    total_fp = sum(len(m.get("feature_points") or []) for m in modules)
    total_tp = sum(len(m.get("test_points") or []) for m in modules)
    total_sc = sum(len(m.get("scenarios") or []) for m in modules)
    for key, actual in (
        ("total_modules", len(modules)),
        ("total_feature_points", total_fp),
        ("total_test_points", total_tp),
        ("total_scenarios", total_sc),
    ):
        declared = meta.get(key)
        if declared is not None and int(declared) != actual:
            rep.warn("V9", f"meta.{key}={declared} 与实际计数 {actual} 不一致")

    stats = {
        "modules": len(modules),
        "feature_points": total_fp,
        "test_points": total_tp,
        "scenarios": total_sc,
    }
    return rep, stats


def render_markdown(rep, stats, path):
    lines = []
    lines.append("## validate_spec_model.py")
    lines.append("")
    lines.append(f"- 文件：`{path}`")
    lines.append(
        f"- 规模：模块 {stats.get('modules', 0)} / 功能点 {stats.get('feature_points', 0)}"
        f" / 测试点 {stats.get('test_points', 0)} / 场景 {stats.get('scenarios', 0)}"
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
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="qa-suite · Spec Model 结构机检")
    parser.add_argument("spec", help="spec-model.json 路径")
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

    rep, stats = run(spec)

    if args.json:
        print(
            json.dumps(
                {
                    "file": args.spec,
                    "stats": stats,
                    "fails": rep.fails,
                    "warns": rep.warns,
                    "verdict": "FAIL" if rep.fails else "PASS",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(render_markdown(rep, stats, args.spec))

    sys.exit(1 if rep.fails else 0)


if __name__ == "__main__":
    main()