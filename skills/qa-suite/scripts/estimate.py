#!/usr/bin/env python3
"""qa-suite · 周期与人员换算（estimate.py）

职责：把「用例条数」换算为「各阶段人天、测试周期、投入人数」。
用例条数由 count_cases.py 得出，本脚本只做确定性算术（见
references/04-counting-and-conversion.md 第 6 节）。

用法：
    echo '{"total_cases": 340, "team_size": 4}'   | python3 scripts/estimate.py
    echo '{"total_cases": 340, "target_days": 20}'| python3 scripts/estimate.py --json
    python3 scripts/estimate.py --input inputs.json

输入字段：
    total_cases  (int, 必填)   功能用例总条数（来自 count_cases.py）
    smoke_cases  (int, 可选)   冒烟条数，缺省 = total_cases * smoke_ratio
    team_size    (int, 可选)   团队人数 → 算周期
    target_days  (float, 可选) 目标周期(自然日) → 算人数
    config_path  (str, 可选)   自定义配置路径

退出码：0 = 正常，1 = 输入非法
"""

import argparse
import json
import math
import os
import sys

DEFAULT_CONFIG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "assets", "estimate-config.json"
)


def load_config(path):
    with open(path or DEFAULT_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


def round_half_up(x, ndigits=1):
    factor = 10 ** ndigits
    return math.floor(x * factor + 0.5) / factor


def estimate(inputs, cfg):
    total = int(inputs["total_cases"])
    if total <= 0:
        raise ValueError("total_cases 必须为正整数")

    smoke = inputs.get("smoke_cases")
    if smoke is None:
        smoke = round(total * cfg["smoke_ratio"])
    smoke = int(smoke)

    prod = cfg["productivity"]
    ratios = cfg["phase_ratios"]

    design = total / prod["case_design_per_day"]
    review = design * ratios["review_ratio"]
    env_prep = max(1.0, design * ratios["env_prep_ratio"])
    execution = total / prod["case_execution_per_day"]
    regression = total * cfg["regression_scope_ratio"] / prod["regression_per_day"]
    report = ratios["report_days"]

    phases = [
        ("需求分析与用例设计", design),
        ("用例评审", review),
        ("测试环境与数据准备", env_prep),
        ("用例执行（首轮）", execution),
        ("缺陷回归测试", regression),
        ("测试报告与收尾", report),
    ]

    raw = sum(d for _, d in phases)
    buffered = raw * (1 + cfg["buffer_ratio"])
    smoke_ratio = smoke / total if total else 0.0

    result = {
        "total_cases": total,
        "smoke_cases": smoke,
        "smoke_ratio": round_half_up(smoke_ratio * 100, 1),
        "smoke_ratio_range": cfg.get("smoke_ratio_range"),
        "phases": [(name, round_half_up(d)) for name, d in phases],
        "raw_man_days": round_half_up(raw),
        "buffered_man_days": round_half_up(buffered),
        "buffer_ratio": cfg["buffer_ratio"],
        "productivity": prod,
        "workdays_per_week": cfg["workdays_per_week"],
    }

    lo, hi = (cfg.get("smoke_ratio_range") or [0.08, 0.15])
    result["smoke_ratio_ok"] = bool(lo <= smoke_ratio <= hi)

    team_size = inputs.get("team_size")
    target_days = inputs.get("target_days")
    if team_size:
        team_size = int(team_size)
        days = buffered / (team_size * cfg["parallel_efficiency"])
        result.update(
            {
                "mode": "given_team",
                "team_size": team_size,
                "calendar_days": round_half_up(days),
                "weeks": round_half_up(days / cfg["workdays_per_week"], 1),
            }
        )
    elif target_days:
        target_days = float(target_days)
        needed = buffered / (target_days * cfg["parallel_efficiency"])
        result.update(
            {
                "mode": "given_days",
                "target_days": target_days,
                "required_team_size": int(math.ceil(needed)),
                "weeks": round_half_up(target_days / cfg["workdays_per_week"], 1),
            }
        )
    else:
        result["mode"] = "man_days_only"
    return result


def render_markdown(r):
    out = []
    out.append("## estimate.py · 周期与人员换算")
    out.append("")
    out.append(f"- 功能用例总数：**{r['total_cases']} 条**（来源：`count_cases.py` 模拟计数）")
    out.append(
        f"- 冒烟用例：**{r['smoke_cases']} 条**（占比 {r['smoke_ratio']}%"
        f"{'' if r.get('smoke_ratio_ok') else ' ⚠️ 超出 8%~15% 合理区间'}）"
    )
    out.append("")
    out.append("### 各阶段工作量")
    out.append("")
    out.append("| 阶段 | 工作量（人天） |")
    out.append("| --- | --- |")
    for name, d in r["phases"]:
        out.append(f"| {name} | {d} |")
    out.append(f"| **合计（含缓冲 {int(r['buffer_ratio']*100)}%）** | **{r['buffered_man_days']}** |")
    out.append("")
    p = r["productivity"]
    out.append(
        f"> 参数：设计 {p['case_design_per_day']} 条/人天、执行 {p['case_execution_per_day']} 条/人天、"
        f"回归 {p['regression_per_day']} 条/人天（已按聚合用例口径标定）"
    )
    out.append("")
    if r["mode"] == "given_team":
        out.append("### 人员与周期")
        out.append("")
        out.append(f"- 投入人数：**{r['team_size']} 人**")
        out.append(f"- 预计测试周期：**{r['calendar_days']} 自然日（约 {r['weeks']} 周）**")
    elif r["mode"] == "given_days":
        out.append("### 人员与周期")
        out.append("")
        out.append(f"- 目标周期：**{r['target_days']} 自然日（约 {r['weeks']} 周）**")
        out.append(f"- 所需投入人数：**{r['required_team_size']} 人**")
    else:
        out.append("### 人员与周期")
        out.append("")
        out.append(f"- 总工作量：**{r['buffered_man_days']} 人天**（提供 team_size 算周期，提供 target_days 算人数）")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="qa-suite · 周期与人员换算")
    parser.add_argument("--input", help="输入 JSON 文件（缺省从 stdin 读）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            inputs = json.load(f)
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            print(
                '用法：echo \'{"total_cases": 340, "team_size": 4}\' | python3 scripts/estimate.py',
                file=sys.stderr,
            )
            sys.exit(1)
        inputs = json.loads(raw)

    try:
        cfg = load_config(inputs.get("config_path"))
        result = estimate(inputs, cfg)
    except (KeyError, ValueError) as e:
        print(f"输入非法：{e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_markdown(result))


if __name__ == "__main__":
    main()