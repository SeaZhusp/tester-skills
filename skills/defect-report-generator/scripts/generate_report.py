#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a self-contained HTML test defect report from a CSV defect/task list.

Usage:
    python3 generate_report.py <input.csv> [-o output.html] [--title "报告标题"]
                                      [--project "项目名"] [--period "起 ~ 止"]

Design goals:
  * Standard library only (csv/re/math/html/argparse) -> no pip, no network.
  * Self-contained HTML: inline SVG donut + CSS bars, no CDN -> opens offline.
  * Schema-tolerant: auto-detects status/title/owner/module/overdue/id columns.
"""
import csv
import re
import math
import html
import sys
import os
import argparse
import datetime

# --------------------------------------------------------------------------
# Status canonicalisation (map any raw status text into a fixed 6-bucket model)
# --------------------------------------------------------------------------
CANON_ORDER = ["已验收", "已拒绝", "已修复", "修复中", "待确认", "其他"]
CANON_COLOR = {
    "已验收": "#22a06b",
    "已拒绝": "#9ca3af",
    "已修复": "#3b82f6",
    "修复中": "#f59e0b",
    "待确认": "#a855f7",
    "其他": "#64748b",
}
OPEN_CANON = {"已修复", "修复中", "待确认", "其他"}  # not yet closed from QA view

CANON_RULES = [
    ("已验收", ["已验收", "已关闭", "验收", "closed", "verified", "已解决", "fixed and verified"]),
    ("已拒绝", ["已拒绝", "拒绝", "rejected", "wontfix", "不予修复", "invalid", "不是缺陷", "设计如此", "duplicate", "重复", "不修复"]),
    ("修复中", ["修复中", "处理中", "进行中", "in progress", "开发中", "open-progress"]),
    ("已修复", ["已修复", "修复", "fixed", "resolved"]),
    ("待确认", ["待确认", "待处理", "待验证", "待修复", "to confirm", "pending", "新建", "打开", "重新打开", "待"]),
]


def classify(raw):
    s = (raw or "").strip()
    for canon, kws in CANON_RULES:
        for k in kws:
            if k in s:
                return canon
    return "其他"


# --------------------------------------------------------------------------
# Column auto-detection
# --------------------------------------------------------------------------
def detect_columns(headers):
    low = [(h or "").strip().lower() for h in headers]

    def find(*keys):
        for i, h in enumerate(low):
            for k in keys:
                if k in h:
                    return i
        return -1

    return {
        "status": find("状态", "status"),
        "title": find("标题", "title", "名称", "summary", "主题", "描述"),
        "owner": find("负责人", "处理人", "owner", "assignee", "处理者", "经办"),
        "module": find("模块", "module"),
        "overdue": find("逾期", "overdue", "late"),
        "id": find("任务id", "缺陷id", "bug id", "id", "编号", "序号"),
        "start": find("开始", "start"),
        "end": find("截止", "due", "完成日期", "结束"),
        "project": find("项目", "project"),
    }


def extract_module(title):
    m = re.search(r"[【\[]([^】\]]+)[\]】]", title or "")
    return m.group(1).strip() if m else ""


def read_rows(path):
    last_err = None
    for enc in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            with open(path, encoding=enc) as f:
                rows = list(csv.DictReader(f))
                if rows:
                    return rows
        except UnicodeDecodeError as e:
            last_err = e
    if last_err:
        raise last_err
    raise RuntimeError("无法读取文件或文件为空: " + path)


# --------------------------------------------------------------------------
# Chart builders (no external libs)
# --------------------------------------------------------------------------
def polar(cx, cy, r, ang):
    a = math.radians(ang)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def donut_segments(values, colors, cx=110, cy=110, R=100, r=62):
    total_v = sum(values) or 1
    segs = []
    ang = -90.0
    for v, c in zip(values, colors):
        if v <= 0:
            continue
        frac = v / total_v
        a0, a1 = ang, ang + frac * 360.0
        ang = a1
        osx, osy = polar(cx, cy, R, a0)
        oex, oey = polar(cx, cy, R, a1)
        iex, iey = polar(cx, cy, r, a1)
        isx, isy = polar(cx, cy, r, a0)
        large = 1 if (a1 - a0) > 180 else 0
        path = (f"M {osx:.2f} {osy:.2f} A {R} {R} 0 {large} 1 {oex:.2f} {oey:.2f} "
                f"L {iex:.2f} {iey:.2f} A {r} {r} 0 {large} 0 {isx:.2f} {isy:.2f} Z")
        segs.append((path, c))
    return segs


def bar_chart(data, color="#3b82f6", maxv=None, suffix=""):
    maxv = maxv or max((v for _, v in data), default=1) or 1
    out = []
    for name, v in data:
        pct = v / maxv * 100
        out.append(
            f'<div class="bar-row"><div class="bar-label" title="{html.escape(str(name))}">'
            f"{html.escape(str(name))}</div>"
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div>'
            f'<span class="bar-val">{v}{suffix}</span></div></div>'
        )
    return "\n".join(out)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Generate HTML test defect report from CSV")
    ap.add_argument("input", help="path to CSV defect/task list")
    ap.add_argument("-o", "--output", help="output HTML path (default: <input>_测试缺陷报告.html)")
    ap.add_argument("--title", help="report title override")
    ap.add_argument("--project", help="project name override")
    ap.add_argument("--period", help='test period, e.g. "2026-07-10 ~ 2026-07-31"')
    args = ap.parse_args()

    rows = read_rows(args.input)
    headers = list(rows[0].keys())
    col = detect_columns(headers)

    if col["status"] < 0:
        sys.exit("错误：未找到状态列（表头需含 '状态'/'status'）。请检查 CSV 表头。")

    total = len(rows)
    canon_counter = {c: 0 for c in CANON_ORDER}
    raw_status_counter = {}
    module_counter = {}
    owner_counter = {}
    module_canon = {}
    owner_canon = {}
    overdue = []
    open_defects = []

    for r in rows:
        raw = r[headers[col["status"]]]
        canon = classify(raw)
        canon_counter[canon] = canon_counter.get(canon, 0) + 1
        raw_status_counter[raw] = raw_status_counter.get(raw, 0) + 1

        title = r[headers[col["title"]]] if col["title"] >= 0 else ""
        mod = extract_module(title)
        if not mod and col["module"] >= 0:
            mod = (r[headers[col["module"]]] or "").strip()
        if not mod:
            mod = "未分类"

        owner = (r[headers[col["owner"]]] if col["owner"] >= 0 else "") or "未知"
        tid = (r[headers[col["id"]]] if col["id"] >= 0 else "") or ""

        module_counter[mod] = module_counter.get(mod, 0) + 1
        module_canon.setdefault(mod, {})
        module_canon[mod][canon] = module_canon[mod].get(canon, 0) + 1
        owner_counter[owner] = owner_counter.get(owner, 0) + 1
        owner_canon.setdefault(owner, {})
        owner_canon[owner][canon] = owner_canon[owner].get(canon, 0) + 1

        if col["overdue"] >= 0:
            ov = (r[headers[col["overdue"]]] or "").strip()
            if ov and ov != "完成" and ("逾期" in ov or "late" in ov.lower() or "overdue" in ov.lower()):
                overdue.append(r)
        if canon in OPEN_CANON:
            open_defects.append((r, canon, tid, mod, title, owner))

    # project / period meta
    project = args.project
    if not project and col["project"] >= 0:
        seen = [ (r[headers[col["project"]]] or "").strip() for r in rows ]
        seen = [s for s in seen if s]
        project = seen[0] if seen else ""
    period = args.period
    if not period and (col["start"] >= 0 or col["end"] >= 0):
        starts = [ (r[headers[col["start"]]] if col["start"] >= 0 else "") for r in rows ]
        ends = [ (r[headers[col["end"]]] if col["end"] >= 0 else "") for r in rows ]
        s = next((x.strip() for x in starts if x and x.strip()), "")
        e = next((x.strip() for x in ends if x and x.strip()), "")
        if s or e:
            period = f"{s or '?'} ~ {e or '?'}"

    resolved = canon_counter["已验收"] + canon_counter["已拒绝"]
    closed_verified = canon_counter["已验收"]
    open_count = sum(canon_counter.get(c, 0) for c in OPEN_CANON)
    total = max(total, 1)

    def pct(n):
        return f"{n / total * 100:.1f}%"

    # donut
    donut_vals = [canon_counter[c] for c in CANON_ORDER]
    donut_cols = [CANON_COLOR[c] for c in CANON_ORDER]
    donut = donut_segments(donut_vals, donut_cols)
    donut_paths = "\n".join(f'<path d="{p}" fill="{c}"></path>' for p, c in donut)
    legend_html = "".join(
        f'<div class="legend-item"><span class="dot" style="background:{CANON_COLOR[c]}"></span>'
        f'{c} <b>{canon_counter[c]}</b> <span class="lp">{pct(canon_counter[c])}</span></div>'
        for c in CANON_ORDER if canon_counter[c] > 0
    )

    # module bars (top 10 + 其他)
    mod_sorted = sorted(module_counter.items(), key=lambda x: (-x[1], x[0]))
    top_modules = mod_sorted[:10]
    others_count = sum(v for _, v in mod_sorted[10:])
    # 其他模块是聚合项，可能超过单个模块最大值，所以 maxv 要同时考虑两者，避免条形图溢出
    maxv_module = max(max((v for _, v in top_modules), default=1), others_count, 1)
    module_bars = bar_chart(top_modules, color="#3b82f6", maxv=maxv_module)
    if others_count:
        w = others_count / maxv_module * 100
        module_bars += (f'<div class="bar-row"><div class="bar-label">其他模块</div>'
                        f'<div class="bar-track"><div class="bar-fill" style="width:{w:.1f}%;background:#cbd5e1"></div>'
                        f'<span class="bar-val">{others_count}</span></div></div>')

    # owner bars
    owner_sorted = sorted(owner_counter.items(), key=lambda x: (-x[1], x[0]))
    owner_bars = bar_chart(owner_sorted, color="#0ea5e9")

    # module detail table
    mod_table = ""
    for mod, cnt in mod_sorted:
        open_mod = sum(module_canon[mod].get(c, 0) for c in OPEN_CANON)
        cells = "".join(
            f'<td class="st st-{c}">{module_canon[mod].get(c, 0)}</td>' for c in CANON_ORDER
        )
        badge = (f'<span class="badge-open">未关闭 {open_mod}</span>' if open_mod
                 else '<span class="badge-ok">已清</span>')
        mod_table += (f'<tr><td class="mod-name">{html.escape(mod)}</td><td>{cnt}</td>'
                       f'{cells}<td>{badge}</td></tr>')

    # open defects table
    open_defects.sort(key=lambda x: (CANON_ORDER.index(x[1]), x[3]))
    open_table = ""
    for r, canon, tid, mod, title, owner in open_defects:
        end = (r[headers[col["end"]]] if col["end"] >= 0 else "") or ""
        open_table += (f'<tr><td>{html.escape(tid)}</td><td class="mod-name">{html.escape(mod)}</td>'
                       f'<td class="title-cell">{html.escape(title)}</td>'
                       f'<td><span class="pill" style="background:{CANON_COLOR[canon]}">{html.escape(canon)}</span></td>'
                       f'<td>{html.escape(owner)}</td><td>{html.escape(end)}</td></tr>')

    # overdue table
    overdue_html = ""
    for r in overdue:
        overdue_html += (f'<tr><td>{html.escape(tid_of(r, headers, col))}</td>'
                          f'<td class="title-cell">{html.escape((r[headers[col["title"]]] if col["title"] >= 0 else ""))}</td>'
                          f'<td>{html.escape((r[headers[col["owner"]]] if col["owner"] >= 0 else "") or "未知")}</td>'
                          f'<td>{html.escape((r[headers[col["start"]]] if col["start"] >= 0 else "") or "")}</td>'
                          f'<td>{html.escape((r[headers[col["end"]]] if col["end"] >= 0 else "") or "")}</td>'
                          f'<td class="over">{html.escape((r[headers[col["overdue"]]] or "").strip())}</td></tr>')

    today = datetime.date.today().strftime("%Y-%m-%d")
    report_title = args.title or "测试缺陷报告"
    meta_parts = []
    if project:
        meta_parts.append(f"<span><b>项目：</b>{html.escape(project)}</span>")
    if period:
        meta_parts.append(f"<span><b>测试周期：</b>{html.escape(period)}</span>")
    meta_parts.append(f"<span><b>报告生成：</b>{today}</span>")
    meta_parts.append(f"<span><b>缺陷总数：</b>{total}</span>")
    meta_html = "".join(meta_parts)

    reject_rate = canon_counter["已拒绝"] / total * 100
    resolved_rate = resolved / total * 100
    closed_rate = closed_verified / total * 100

    th_cells = "".join(f"<th>{c}</th>" for c in CANON_ORDER)

    HTML = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(report_title)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
         color:#1f2937; background:#f4f6fb; line-height:1.6; }}
  .wrap {{ max-width: 1080px; margin:0 auto; padding:32px 24px 64px; }}
  header.top {{ background: linear-gradient(135deg,#1e3a8a,#2563eb); color:#fff; border-radius:16px;
         padding:28px 32px; box-shadow:0 8px 24px rgba(30,58,138,.25); }}
  header.top h1 {{ margin:0 0 6px; font-size:26px; letter-spacing:.5px; }}
  header.top .sub {{ opacity:.9; font-size:14px; }}
  header.top .meta {{ margin-top:14px; display:flex; flex-wrap:wrap; gap:10px 26px; font-size:13px; }}
  header.top .meta span b {{ font-weight:600; }}
  .cards {{ display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin:24px 0; }}
  .card {{ background:#fff; border-radius:12px; padding:18px 16px; box-shadow:0 2px 10px rgba(0,0,0,.05);
          border:1px solid #eef1f6; text-align:center; }}
  .card .num {{ font-size:30px; font-weight:700; }}
  .card .lbl {{ font-size:13px; color:#6b7280; margin-top:4px; }}
  .card.c1 .num {{ color:#2563eb; }} .card.c2 .num {{ color:#22a06b; }}
  .card.c3 .num {{ color:#9ca3af; }} .card.c4 .num {{ color:#f59e0b; }}
  .card.c5 .num {{ color:#ef4444; }}
  section {{ background:#fff; border-radius:14px; padding:24px 26px; margin:20px 0;
            box-shadow:0 2px 10px rgba(0,0,0,.05); border:1px solid #eef1f6; }}
  section h2 {{ font-size:18px; margin:0 0 16px; padding-left:12px; border-left:4px solid #2563eb; }}
  .grid2 {{ display:grid; grid-template-columns: 280px 1fr; gap:24px; align-items:center; }}
  .donut {{ text-align:center; }}
  .donut svg {{ width:220px; height:220px; }}
  .donut .center {{ font-size:13px; fill:#374151; }}
  .legend {{ display:flex; flex-direction:column; gap:8px; }}
  .legend-item {{ display:flex; align-items:center; gap:8px; font-size:14px; }}
  .dot {{ width:12px; height:12px; border-radius:3px; display:inline-block; }}
  .legend-item b {{ min-width:28px; text-align:right; }}
  .lp {{ color:#9ca3af; font-size:12px; }}
  .bar-row {{ display:flex; align-items:center; margin:7px 0; font-size:13px; }}
  .bar-label {{ width:100px; flex:none; text-align:right; padding-right:10px; color:#374151;
               overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .bar-track {{ flex:1; background:#f1f5f9; border-radius:6px; position:relative; height:22px; }}
  .bar-fill {{ height:22px; border-radius:6px; min-width:2px; max-width:100%; }}
  .bar-val {{ position:absolute; right:8px; top:0; line-height:22px; font-size:12px; color:#334155; font-weight:600; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; margin-top:4px; }}
  th, td {{ padding:9px 10px; border-bottom:1px solid #eef1f6; text-align:center; }}
  th {{ background:#f8fafc; color:#475569; font-weight:600; }}
  td.t-left, th.t-left {{ text-align:left; }}
  .mod-name {{ text-align:left; font-weight:600; color:#334155; white-space:nowrap; }}
  .title-cell {{ text-align:left; max-width:360px; }}
  .st {{ font-weight:600; }}
  .st-已验收 {{ color:#22a06b; }} .st-已拒绝 {{ color:#9ca3af; }} .st-已修复 {{ color:#3b82f6; }}
  .st-修复中 {{ color:#f59e0b; }} .st-待确认 {{ color:#a855f7; }} .st-其他 {{ color:#64748b; }}
  .badge-ok {{ color:#22a06b; font-size:12px; }} .badge-open {{ color:#ef4444; font-size:12px; font-weight:600; }}
  .pill {{ color:#fff; padding:2px 10px; border-radius:20px; font-size:12px; }}
  .over {{ color:#ef4444; font-weight:600; }}
  .note {{ background:#fffbeb; border:1px solid #fde68a; border-radius:10px; padding:14px 18px;
          font-size:13px; color:#92400e; }}
  .concl li {{ margin:6px 0; }}
  .two-col {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
  footer {{ text-align:center; color:#9ca3af; font-size:12px; margin-top:30px; }}
  @media (max-width:760px) {{ .cards{{grid-template-columns:repeat(2,1fr);}} .grid2{{grid-template-columns:1fr;}}
          .two-col{{grid-template-columns:1fr;}} }}
</style></head>
<body><div class="wrap">

<header class="top">
  <h1>{html.escape(report_title)}</h1>
  <div class="sub">基于缺陷/任务清单的测试质量分析</div>
  <div class="meta">{meta_html}</div>
</header>

<div class="cards">
  <div class="card c1"><div class="num">{total}</div><div class="lbl">缺陷总数</div></div>
  <div class="card c2"><div class="num">{closed_verified}</div><div class="lbl">已验收关闭 ({pct(closed_verified)})</div></div>
  <div class="card c3"><div class="num">{canon_counter["已拒绝"]}</div><div class="lbl">已拒绝 ({pct(canon_counter["已拒绝"])})</div></div>
  <div class="card c4"><div class="num">{open_count}</div><div class="lbl">未关闭 ({pct(open_count)})</div></div>
  <div class="card c5"><div class="num">{len(overdue)}</div><div class="lbl">逾期任务</div></div>
</div>

<section>
  <h2>一、缺陷状态分布</h2>
  <div class="grid2">
    <div class="donut">
      <svg viewBox="0 0 220 220">
        {donut_paths}
        <text x="110" y="104" text-anchor="middle" class="center" style="font-size:15px;font-weight:700">{total}</text>
        <text x="110" y="124" text-anchor="middle" class="center" style="font-size:11px">缺陷总数</text>
      </svg>
    </div>
    <div class="legend">{legend_html}</div>
  </div>
  <div class="note" style="margin-top:18px">
    解决进度：已验收({closed_verified}) + 已拒绝({canon_counter["已拒绝"]}) = <b>{resolved}</b> 项已处理完毕，
    解决率 <b>{resolved_rate:.1f}%</b>；其中经测试确认关闭率 <b>{closed_rate:.1f}%</b>。
    仍有 <b>{open_count}</b> 项未关闭（已修复 {canon_counter["已修复"]}、修复中 {canon_counter["修复中"]}、待确认 {canon_counter["待确认"]}）。
  </div>
</section>

<section>
  <h2>二、缺陷模块分布</h2>
  <p style="font-size:13px;color:#6b7280;margin-top:0">按功能模块统计缺陷数量（取数量最多的前 10 个模块，其余合并为"其他模块"）。</p>
  {module_bars}
</section>

<section>
  <h2>三、各模块状态明细</h2>
  <table>
    <thead><tr><th class="t-left">模块</th><th>总数</th>{th_cells}<th>清况</th></tr></thead>
    <tbody>{mod_table}</tbody>
  </table>
</section>

<section>
  <h2>四、负责人分布</h2>
  {owner_bars}
</section>

<section>
  <h2>五、未完成（未关闭）缺陷清单</h2>
  <p style="font-size:13px;color:#6b7280;margin-top:0">以下 {open_count} 项仍处于未关闭状态，需在后续迭代中跟进处理与回归验证。</p>
  <table>
    <thead><tr><th>任务ID</th><th>模块</th><th class="t-left">标题</th><th>状态</th><th>负责人</th><th>计划截止</th></tr></thead>
    <tbody>{open_table}</tbody>
  </table>
</section>

<section>
  <h2>六、逾期情况</h2>
  {('<table><thead><tr><th>任务ID</th><th class="t-left">标题</th><th>负责人</th><th>计划开始</th><th>计划截止</th><th>逾期情况</th></tr></thead>'
    f'<tbody>{overdue_html}</tbody></table>') if overdue else '<p style="font-size:13px;color:#6b7280">本次清单中无逾期任务。</p>'}
</section>

<section>
  <h2>七、测试结论与建议</h2>
  <div class="two-col">
    <div>
      <h3 style="font-size:15px;margin:0 0 8px">结论</h3>
      <ul class="concl">
        <li>本轮共记录缺陷 <b>{total}</b> 项，整体解决率 <b>{resolved_rate:.1f}%</b>，测试确认关闭率 <b>{closed_rate:.1f}%</b>。</li>
        <li>缺陷最集中模块：<b>{mod_sorted[0][0]}</b>（{mod_sorted[0][1]} 项），建议作为后续回归重点。</li>
        <li>仍有 <b>{open_count}</b> 项未关闭，需在截止前完成验证或处理。</li>
        <li>逾期 <b>{len(overdue)}</b> 项，进度风险{'可控' if len(overdue) <= 2 else '需关注'}。</li>
        <li>已拒绝 {canon_counter["已拒绝"]} 项（占比 {reject_rate:.1f}%），建议复盘以减少无效提单。</li>
      </ul>
    </div>
    <div>
      <h3 style="font-size:15px;margin:0 0 8px">改进建议</h3>
      <ul class="concl">
        <li><b>尽快收敛未关闭缺陷：</b>优先验证"已修复"的 {canon_counter["已修复"]} 项，推动"修复中/待确认"各 {canon_counter["修复中"]}/{canon_counter["待确认"]} 项明确结论。</li>
        <li><b>重点模块专项回归：</b>对缺陷最多的模块补充针对性用例。</li>
        <li><b>规范缺陷提交：</b>减少"已拒绝"比例，提交前自查是否重复/可复现/符合预期设计。</li>
        <li><b>补充缺陷属性：</b>建议增加严重程度/优先级/发现版本字段，便于量化风险与排期。</li>
        <li><b>进度监控：</b>对临期任务设置预警，避免再次出现逾期。</li>
      </ul>
    </div>
  </div>
</section>

<section>
  <h2>八、数据说明与局限</h2>
  <div class="note">
    <ul style="margin:0;padding-left:18px">
      <li>本报告由 <b>defect-report-generator</b> 技能自动生成，源文件共 {total} 条记录。</li>
      <li>状态映射：<b>已验收</b>=测试确认关闭；<b>已拒绝</b>=开发拒绝/非缺陷（视为已处理）；<b>已修复</b>=待验证；<b>修复中/待确认</b>=未关闭。无法归类的状态计入"其他"。</li>
      <li>模块由任务标题首段【】/[]自动解析；若无括号则尝试使用模块列，否则记"未分类"。</li>
      <li>原始数据若缺少严重程度、优先级、发现/关闭时间等字段，本报告未做相应分析。</li>
    </ul>
  </div>
</section>

<footer>报告由 defect-report-generator 技能生成 · 数据基准日 {today} · 共 {total} 条缺陷记录</footer>
</div></body></html>'''

    out = args.output or (os.path.splitext(args.input)[0] + "_测试缺陷报告.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(HTML)
    print(f"OK 报告已生成: {out}")
    print(f"总数={total} 已验收={canon_counter['已验收']} 已拒绝={canon_counter['已拒绝']} "
          f"已修复={canon_counter['已修复']} 修复中={canon_counter['修复中']} 待确认={canon_counter['待确认']} 其他={canon_counter['其他']}")
    print(f"未关闭={open_count} 逾期={len(overdue)} 解决率={resolved_rate:.1f}% 关闭率={closed_rate:.1f}%")


def tid_of(r, headers, col):
    if col["id"] >= 0:
        return (r[headers[col["id"]]] or "").strip()
    return ""


if __name__ == "__main__":
    main()
