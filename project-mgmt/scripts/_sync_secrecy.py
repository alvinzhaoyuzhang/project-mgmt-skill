#!/usr/bin/env python3
"""
任务保密等级 cascade 同步 — 把项目主表的「保密等级」回写到该项目下所有任务的「任务保密等级」字段。

用户场景:
  - 用户在飞书 UI 改了 项目主表 某行的「保密等级」(从 L2 改 L3)
  - 此时该项目下所有任务的「任务保密等级」字段还是旧值,需要主动 cascade
  - 用户对 skill 说"把'V2.5 上线'项目的保密等级同步到任务" → skill 跑这个脚本

实现:
  1. 找到项目主表那一行,读「保密等级」当前值
  2. 找到该项目对应的任务表("任务表" 模板表 或 "任务表·<项目名>" — 看 B1 还是 B2 架构)
  3. 列出"所属项目 contains <项目名>"的所有 record(B1)或全表(B2)
  4. 批量 update 这些 record 的「任务保密等级」字段
  5. 报告改了几条

用法:
  python3 _sync_secrecy.py --base-token <token> --project-name "<项目名>"
  python3 _sync_secrecy.py --base-token <token> --project-name "<项目名>" --dry-run
"""

import argparse
import json
import subprocess
import sys


def cli(*args, check=True):
    """Run lark-cli base; return parsed JSON of stdout. 失败时打印完整诊断上下文。"""
    r = subprocess.run(["lark-cli", "base", *args], capture_output=True, text=True)
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


def find_table(base_token, name_or_prefix):
    """返回匹配的第一个 table id"""
    tables = cli("+table-list", "--base-token", base_token)["data"]["tables"]
    for t in tables:
        if t["name"] == name_or_prefix:
            return t["id"], t["name"]
    for t in tables:
        if t["name"].startswith(name_or_prefix):
            return t["id"], t["name"]
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-token", required=True)
    ap.add_argument("--project-name", required=True, help="项目主表 → 项目名称 字段值")
    ap.add_argument("--dry-run", action="store_true", help="只列出要改的记录,不实际写")
    args = ap.parse_args()

    # 1. 拿项目主表当前「保密等级」
    project_tid, _ = find_table(args.base_token, "项目主表")
    if not project_tid:
        sys.stderr.write("❌ 没找到 项目主表\n")
        sys.exit(1)

    proj_recs_resp = cli(
        "+record-list", "--base-token", args.base_token, "--table-id", project_tid,
        "--limit", "500"
    )
    proj_recs = proj_recs_resp.get("data", {}).get("items") \
        or proj_recs_resp.get("data", {}).get("records") \
        or proj_recs_resp.get("data", {}).get("data") or []

    target_secrecy = None
    for r in proj_recs:
        fields = r.get("fields", {})
        # 项目名称可能是 text 或 link 或 string
        name = fields.get("项目名称")
        if isinstance(name, list) and name:
            name = name[0].get("text") if isinstance(name[0], dict) else name[0]
        if name == args.project_name:
            secrecy = fields.get("保密等级")
            if isinstance(secrecy, dict):
                target_secrecy = secrecy.get("text") or secrecy.get("name")
            else:
                target_secrecy = secrecy
            break

    if not target_secrecy:
        sys.stderr.write(
            f"❌ 没找到项目 '{args.project_name}' 或其「保密等级」字段为空\n"
        )
        sys.exit(1)

    print(f"==> 项目「{args.project_name}」当前保密等级: {target_secrecy}")

    # 2. 找任务表 — B1 是单张"任务表",B2 是"任务表·<项目名>"
    task_tid, task_name = find_table(args.base_token, f"任务表·{args.project_name}")
    if not task_tid:
        task_tid, task_name = find_table(args.base_token, "任务表")
    if not task_tid:
        sys.stderr.write("❌ 没找到任务表\n")
        sys.exit(1)
    print(f"==> 目标任务表: {task_name}")

    # 3. 列出该项目的任务记录
    task_resp = cli(
        "+record-list", "--base-token", args.base_token, "--table-id", task_tid,
        "--limit", "500"
    )
    task_recs = task_resp.get("data", {}).get("items") \
        or task_resp.get("data", {}).get("records") \
        or task_resp.get("data", {}).get("data") or []

    targets = []
    for r in task_recs:
        fields = r.get("fields", {})
        proj_link = fields.get("所属项目")
        proj_names = []
        if isinstance(proj_link, list):
            for x in proj_link:
                if isinstance(x, dict):
                    proj_names.append(x.get("text") or x.get("name") or "")
                else:
                    proj_names.append(str(x))
        elif isinstance(proj_link, dict):
            proj_names.append(proj_link.get("text") or proj_link.get("name") or "")
        else:
            proj_names.append(str(proj_link or ""))
        if args.project_name in proj_names:
            current_secrecy = fields.get("任务保密等级")
            if isinstance(current_secrecy, dict):
                current_secrecy = current_secrecy.get("text") or current_secrecy.get("name")
            if current_secrecy != target_secrecy:
                targets.append(r["record_id"])

    print(f"==> 需要更新的任务数: {len(targets)} 条")

    if not targets:
        print("    (所有任务的「任务保密等级」已是最新)")
        return

    if args.dry_run:
        print(f"    [dry-run] 不实际写入。要更新的 record_id 数量: {len(targets)}")
        for rid in targets[:10]:
            print(f"      - {rid}")
        if len(targets) > 10:
            print(f"      ... 还有 {len(targets) - 10} 条")
        return

    # 4. 批量 update,每批 100 条
    print(f"==> 开始批量更新...")
    BATCH = 100
    updated = 0
    for i in range(0, len(targets), BATCH):
        batch = targets[i:i + BATCH]
        records_payload = [
            {"record_id": rid, "fields": {"任务保密等级": target_secrecy}}
            for rid in batch
        ]
        cli(
            "+record-batch-update", "--base-token", args.base_token,
            "--table-id", task_tid,
            "--json", json.dumps({"records": records_payload}, ensure_ascii=False),
        )
        updated += len(batch)
        print(f"    已更新 {updated}/{len(targets)}")

    print(f"\n✅ 完成,{updated} 条任务的「任务保密等级」已更新为 '{target_secrecy}'")


if __name__ == "__main__":
    main()
