#!/usr/bin/env python3
"""
报告类脚本共用 helper:从飞书空间读项目+任务数据。
被 weekly_report.py / risk_check.py / retrospective.py 共用。
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta


def cli(*args, check=True):
    """Run lark-cli base; return parsed JSON of stdout. 失败时打印完整诊断上下文。"""
    r = subprocess.run(
        ["lark-cli", "base", *args],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        if check:
            sys.stderr.write(f"\n❌ lark-cli 调用失败 (exit code {r.returncode})\n")
            sys.stderr.write(f"   命令: lark-cli base {' '.join(args)}\n")
            if r.stderr.strip():
                sys.stderr.write(f"   ─── stderr ───\n{r.stderr}\n")
            if r.stdout.strip():
                sys.stderr.write(f"   ─── stdout (lark-cli 把 API 错误的 JSON 通常放在这里) ───\n{r.stdout}\n")
            sys.exit(1)
        return None
    return json.loads(r.stdout) if r.stdout.strip() else {}


def find_task_table(base_token: str, project_name: str) -> dict:
    """根据项目名找到对应的任务表。

    B1 架构下任务表名格式 '任务表·<项目名>'。
    A 架构(共享)下任务表叫 '任务表',通过 所属项目名称 字段过滤。
    """
    r = cli("+table-list", "--base-token", base_token)
    tables = r["data"]["tables"]

    # B1 优先
    for t in tables:
        if t["name"] == f"任务表·{project_name}":
            return {"id": t["id"], "name": t["name"], "arch": "B1"}

    # A 兜底
    for t in tables:
        if t["name"] == "任务表":
            return {"id": t["id"], "name": t["name"], "arch": "A"}

    sys.stderr.write(f"❌ 没找到匹配项目 '{project_name}' 的任务表\n")
    sys.exit(2)


def get_field_id_map(base_token: str, table_id: str) -> dict:
    """{字段名: 字段 id}."""
    r = cli("+field-list", "--base-token", base_token, "--table-id", table_id)
    return {f["name"]: f["id"] for f in r["data"]["fields"]}


def get_field_order(base_token: str, table_id: str, want_fields: list) -> list:
    """以 want_fields 顺序拿数据,返回字段名列表(顺序就是 record-list 数据的列顺序)."""
    return list(want_fields)


def fetch_tasks(base_token: str, table_id: str, want_fields: list, project_filter: str = None) -> list:
    """读取任务数据,返回 [{field: value, ...}, ...]。

    project_filter:A 架构下用,值是项目名,过滤 所属项目名称 字段。
    """
    args = ["+record-list", "--base-token", base_token, "--table-id", table_id, "--limit", "500"]
    for f in want_fields:
        args.extend(["--field-id", f])

    r = cli(*args)
    rows = r["data"]["data"]

    tasks = []
    for row in rows:
        task = {}
        for i, fname in enumerate(want_fields):
            task[fname] = row[i] if i < len(row) else None
        # A 架构下过滤项目
        if project_filter and task.get("所属项目名称") != project_filter:
            continue
        tasks.append(task)
    return tasks


def parse_user(user_field):
    """user 字段解析为姓名,例如 [{'id': 'ou_xxx', 'name': '骆航'}] → '骆航'."""
    if not user_field:
        return None
    if isinstance(user_field, list) and user_field:
        return user_field[0].get("name", "未知")
    return str(user_field)


def parse_select(select_field):
    """单选/多选字段解析,'P0-紧急' 或 ['P0-紧急'] → 'P0-紧急'."""
    if not select_field:
        return None
    if isinstance(select_field, list):
        return select_field[0] if select_field else None
    return str(select_field)


def parse_date(date_str):
    """日期字符串 '2026-04-30 00:00:00' → datetime."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.split()[0], "%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def is_leaf(task):
    """判断是否叶子任务(📋 二级工作)。"""
    level = parse_select(task.get("任务级别"))
    return level == "📋 二级工作"


def is_active(task):
    """状态非 已完成 / 已取消。"""
    status = parse_select(task.get("状态"))
    return status not in ("已完成", "已取消")


def days_overdue(task, today=None):
    """计算延期天数(若计划完成日期 < today 且未完成,正数;否则 None)."""
    if not is_active(task):
        return None
    plan_date = parse_date(task.get("计划完成日期"))
    if not plan_date:
        return None
    today = today or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    diff = (today - plan_date).days
    return diff if diff > 0 else None


def days_to_deadline(task, today=None):
    """计算距 deadline 天数(正数=未到期,负数=已过期,None=无 deadline 或已完成)."""
    if not is_active(task):
        return None
    plan_date = parse_date(task.get("计划完成日期"))
    if not plan_date:
        return None
    today = today or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return (plan_date - today).days
