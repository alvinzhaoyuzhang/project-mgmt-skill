#!/usr/bin/env python3
"""
风险预警:列出严重风险 / 关注项 / 资源紧张。

用法:
  python3 risk_check.py --base-token <token> --project-name <项目名> [--severe-block-days 3]

输出 markdown 到 stdout。
"""

import argparse
import sys
from collections import Counter
from datetime import datetime, timedelta

import _report_helpers as h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-token", required=True)
    ap.add_argument("--project-name", required=True)
    ap.add_argument("--severe-block-days", type=int, default=3, help="阻塞超 N 天判严重(默认 3)")
    ap.add_argument("--near-deadline-days", type=int, default=3, help="临期警告窗口(默认 3 天内)")
    ap.add_argument("--owner-load-threshold", type=int, default=5, help="单人进行中任务超 N 个判资源紧张(默认 5)")
    args = ap.parse_args()

    # 找任务表
    table = h.find_task_table(args.base_token, args.project_name)
    fields = ["任务编号", "任务名称", "任务级别", "负责人", "状态", "优先级",
              "计划完成日期", "风险与阻塞", "更新时间", "所属项目名称"]
    project_filter = args.project_name if table["arch"] == "A" else None
    tasks = h.fetch_tasks(args.base_token, table["id"], fields, project_filter)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 分类
    severe = []
    watching = []
    overdue = []
    near_deadline = []
    owner_loads = Counter()

    for t in tasks:
        if not h.is_leaf(t):
            continue  # 只看叶子任务
        if not h.is_active(t):
            continue

        owner = h.parse_user(t.get("负责人")) or "未分配"
        owner_loads[owner] += 1

        status = h.parse_select(t.get("状态"))
        priority = h.parse_select(t.get("优先级")) or "P3-低"
        is_high_priority = priority.startswith(("P0", "P1"))

        # 已过期
        d_over = h.days_overdue(t, today)
        if d_over is not None:
            overdue.append({**t, "_overdue_days": d_over,
                            "_owner": owner, "_priority": priority})
            if is_high_priority and d_over >= args.severe_block_days:
                severe.append({**t, "_reason": f"已过期 {d_over} 天 + {priority}",
                               "_owner": owner})
            else:
                watching.append({**t, "_reason": f"已过期 {d_over} 天",
                                 "_owner": owner})

        # 阻塞
        if status == "阻塞":
            update_time = h.parse_date(t.get("更新时间"))
            block_days = (today - update_time).days if update_time else 0
            if block_days >= args.severe_block_days:
                severe.append({**t, "_reason": f"阻塞超 {block_days} 天",
                               "_owner": owner})
            else:
                watching.append({**t, "_reason": "阻塞中",
                                 "_owner": owner})

        # 临期未完成
        d_to = h.days_to_deadline(t, today)
        if d_to is not None and 0 <= d_to <= args.near_deadline_days:
            near_deadline.append({**t, "_days_left": d_to, "_owner": owner,
                                  "_priority": priority})

    # 资源紧张
    overloaded = [(owner, count) for owner, count in owner_loads.items()
                  if count >= args.owner_load_threshold]

    # 输出 markdown
    lines = []
    lines.append(f"# 风险预警 · {args.project_name}")
    lines.append(f"\n> 生成于 {today.strftime('%Y-%m-%d')} · 阈值:阻塞 ≥{args.severe_block_days}天=严重 / 临期窗口 ={args.near_deadline_days}天 / 单人 ≥{args.owner_load_threshold}任务=资源紧张\n")

    # 严重风险
    if severe:
        lines.append(f"## 🔴 严重风险({len(severe)} 项)\n")
        for t in severe:
            code = t.get("任务编号", "T-?")
            name = t.get("任务名称", "")[:40]
            lines.append(f"- **{code}** {name} — {t['_reason']} — 负责人:{t['_owner']}")
            risk = t.get("风险与阻塞", "")
            if risk:
                lines.append(f"  > {risk[:100]}")
        lines.append("")
    else:
        lines.append("## 🔴 严重风险:无 ✅\n")

    # 关注项
    if watching:
        lines.append(f"## 🟡 关注项({len(watching)} 项)\n")
        for t in watching[:10]:
            code = t.get("任务编号", "T-?")
            name = t.get("任务名称", "")[:40]
            lines.append(f"- **{code}** {name} — {t['_reason']} — 负责人:{t['_owner']}")
        if len(watching) > 10:
            lines.append(f"- ...及另 {len(watching)-10} 项")
        lines.append("")

    # 临期
    if near_deadline:
        lines.append(f"## ⏰ 临期任务({len(near_deadline)} 项,未来 {args.near_deadline_days} 天到期)\n")
        for t in sorted(near_deadline, key=lambda x: x["_days_left"]):
            code = t.get("任务编号", "T-?")
            name = t.get("任务名称", "")[:40]
            d = t["_days_left"]
            d_str = "今天" if d == 0 else f"{d} 天后"
            lines.append(f"- **{code}** {name} — {d_str} — {t['_priority']} — {t['_owner']}")
        lines.append("")

    # 资源紧张
    if overloaded:
        lines.append(f"## 📊 资源紧张({len(overloaded)} 人)\n")
        for owner, count in sorted(overloaded, key=lambda x: -x[1]):
            avg = sum(owner_loads.values()) / len(owner_loads) if owner_loads else 1
            lines.append(f"- **{owner}**:进行中 {count} 任务({count/avg:.1f}× 团队均值)")
        lines.append("")

    # 总结建议
    lines.append("## 建议")
    if severe:
        lines.append("- 🔴 **优先处理严重风险**:跟严重风险任务的负责人 1:1 同步,看能不能拆任务/换人/调期")
    if overloaded:
        names = [o[0] for o in overloaded]
        lines.append(f"- 📊 **重新分配**:{', '.join(names)} 手上任务过多,考虑转给其他人")
    if not severe and not overloaded:
        lines.append("- ✅ 项目整体健康,无需特别处理")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
