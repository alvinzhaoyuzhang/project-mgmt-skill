#!/usr/bin/env python3
"""
按 configs/views/*.json 给指定 table 批量建视图(含 filter/sort/group/visible-fields)。

bootstrap.sh 和 new-project.sh 共用。

用法:
  python3 _apply_views.py \
    --base-token <token> \
    --table-id <tid> \
    --views-config configs/views/task_views.json
"""

import argparse
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


def get_field_name_to_id(base_token: str, table_id: str) -> dict:
    """返回 {字段名: field_id} 映射。"""
    r = cli("+field-list", "--base-token", base_token, "--table-id", table_id)
    return {f["name"]: f["id"] for f in r["data"]["fields"]}


def find_existing_view(base_token: str, table_id: str, view_name: str):
    """查找同名视图,返回 view_id;不存在返回 None。"""
    r = cli("+view-list", "--base-token", base_token, "--table-id", table_id, check=False)
    if not r:
        return None
    data = r.get("data", {})
    views = data.get("views") or data.get("items") or []
    for v in views:
        # 不同 lark-cli 版本字段命名不同,做兼容
        name = v.get("view_name") or v.get("name")
        if name == view_name:
            return v.get("view_id") or v.get("id")
    return None


def translate_filter(filter_cfg: dict, name2id: dict) -> dict:
    """把 conditions 里的字段名替换成 ID。"""
    if not filter_cfg or not filter_cfg.get("conditions"):
        return filter_cfg
    new_conds = []
    for cond in filter_cfg["conditions"]:
        if isinstance(cond, list) and len(cond) >= 2:
            field = cond[0]
            field_id = name2id.get(field, field)
            new_conds.append([field_id, *cond[1:]])
        else:
            new_conds.append(cond)
    return {"logic": filter_cfg.get("logic", "and"), "conditions": new_conds}


def translate_visible_fields(fields: list, name2id: dict) -> list:
    return [name2id.get(f, f) for f in fields]


def translate_group_or_sort(items: list, name2id: dict) -> list:
    out = []
    for it in items or []:
        new = dict(it)
        if "field" in new:
            new["field"] = name2id.get(new["field"], new["field"])
        out.append(new)
    return out


def create_view(base_token: str, table_id: str, view_cfg: dict, name2id: dict) -> str:
    name = view_cfg["name"]
    vtype = view_cfg.get("type", "grid")

    # 0. 幂等 — 如已存在同名视图,复用其 view_id,不重建,但仍重新 apply 配置(filter/group/sort/visible-fields)
    existing_id = find_existing_view(base_token, table_id, name)
    if existing_id:
        print(f"  ⚠️ 视图 '{name}' 已存在,复用并刷新配置 → {existing_id}")
        view_id = existing_id
    else:
        # 1. create view (basic name + type)
        create_payload = {"name": name, "type": vtype}
        r = cli(
            "+view-create",
            "--base-token", base_token,
            "--table-id", table_id,
            "--json", json.dumps(create_payload, ensure_ascii=False),
        )
        # response shape varies; try common paths
        data = r.get("data", {})
        view_id = (
            data.get("view", {}).get("id")
            or (data.get("views", [{}])[0].get("id") if isinstance(data.get("views"), list) else None)
        )
        if not view_id:
            sys.stderr.write(f"⚠️ couldn't determine view_id for {name}: {r}\n")
            return ""

    # 2. set filter
    if view_cfg.get("filter"):
        f = translate_filter(view_cfg["filter"], name2id)
        cli(
            "+view-set-filter",
            "--base-token", base_token, "--table-id", table_id, "--view-id", view_id,
            "--json", json.dumps(f, ensure_ascii=False), check=False,
        )

    # 3. set group
    if view_cfg.get("group_config"):
        g = translate_group_or_sort(view_cfg["group_config"], name2id)
        cli(
            "+view-set-group",
            "--base-token", base_token, "--table-id", table_id, "--view-id", view_id,
            "--json", json.dumps({"group_config": g}, ensure_ascii=False), check=False,
        )

    # 4. set sort
    if view_cfg.get("sort_config"):
        s = translate_group_or_sort(view_cfg["sort_config"], name2id)
        cli(
            "+view-set-sort",
            "--base-token", base_token, "--table-id", table_id, "--view-id", view_id,
            "--json", json.dumps({"sort_config": s}, ensure_ascii=False), check=False,
        )

    # 5. set visible fields
    if view_cfg.get("visible_fields"):
        v = translate_visible_fields(view_cfg["visible_fields"], name2id)
        cli(
            "+view-set-visible-fields",
            "--base-token", base_token, "--table-id", table_id, "--view-id", view_id,
            "--json", json.dumps({"visible_fields": v}, ensure_ascii=False), check=False,
        )

    return view_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-token", required=True)
    ap.add_argument("--table-id", required=True)
    ap.add_argument("--views-config", required=True)
    args = ap.parse_args()

    with open(args.views_config, encoding="utf-8") as f:
        cfg = json.load(f)

    name2id = get_field_name_to_id(args.base_token, args.table_id)

    for v in cfg["views"]:
        if v.get("_workspace_only"):
            # 工作区专属视图(如"按模块浏览"),模板 Base 跳过
            print(f"  跳过(_workspace_only): {v['name']}")
            continue
        try:
            vid = create_view(args.base_token, args.table_id, v, name2id)
            print(f"  ✅ {v['name']:30s} → {vid}")
        except Exception as e:
            print(f"  ❌ {v['name']:30s} → {e}")


if __name__ == "__main__":
    main()
