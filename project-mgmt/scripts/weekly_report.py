#!/usr/bin/env python3
"""
项目周报自动生成。

用法:
  python3 weekly_report.py --base-token <token> --project-name <项目名> [--week-of YYYY-MM-DD]

输出 markdown 周报到 stdout。
"""

import argparse
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import _report_helpers as h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-token", required=True)
    ap.add_argument("--project-name", required=True)
    ap.add_argument("--week-of", help="本周内任意日期(YYYY-MM-DD),默认今天")
    args = ap.parse_args()

    # 计算本周区间(周一到周日)
    if args.week_of:
        ref = datetime.strptime(args.week_of, "%Y-%m-%d")
    else:
        ref = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    monday = ref - timedelta(days=ref.weekday())
    sunday = monday + timedelta(days=6)
    next_monday = sunday + timedelta(days=1)
    next_sunday = next_monday + timedelta(days=6)

    # 找任务表 + 拉数据
    table = h.find_task_table(args.base_token, args.project_name)
    fields = ["任务编号", "任务名称", "任务级别", "负责人", "状态",
              "优先级", "进度", "计划完成日期", "实际完成日期",
              "风险与阻塞", "最近更新", "所属里程碑", "所属项目名称"]
    project_filter = args.project_name if table["arch"] == "A" else None
    tasks = h.fetch_tasks(args.base_token, table["id"], fields, project_filter)

    # 分类统计
    leaf_tasks = [t for t in tasks if h.is_leaf(t)]
    total_leaves = len(leaf_tasks)

    completed_total = sum(1 for t in leaf_tasks if h.parse_select(t.get("状态")) == "已完成")
    completion_rate = round(completed_total / total_leaves * 100) if total_leaves else 0

    # 本周完成的(实际完成日期在本周区间)
    completed_this_week = []
    for t in leaf_tasks:
        actual = h.parse_date(t.get("实际完成日期"))
        if actual and monday <= actual <= sunday:
            completed_this_week.append(t)

    # 进行中
    in_progress = [t for t in leaf_tasks
                   if h.parse_select(t.get("状态")) == "进行中"]

    # 阻塞
    blocked = [t for t in leaf_tasks
               if h.parse_select(t.get("状态")) == "阻塞"]

    # 延期(过期未完成)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    delayed = []
    for t in leaf_tasks:
        d = h.days_overdue(t, today)
        if d is not None and d > 0:
            delayed.append({**t, "_overdue": d})

    # 下周到期
    next_week_due = []
    for t in leaf_tasks:
        if not h.is_active(t):
            continue
        plan = h.parse_date(t.get("计划完成日期"))
        if plan and next_monday <= plan <= next_sunday:
            next_week_due.append(t)

    # 里程碑达成
    milestone_done = []
    for t in tasks:
        if h.parse_select(t.get("任务级别")) == "🏁 里程碑":
            actual = h.parse_date(t.get("实际完成日期"))
            if actual and monday <= actual <= sunday:
                milestone_done.append(t)

    # 输出 markdown
    lines = []
    lines.append(f"# {args.project_name} · 第 {ref.isocalendar()[1]} 周周报")
    lines.append(f"\n> 周期:{monday.strftime('%Y-%m-%d')} 至 {sunday.strftime('%Y-%m-%d')}\n")

    # 进度数字
    lines.append("## 📊 进度数字\n")
    lines.append(f"- 完成率:**{completion_rate}%**(累计 {completed_total}/{total_leaves})")
    lines.append(f"- 本周完成:**{len(completed_this_week)}** 个任务")
    lines.append(f"- 进行中:{len(in_progress)} 个")
    if blocked:
        lines.append(f"- 🟥 阻塞:{len(blocked)} 个")
    if delayed:
        lines.append(f"- ⚠️ 延期:{len(delayed)} 个")
    lines.append("")

    # 本周亮点
    lines.append("## ✅ 本周亮点\n")
    if milestone_done:
        for t in milestone_done:
            lines.append(f"- **完成里程碑**:{t.get('任务名称','')[:50]}")

    if completed_this_week:
        # 按负责人分组
        by_owner = defaultdict(list)
        for t in completed_this_week:
            owner = h.parse_user(t.get("负责人")) or "未分配"
            by_owner[owner].append(t)

        for owner, ts in sorted(by_owner.items(), key=lambda x: -len(x[1]))[:5]:
            lines.append(f"- **{owner}** 完成 {len(ts)} 个任务: " +
                         ", ".join(t.get("任务名称", "")[:25] for t in ts[:3]) +
                         (f"...等 {len(ts)} 项" if len(ts) > 3 else ""))
    else:
        lines.append("- (本周无完成任务)")
    lines.append("")

    # 风险与阻塞
    lines.append("## ⚠️ 风险与阻塞\n")
    risk_items = blocked + sorted(delayed, key=lambda x: -x.get("_overdue", 0))[:3]
    if risk_items:
        for t in risk_items[:5]:
            code = t.get("任务编号", "T-?")
            name = t.get("任务名称", "")[:40]
            owner = h.parse_user(t.get("负责人")) or "未分配"
            status = h.parse_select(t.get("状态"))
            extra = ""
            if "_overdue" in t:
                extra = f"(延期 {t['_overdue']} 天)"
            lines.append(f"- **{code}** {name} — {status}{extra} — {owner}")
            risk = t.get("风险与阻塞", "")
            if risk:
                lines.append(f"  > {risk[:80]}")
    else:
        lines.append("- ✅ 本周无重大阻塞")
    lines.append("")

    # 下周计划
    lines.append("## 📅 下周计划\n")
    lines.append(f"- {next_monday.strftime('%Y-%m-%d')} 至 {next_sunday.strftime('%Y-%m-%d')}")
    lines.append(f"- 计划完成 **{len(next_week_due)}** 个任务")
    if next_week_due:
        # 按优先级排序展示前 5
        prio_order = {"P0-紧急": 0, "P1-高": 1, "P2-中": 2, "P3-低": 3, None: 4}
        sorted_due = sorted(next_week_due,
                            key=lambda t: prio_order.get(h.parse_select(t.get("优先级")), 4))
        lines.append("\n关键任务:")
        for t in sorted_due[:5]:
            owner = h.parse_user(t.get("负责人")) or "未分配"
            prio = h.parse_select(t.get("优先级")) or ""
            lines.append(f"- **{t.get('任务编号','?')}** {t.get('任务名称','')[:40]} — {prio} — {owner}")
    lines.append("")

    # 个人进展(本周更新过"最近更新"字段的人)
    update_by_owner = defaultdict(list)
    for t in leaf_tasks:
        if t.get("最近更新"):
            owner = h.parse_user(t.get("负责人")) or "未分配"
            update_by_owner[owner].append(t.get("最近更新", "")[:60])

    if update_by_owner:
        lines.append("## 👥 成员进展\n")
        for owner, updates in sorted(update_by_owner.items()):
            lines.append(f"**{owner}**:")
            for upd in updates[:2]:
                lines.append(f"  - {upd}")
        lines.append("")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
