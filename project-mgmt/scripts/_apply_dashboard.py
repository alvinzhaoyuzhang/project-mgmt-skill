#!/usr/bin/env python3
"""
按 configs/dashboard_template.json 在指定 Base 建综合看板,占位会被替换:
  <TASK_TABLE_NAME> → 任务表名(必须是 Base 内已存在的任务表名)
  <PROJECT_NAME>    → 项目名(用于 filter 所属项目名称 = ...)

bootstrap.sh / new-project.sh 共用。

用法:
  python3 _apply_dashboard.py \
    --base-token <token> \
    --dashboard-name "综合看板·模板" \
    --task-table-name "任务表" \
    --project-name "示例项目:Q2新产品发布" \
    --template configs/dashboard_template.json
"""

import argparse
import copy
import json
import subprocess
import sys


def cli(*args, check=True):
    r = subprocess.run(
        ["lark-cli", "base", *args],
        capture_output=True, text=True, check=check,
    )
    if r.returncode != 0 and check:
        sys.stderr.write(r.stderr)
        sys.exit(1)
    return json.loads(r.stdout) if r.stdout.strip() else {}


def substitute(obj, replacements: dict):
    """递归替换字符串占位。"""
    if isinstance(obj, dict):
        return {k: substitute(v, replacements) for k, v in obj.items()}
    if isinstance(obj, list):
        return [substitute(v, replacements) for v in obj]
    if isinstance(obj, str):
        out = obj
        for k, v in replacements.items():
            out = out.replace(k, v)
        return out
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-token", required=True)
    ap.add_argument("--dashboard-name", required=True)
    ap.add_argument("--task-table-name", required=True)
    ap.add_argument("--project-name", required=True)
    ap.add_argument("--template", required=True)
    args = ap.parse_args()

    with open(args.template, encoding="utf-8") as f:
        tpl = json.load(f)

    replacements = {
        "<TASK_TABLE_NAME>": args.task_table_name,
        "<PROJECT_NAME>": args.project_name,
    }

    # 1. 创建 dashboard
    r = cli("+dashboard-create", "--base-token", args.base_token, "--name", args.dashboard_name)
    dash_id = r["data"]["dashboard"]["dashboard_id"]
    print(f"  ✅ dashboard 创建: {args.dashboard_name} → {dash_id}")

    # 2. 串行建图表 block(text 留到最后)
    text_blocks = []
    for block in tpl["blocks"]:
        if block["type"] == "text":
            text_blocks.append(block)
            continue
        cfg = substitute(copy.deepcopy(block["data_config"]), replacements)
        cli(
            "+dashboard-block-create",
            "--base-token", args.base_token,
            "--dashboard-id", dash_id,
            "--name", block["name"],
            "--type", block["type"],
            "--data-config", json.dumps(cfg, ensure_ascii=False),
        )
        print(f"  ✅ block 创建: {block['name']} ({block['type']})")

    # 3. arrange(让图表自动布局)
    cli("+dashboard-arrange", "--base-token", args.base_token, "--dashboard-id", dash_id)
    print(f"  ✅ dashboard arrange 完成")

    # 4. 最后建 text block,使其落到底部
    for block in text_blocks:
        cfg = substitute(copy.deepcopy(block["data_config"]), replacements)
        cli(
            "+dashboard-block-create",
            "--base-token", args.base_token,
            "--dashboard-id", dash_id,
            "--name", block["name"],
            "--type", block["type"],
            "--data-config", json.dumps(cfg, ensure_ascii=False),
        )
        print(f"  ✅ text block: {block['name']} (放在底部)")

    print(f"\nDashboard ID: {dash_id}")


if __name__ == "__main__":
    main()
