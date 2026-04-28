#!/usr/bin/env python3
"""
按 configs/dashboard_template.json 在指定 Base 建综合看板,占位会被替换:
  <TASK_TABLE_NAME> → 任务表名(必须是 Base 内已存在的任务表名)
  <PROJECT_NAME>    → 项目名(用于 filter 所属项目名称 = ...)

bootstrap.sh / new-project.sh 共用。

幂等行为:
  - 如果 base 内已有同名 dashboard,**跳过整个 dashboard 创建步骤**(不重建 / 不补 block)。
    这样脚本中途失败可安全重跑而不会再因"name conflict"卡住。
  - 用户想强制重建,先删旧 dashboard,详见脚本 stdout 的提示信息。

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


def find_existing_dashboard(base_token: str, dashboard_name: str):
    """返回同名 dashboard 的 id;不存在返回 None。"""
    r = cli("+dashboard-list", "--base-token", base_token, check=False)
    if not r:
        return None
    data = r.get("data", {})
    # API 返回字段名可能是 dashboards / items / data,兼容
    candidates = data.get("dashboards") or data.get("items") or data.get("data") or []
    for d in candidates:
        if d.get("name") == dashboard_name:
            return d.get("dashboard_id") or d.get("id")
    return None


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

    # 0. 幂等检查 — 如果同名 dashboard 已在 base 内,直接跳过整段
    existing_id = find_existing_dashboard(args.base_token, args.dashboard_name)
    if existing_id:
        print(f"  ⚠️ Dashboard '{args.dashboard_name}' 已存在,跳过创建并复用 → {existing_id}")
        print(f"  ℹ 这通常意味着上次跑到这一步成功了,但后续步骤失败导致脚本退出。")
        print(f"  ℹ 当前选择'安全跳过'(不重建,不重复建 block)。")
        print(f"  ℹ 如确需重建一份干净的 dashboard,先删旧的:")
        print(f"      lark-cli base +dashboard-delete --base-token {args.base_token} --dashboard-id {existing_id} --yes")
        print(f"      然后重跑本脚本。")
        print(f"\nDashboard ID: {existing_id}")
        return

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
