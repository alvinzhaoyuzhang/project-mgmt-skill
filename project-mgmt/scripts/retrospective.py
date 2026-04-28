#!/usr/bin/env python3
"""
项目复盘报告自动生成。

用法:
  python3 retrospective.py --base-token <token> --project-name <项目名>

输出 markdown 复盘报告到 stdout。
"""

import argparse
import sys
from collections import Counter, defaultdict
from datetime import datetime

import _report_helpers as h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-token", required=True)
    ap.add_argument("--project-name", required=True)
    args = ap.parse_args()

    table = h.find_task_table(args.base_token, args.project_name)
    fields = ["任务编号", "任务名称", "任务级别", "负责人", "状态",
              "优先级", "进度", "开始日期", "计划完成日期", "实际完成日期",
              "风险与阻塞", "最近更新", "所属里程碑", "所属项目名称"]
    project_filter = args.project_name if table["arch"] == "A" else None
    tasks = h.fetch_tasks(args.base_token, table["id"], fields, project_filter)

    leaf_tasks = [t for t in tasks if h.is_leaf(t)]
    milestones = [t for t in tasks if h.parse_select(t.get("任务级别")) == "🏁 里程碑"]

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 总体数字
    total = len(leaf_tasks)
    completed = sum(1 for t in leaf_tasks if h.parse_select(t.get("状态")) == "已完成")
    cancelled = sum(1 for t in leaf_tasks if h.parse_select(t.get("状态")) == "已取消")
    completion_rate = round(completed / (total - cancelled) * 100) if (total - cancelled) else 0

    # 按时完成率
    on_time = 0
    total_with_dates = 0
    overdue_completed = []
    for t in leaf_tasks:
        if h.parse_select(t.get("状态")) != "已完成":
            continue
        plan = h.parse_date(t.get("计划完成日期"))
        actual = h.parse_date(t.get("实际完成日期"))
        if plan and actual:
            total_with_dates += 1
            if actual <= plan:
                on_time += 1
            else:
                overdue_completed.append({**t, "_overdue": (actual - plan).days})
    on_time_rate = round(on_time / total_with_dates * 100) if total_with_dates else 0

    # 阻塞累计(看 风险与阻塞 字段非空数量)
    has_blocker = sum(1 for t in leaf_tasks if t.get("风险与阻塞"))

    # 按里程碑分组
    by_milestone = defaultdict(lambda: {"total": 0, "done": 0})
    for t in leaf_tasks:
        ms = t.get("所属里程碑") or "未归属"
        by_milestone[ms]["total"] += 1
        if h.parse_select(t.get("状态")) == "已完成":
            by_milestone[ms]["done"] += 1

    # 成员贡献(按完成数)
    contributions = Counter()
    member_tasks = defaultdict(list)
    for t in leaf_tasks:
        owner = h.parse_user(t.get("负责人")) or "未分配"
        if h.parse_select(t.get("状态")) == "已完成":
            contributions[owner] += 1
        member_tasks[owner].append(t)

    # 优先级分布
    priority_dist = Counter()
    for t in leaf_tasks:
        prio = h.parse_select(t.get("优先级")) or "未定级"
        priority_dist[prio] += 1

    # 项目周期
    start_dates = [h.parse_date(t.get("开始日期")) for t in leaf_tasks
                   if t.get("开始日期")]
    end_dates = [h.parse_date(t.get("实际完成日期")) for t in leaf_tasks
                 if t.get("实际完成日期")]
    project_start = min(start_dates) if start_dates else None
    project_end = max(end_dates) if end_dates else None

    # 风险与教训(汇总所有 风险与阻塞 字段非空内容)
    blockers = []
    for t in leaf_tasks:
        risk = t.get("风险与阻塞")
        if risk and len(risk.strip()) > 5:
            blockers.append({"code": t.get("任务编号", "?"),
                             "name": t.get("任务名称", "")[:40],
                             "risk": risk[:200],
                             "owner": h.parse_user(t.get("负责人"))})

    # 输出 markdown
    lines = []
    lines.append(f"# {args.project_name} · 项目复盘报告")
    lines.append(f"\n> 生成于 {today.strftime('%Y-%m-%d')}\n")

    # 总体数字
    lines.append("## 📊 总体数据\n")
    if project_start and project_end:
        days = (project_end - project_start).days
        lines.append(f"- **项目周期**:{project_start.strftime('%Y-%m-%d')} → {project_end.strftime('%Y-%m-%d')}({days} 天)")
    lines.append(f"- **任务总数**:{total} 个叶子任务({len(milestones)} 个里程碑)")
    lines.append(f"- **完成率**:**{completion_rate}%** ({completed}/{total - cancelled},已取消 {cancelled})")
    lines.append(f"- **按时完成率**:{on_time_rate}% ({on_time}/{total_with_dates} 有时间数据的任务)")
    if has_blocker:
        lines.append(f"- **阻塞次数**:{has_blocker} 个任务遇到过阻塞")
    lines.append("")

    # 里程碑达成
    if by_milestone:
        lines.append("## 🏁 里程碑达成\n")
        lines.append("| 里程碑 | 完成 / 总数 | 达成率 |")
        lines.append("|---|---|---|")
        for ms, stats in by_milestone.items():
            rate = round(stats["done"] / stats["total"] * 100) if stats["total"] else 0
            emoji = "✅" if rate == 100 else ("🟢" if rate >= 80 else ("🟡" if rate >= 50 else "🔴"))
            lines.append(f"| {ms[:30]} | {stats['done']}/{stats['total']} | {emoji} {rate}% |")
        lines.append("")

    # 成员贡献
    if contributions:
        lines.append("## 👥 成员贡献\n")
        lines.append("| 成员 | 完成任务 | 占比 |")
        lines.append("|---|---|---|")
        total_done = sum(contributions.values())
        for owner, count in contributions.most_common():
            pct = round(count / total_done * 100) if total_done else 0
            lines.append(f"| {owner} | {count} | {pct}% |")
        lines.append("")

    # 优先级分布
    lines.append("## 🎯 任务优先级分布\n")
    for prio in ["P0-紧急", "P1-高", "P2-中", "P3-低", "未定级"]:
        if priority_dist.get(prio):
            count = priority_dist[prio]
            pct = round(count / total * 100) if total else 0
            lines.append(f"- {prio}:{count} 个 ({pct}%)")
    lines.append("")

    # 延期分析
    if overdue_completed:
        lines.append(f"## ⚠️ 延期任务({len(overdue_completed)} 个完成但超期)\n")
        for t in sorted(overdue_completed, key=lambda x: -x["_overdue"])[:10]:
            owner = h.parse_user(t.get("负责人"))
            lines.append(f"- **{t.get('任务编号','?')}** {t.get('任务名称','')[:40]} — 延期 {t['_overdue']} 天 — {owner}")
        if len(overdue_completed) > 10:
            lines.append(f"- ...及另 {len(overdue_completed)-10} 项")
        lines.append("")

    # 阻塞与教训
    if blockers:
        lines.append(f"## 🚧 阻塞回溯({len(blockers)} 项有阻塞记录)\n")
        for b in blockers[:8]:
            lines.append(f"- **{b['code']}** {b['name']} — {b['owner']}")
            lines.append(f"  > {b['risk']}")
        if len(blockers) > 8:
            lines.append(f"- ...及另 {len(blockers)-8} 项,详见任务表「风险与阻塞」字段")
        lines.append("")

    # 经验沉淀(模板)
    lines.append("## 💡 经验沉淀(待团队补充)\n")
    lines.append("以下是 skill 自动整理的项目数据线索,**真正的经验需要团队讨论后补充**:")
    lines.append("")
    lines.append("### 做得好的地方")
    lines.append("- (从'本周亮点'中提炼:哪些里程碑按时完成?哪些团队协作高效?)")
    lines.append("")
    lines.append("### 需要改进的地方")
    if on_time_rate < 70:
        lines.append(f"- ⚠️ **按时完成率仅 {on_time_rate}%** — 估时偏乐观?需求频繁变更?")
    if has_blocker > total * 0.2:
        lines.append(f"- ⚠️ **阻塞率高({has_blocker}/{total})** — 上下游协调机制?决策链条?")
    if not contributions:
        lines.append("- 数据不足,无法分析")
    else:
        max_owner, max_count = contributions.most_common(1)[0]
        if total_done and max_count / total_done > 0.5:
            lines.append(f"- ⚠️ **{max_owner} 一人完成 {max_count}/{total_done}** — 资源过度集中?需要分摊")
    lines.append("")

    lines.append("### 下次类似项目的复用建议")
    lines.append("- (此结构可作为同类项目的模板,新项目通过 skill 直接克隆)")
    lines.append("- (有效的工作包/任务拆分可沉淀到 skill 配置中)")
    lines.append("")

    # 数据出处
    lines.append("---")
    lines.append("\n*数据来源:飞书空间任务表;复盘报告 by project-mgmt skill。建议导出 PDF 后归档。*")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
