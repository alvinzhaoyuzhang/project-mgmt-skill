#!/usr/bin/env python3
"""
按 configs/dashboard_template.json 在指定 Base 建综合看板,占位会被替换:
  <TASK_TABLE_NAME> → 任务表名(必须是 Base 内已存在的任务表名)
  <PROJECT_NAME>    → 项目名(用于 filter 所属项目名称 = ...)

bootstrap.sh / new-project.sh 共用。

幂等行为(v1.1.1):
  - 如果同名 dashboard 已存在,**进一步看里面有几个 block**:
      - block_count >= 1 → 认为已完整,跳过整段
      - block_count == 0 → 这是空壳(很可能是 silent-success bug 导致),
        **复用其 dashboard_id 继续补建 block**
  - 每个 +dashboard-block-create 失败时,如果是飞书 internal_error
    (code=800008006 等 8000xxxxx),**先 list 确认实际是否成功(silent success
    检测),如未成功再 retry**(最多 3 次,每次间隔 3 秒)
  - 同名 block 已存在则 skip(支持单次执行内的部分失败重跑)

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
import time

INTERNAL_ERROR_PATTERNS = ["800008006", "800008", "internal_error", "internal error"]
MAX_RETRIES = 3
RETRY_DELAY_SEC = 3


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


def is_internal_error(combined_output: str) -> bool:
    """检测输出里是否有飞书 internal_error 标志(silent-success 高发场景)。"""
    haystack = combined_output.lower()
    return any(p.lower() in haystack for p in INTERNAL_ERROR_PATTERNS)


def list_dashboards(base_token: str) -> list:
    """返回 base 下所有 dashboard 的 list,每项 {dashboard_id, name}。"""
    r = cli("+dashboard-list", "--base-token", base_token, check=False)
    if not r:
        return []
    data = r.get("data", {})
    candidates = data.get("dashboards") or data.get("items") or data.get("data") or []
    out = []
    for d in candidates:
        out.append({
            "dashboard_id": d.get("dashboard_id") or d.get("id"),
            "name": d.get("name"),
        })
    return out


def find_existing_dashboard(base_token: str, dashboard_name: str):
    """返回同名 dashboard 的 id;不存在返回 None。"""
    for d in list_dashboards(base_token):
        if d.get("name") == dashboard_name:
            return d.get("dashboard_id")
    return None


def list_dashboard_blocks(base_token: str, dashboard_id: str) -> list:
    """列出 dashboard 内所有 block 的 [{name, block_id, type}, ...]。"""
    r = cli("+dashboard-block-list", "--base-token", base_token,
            "--dashboard-id", dashboard_id, check=False)
    if not r:
        return []
    data = r.get("data", {})
    items = data.get("items") or data.get("blocks") or []
    return items


def create_dashboard_with_retry(base_token: str, dashboard_name: str) -> str:
    """创建 dashboard,处理 silent-success(create 报错但实际已建)+ 重试。"""
    for attempt in range(1, MAX_RETRIES + 1):
        r = subprocess.run(
            ["lark-cli", "base", "+dashboard-create", "--base-token", base_token,
             "--name", dashboard_name],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            dash_id = data["data"]["dashboard"]["dashboard_id"]
            print(f"  ✅ Dashboard 创建: {dashboard_name} → {dash_id}")
            return dash_id

        combined = r.stdout + r.stderr
        if is_internal_error(combined):
            # silent success 检测:虽然报错,看 list 是否实际已建
            print(f"  ⚠️ create 报 internal_error,先 list 看是否 silent success...")
            time.sleep(2)
            existing = find_existing_dashboard(base_token, dashboard_name)
            if existing:
                print(f"  ✅ silent success 检测命中:dashboard 实际已建 → {existing}")
                return existing
            if attempt < MAX_RETRIES:
                print(f"     未检测到,等 {RETRY_DELAY_SEC}s 后重试({attempt}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY_SEC)
                continue

        # 非 internal_error 错误,直接失败
        sys.stderr.write(f"\n❌ Dashboard 创建失败(非 internal_error,不重试)\n")
        sys.stderr.write(f"   命令: lark-cli base +dashboard-create --base-token <...> --name {dashboard_name}\n")
        if r.stderr.strip(): sys.stderr.write(f"   stderr:\n{r.stderr}\n")
        if r.stdout.strip(): sys.stderr.write(f"   stdout:\n{r.stdout}\n")
        sys.exit(1)

    sys.stderr.write(f"\n❌ Dashboard 创建重试 {MAX_RETRIES} 次仍失败\n")
    sys.exit(1)


def create_block_with_retry(base_token: str, dash_id: str, block_def: dict, cfg: dict):
    """创建单个 block,处理 silent-success + retry。"""
    block_name = block_def["name"]
    block_type = block_def["type"]
    for attempt in range(1, MAX_RETRIES + 1):
        r = subprocess.run(
            ["lark-cli", "base", "+dashboard-block-create",
             "--base-token", base_token,
             "--dashboard-id", dash_id,
             "--name", block_name,
             "--type", block_type,
             "--data-config", json.dumps(cfg, ensure_ascii=False)],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            print(f"  ✅ block 创建: {block_name} ({block_type})")
            return

        combined = r.stdout + r.stderr
        if is_internal_error(combined):
            print(f"  ⚠️ block '{block_name}' create 报 internal_error,先 list 看是否 silent success...")
            time.sleep(2)
            existing_blocks = list_dashboard_blocks(base_token, dash_id)
            if any(b.get("name") == block_name for b in existing_blocks):
                print(f"  ✅ silent success 检测命中:block '{block_name}' 实际已建")
                return
            if attempt < MAX_RETRIES:
                print(f"     未检测到,等 {RETRY_DELAY_SEC}s 后重试({attempt}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY_SEC)
                continue

        # 非 internal_error,直接失败
        sys.stderr.write(f"\n❌ Block '{block_name}' 创建失败(非 internal_error,不重试)\n")
        if r.stderr.strip(): sys.stderr.write(f"   stderr:\n{r.stderr}\n")
        if r.stdout.strip(): sys.stderr.write(f"   stdout:\n{r.stdout}\n")
        sys.exit(1)

    sys.stderr.write(f"\n❌ Block '{block_name}' 重试 {MAX_RETRIES} 次仍失败\n")
    sys.exit(1)


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

    # 1. 找到或创建 dashboard(区分"已完整"vs"空壳")
    existing_id = find_existing_dashboard(args.base_token, args.dashboard_name)
    if existing_id:
        existing_blocks = list_dashboard_blocks(args.base_token, existing_id)
        block_count = len(existing_blocks)
        if block_count > 0:
            print(f"  ✅ Dashboard '{args.dashboard_name}' 已完整存在 ({block_count} 个 block),跳过整段")
            print(f"\nDashboard ID: {existing_id}")
            return
        else:
            print(f"  ⚠️ Dashboard '{args.dashboard_name}' 是空壳 (0 block),复用 dashboard_id 继续补建 block")
            print(f"     (这通常是飞书 internal_error 导致的 silent-success 残留)")
            dash_id = existing_id
    else:
        dash_id = create_dashboard_with_retry(args.base_token, args.dashboard_name)

    # 2. 列出已有 block,跳过同名(支持单次执行的部分失败重跑)
    existing_blocks_now = list_dashboard_blocks(args.base_token, dash_id)
    existing_block_names = {b.get("name") for b in existing_blocks_now if b.get("name")}
    if existing_block_names:
        print(f"  ℹ Dashboard 内已有 {len(existing_block_names)} 个 block,会跳过同名:{', '.join(sorted(existing_block_names))}")

    # 3. 串行建图表 block(text 留到最后)
    text_blocks = []
    for block in tpl["blocks"]:
        if block["type"] == "text":
            text_blocks.append(block)
            continue
        if block["name"] in existing_block_names:
            print(f"  ⏭️ block 已存在,跳过: {block['name']}")
            continue
        cfg = substitute(copy.deepcopy(block["data_config"]), replacements)
        create_block_with_retry(args.base_token, dash_id, block, cfg)

    # 4. arrange(让图表自动布局)— 幂等,可重复调
    cli("+dashboard-arrange", "--base-token", args.base_token, "--dashboard-id", dash_id, check=False)
    print(f"  ✅ dashboard arrange 完成")

    # 5. 最后建 text block,使其落到底部
    for block in text_blocks:
        if block["name"] in existing_block_names:
            print(f"  ⏭️ text block 已存在,跳过: {block['name']}")
            continue
        cfg = substitute(copy.deepcopy(block["data_config"]), replacements)
        create_block_with_retry(args.base_token, dash_id, block, cfg)

    print(f"\nDashboard ID: {dash_id}")


if __name__ == "__main__":
    main()
