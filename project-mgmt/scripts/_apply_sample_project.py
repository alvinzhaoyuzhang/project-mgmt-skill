#!/usr/bin/env python3
"""
把 configs/sample_project.json 写入飞书空间,作为示例项目数据。

bootstrap.sh 末尾自动调用,让用户首次打开空间能看到完整项目管理形态:
- dashboard 5 图表立刻有数据可视化
- 看到树状任务层级 + 状态/优先级/日期分布的真实例子
- 当作"使用范本"参照建自己的项目

幂等:
  - 项目主表里如果已有"示例项目:Q2新产品发布"项目记录 → 跳过整段
  - 用户想重新生成需先删该项目记录(在飞书 UI 删 1 行)再重跑

用法:
  python3 _apply_sample_project.py --base-token <token> [--task-table-name 任务表]

  bootstrap.sh 默认调用,可加 --no-sample 跳过。
"""

import argparse
import json
import os
import subprocess
import sys
import time

INTERNAL_ERROR_PATTERNS = ["800008006", "internal_error"]
RATE_LIMIT_PATTERNS = ["800004135", "limited"]
INTER_LAYER_SLEEP_SEC = 1.5  # 各层之间间隔,避免速率限制


def cli(*args, check=True):
    r = subprocess.run(
        ["lark-cli", "base", *args],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        if check:
            sys.stderr.write(f"\n❌ lark-cli 失败 (exit {r.returncode})\n")
            sys.stderr.write(f"   命令: lark-cli base {' '.join(args)}\n")
            if r.stderr.strip():
                sys.stderr.write(f"   stderr:\n{r.stderr}\n")
            if r.stdout.strip():
                sys.stderr.write(f"   stdout:\n{r.stdout}\n")
            sys.exit(1)
        return None
    return json.loads(r.stdout) if r.stdout.strip() else {}


def find_table_id(base_token, table_name):
    r = cli("+table-list", "--base-token", base_token)
    for t in r["data"]["tables"]:
        if t["name"] == table_name:
            return t["id"]
    return None


def project_exists(base_token, project_table_id, project_name):
    """幂等检测 — 查项目主表是否已有同名 record。"""
    r = cli("+record-list", "--base-token", base_token, "--table-id", project_table_id, "--limit", "500")
    data = r.get("data", {})
    fields_list = data.get("fields", [])
    rows = data.get("data", [])
    try:
        name_col = fields_list.index("项目名称")
    except ValueError:
        return False
    for row in rows:
        cell = row[name_col] if name_col < len(row) else None
        if isinstance(cell, list) and cell:
            cell = cell[0].get("text") if isinstance(cell[0], dict) else cell[0]
        if cell == project_name:
            return True
    return False


def date_to_ms(date_str):
    """'2026-04-15' → 13 位毫秒时间戳(飞书 datetime 字段格式)."""
    if not date_str:
        return None
    from datetime import datetime
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.timestamp() * 1000)


def insert_project_row(base_token, project_table_id, proj):
    """写入项目主表 1 行。"""
    fields = dict(proj["fields"])
    # 日期字段转毫秒戳
    for k in ["开始日期", "计划结束日期"]:
        if k in fields:
            fields[k] = date_to_ms(fields[k])

    payload = {"fields": list(fields.keys()), "rows": [list(fields.values())]}
    r = cli(
        "+record-batch-create",
        "--base-token", base_token, "--table-id", project_table_id,
        "--json", json.dumps(payload, ensure_ascii=False),
    )
    # lark-cli batch_create 返回 data.record_id_list(平行 data.data 列式)
    rids = r.get("data", {}).get("record_id_list", [])
    return rids[0] if rids else None


def task_to_field_dict(t, project_record_id, wbs_to_id, secrecy_level):
    """单个 task 转 fields dict(用于 batch payload 行)。"""
    fields = {
        "任务名称": t["name"],
        "任务级别": t["level"],
        "状态": t["status"],
        "优先级": t["priority"],
        "进度": t["progress"],
        "WBS编号": t["wbs"],
        "开始日期": date_to_ms(t.get("start_date")),
        "计划完成日期": date_to_ms(t.get("plan_end_date")),
        "实际完成日期": date_to_ms(t.get("actual_end_date")),
        "任务描述": t.get("description"),
        "交付物": t.get("delivery"),
        "风险与阻塞": t.get("blocker"),
        "最近更新": t.get("recent_update"),
    }
    if secrecy_level is not None:
        fields["任务保密等级"] = secrecy_level
    fields["所属项目"] = [{"id": project_record_id}]
    parent_wbs = t.get("parent_wbs")
    if parent_wbs and parent_wbs in wbs_to_id:
        fields["父任务"] = [{"id": wbs_to_id[parent_wbs]}]
    else:
        fields["父任务"] = None
    return fields


def insert_tasks_layered(base_token, task_table_id, tasks, project_record_id, secrecy_level):
    """
    按层级 BFS 顺序写任务,**每层一次 batch_create**(避免飞书 OpenAPI 速率限制)。
    层之间 sleep 1.5s。父任务 link 通过上一层的 wbs→record_id 映射构建。
    """
    wbs_to_id = {}

    # 按 level 分层
    levels = {
        "🎯 目标": [],
        "🏁 里程碑": [],
        "📦 一级工作": [],
        "📋 二级工作": [],
    }
    for t in tasks:
        if t["level"] in levels:
            levels[t["level"]].append(t)

    for level_name in ["🎯 目标", "🏁 里程碑", "📦 一级工作", "📋 二级工作"]:
        layer = levels[level_name]
        if not layer:
            continue

        print(f"  → 层 {level_name} ({len(layer)} 条)")

        # 每个任务转 fields dict(union 完整字段集)
        rows_dicts = [task_to_field_dict(t, project_record_id, wbs_to_id, secrecy_level) for t in layer]

        # 取所有 row 的字段名 union(确保 batch 列对齐)
        all_field_names = []
        seen = set()
        for d in rows_dicts:
            for k in d.keys():
                if k not in seen:
                    all_field_names.append(k)
                    seen.add(k)

        # 按统一列序构建 rows 数组,缺失字段填 None
        rows_array = [[d.get(fn) for fn in all_field_names] for d in rows_dicts]

        payload = {"fields": all_field_names, "rows": rows_array}
        r = cli(
            "+record-batch-create",
            "--base-token", base_token, "--table-id", task_table_id,
            "--json", json.dumps(payload, ensure_ascii=False),
        )
        rids = r.get("data", {}).get("record_id_list", [])
        if len(rids) != len(layer):
            sys.stderr.write(f"  ⚠️ 层 {level_name} 期望 {len(layer)} record_ids,实际拿到 {len(rids)}\n")
        for i, t in enumerate(layer):
            if i < len(rids):
                wbs_to_id[t["wbs"]] = rids[i]

        # 各层之间 sleep,避免速率限制
        time.sleep(INTER_LAYER_SLEEP_SEC)

    return wbs_to_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-token", required=True)
    ap.add_argument("--sample-config",
                    default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "..", "configs", "sample_project.json"),
                    help="sample_project.json 路径")
    ap.add_argument("--task-table-name", default="任务表",
                    help="任务表名(B1 用'任务表',B2 可能用'任务表·示例项目')")
    args = ap.parse_args()

    with open(args.sample_config, encoding="utf-8") as f:
        sample = json.load(f)

    proj = sample["project"]
    project_name = proj["fields"]["项目名称"]

    # 找表 id
    project_table_id = find_table_id(args.base_token, "项目主表")
    if not project_table_id:
        sys.stderr.write("❌ 没找到 '项目主表',跳过示例项目写入\n")
        sys.exit(1)
    task_table_id = find_table_id(args.base_token, args.task_table_name)
    if not task_table_id:
        sys.stderr.write(f"❌ 没找到 '{args.task_table_name}',跳过示例项目写入\n")
        sys.exit(1)

    # 幂等检测
    if project_exists(args.base_token, project_table_id, project_name):
        print(f"  ⚠️ 示例项目 '{project_name}' 已存在,跳过示例数据写入(避免重复)")
        print(f"  ℹ 如想重新生成,先在飞书 UI 删该行 + 删任务表里所有 WBS 以 1.x 开头的任务,再重跑")
        return

    # 检测保密等级字段是否存在
    proj_fields_resp = cli("+field-list", "--base-token", args.base_token, "--table-id", project_table_id)
    proj_field_names = {f["name"] for f in proj_fields_resp.get("data", {}).get("fields", [])}
    has_secrecy = "保密等级" in proj_field_names
    if not has_secrecy:
        # 工作区未启用分级,从 project payload 移除保密等级字段
        proj["fields"].pop("保密等级", None)
        secrecy_level = None
    else:
        secrecy_level = proj["fields"].get("保密等级", "L2 常规")

    # 1. 项目主表写入
    print(f"==> 写入示例项目记录:{project_name}")
    proj_record_id = insert_project_row(args.base_token, project_table_id, proj)
    if not proj_record_id:
        sys.stderr.write("❌ 项目记录写入失败(record_id 未返回)\n")
        sys.exit(1)
    print(f"    ✅ 项目记录 ID: {proj_record_id}")

    # 2. 任务按层级写入
    print(f"==> 写入示例任务({len(sample['tasks'])} 条,按层级)")
    wbs_to_id = insert_tasks_layered(
        args.base_token, task_table_id, sample["tasks"],
        proj_record_id, secrecy_level if has_secrecy else None,
    )
    print(f"    ✅ 共建 {len(wbs_to_id)} 条任务")

    print()
    print(f"🎉 示例项目数据写入完成!")
    print(f"   项目: {project_name}")
    print(f"   层级: 1 🎯 + 4 🏁 + 8 📦 + 12 📋 = 25 任务")
    print(f"   状态分布:已完成 + 进行中 + 阻塞 + 延期 + 未开始,各种各样")
    print()
    print(f"💡 现在打开 base,综合看板·模板 应该 5 个图表都有数据了。")
    print(f"   不喜欢这个示例?在飞书 UI 删项目主表的'{project_name}'行 + 任务表里所有 WBS=1.x 的任务即可。")


if __name__ == "__main__":
    main()
