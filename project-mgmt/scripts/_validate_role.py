#!/usr/bin/env python3
"""
角色 JSON 预校验 — 拦住会让飞书 API 报错的"非法字段引用"。

飞书规则:角色 filter_rules 中的 field_name **不能**引用以下类型字段:
  - lookup / formula
  - link(单向或双向)
  - auto_number
  - created_time / modified_time / updated_at
  - created_by / updated_by
  - attachment

本脚本扫描 role JSON 中所有 filter_rules 引用,对照 configs/fields/*.json
里的字段定义。任何一个非法引用就报错并指出具体位置(table、field、规则组)。

bootstrap.sh / new-project.sh 在调 `lark-cli base +role-create` **之前**会先跑这个,
比让飞书 API 抛错友好 100 倍——错误一眼定位到具体 JSON 行。

用法:
  python3 _validate_role.py <role_json_path>

退出码:
  0 — 通过
  1 — 发现非法引用(stderr 输出详情)
"""

import argparse
import json
import os
import sys

FORBIDDEN_FILTER_TYPES = {
    "lookup",
    "formula",
    "link",
    "auto_number",
    "created_time",
    "modified_time",
    "updated_at",
    "created_by",
    "updated_by",
    "attachment",
}

TABLE_TO_CONFIG = {
    "项目主表": "project_table.json",
    "任务表": "task_table.json",
    "速查卡·字段分级权限": "cheat_card_table.json",
}


def load_field_types(config_dir):
    table_field_types = {}
    for table_name, fname in TABLE_TO_CONFIG.items():
        path = os.path.join(config_dir, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        types = {}
        if cfg.get("primary_field"):
            types[cfg["primary_field"]["name"]] = cfg["primary_field"]["type"]
        for field in cfg.get("fields", []):
            types[field["name"]] = field["type"]
        for field in cfg.get("lookup_fields", []):
            types[field["name"]] = "lookup"
        for field in cfg.get("formula_fields", []):
            types[field["name"]] = "formula"
        table_field_types[table_name] = types
    return table_field_types


def collect_refs(role_json):
    refs = []
    for table_name, rule in role_json.get("table_rule_map", {}).items():
        record_rule = rule.get("record_rule", {})
        for group_key in [
            "read_filter_rule_group",
            "edit_filter_rule_group",
            "delete_filter_rule_group",
        ]:
            group = record_rule.get(group_key)
            if not group:
                continue
            for fr in group.get("filter_rules", []):
                for f in fr.get("filters", []):
                    name = f.get("field_name")
                    if name:
                        refs.append({"table": table_name, "field": name, "group": group_key})
    return refs


def validate(role_path, config_dir):
    with open(role_path, encoding="utf-8") as f:
        role = json.load(f)
    field_types = load_field_types(config_dir)
    refs = collect_refs(role)

    violations = []
    for ref in refs:
        table_types = field_types.get(ref["table"])
        if table_types is None:
            violations.append(
                f"  ❌ {ref['table']}.{ref['field']} ({ref['group']}) "
                f"— 表名 '{ref['table']}' 不在已知 schema 中"
            )
            continue
        ftype = table_types.get(ref["field"])
        if ftype is None:
            violations.append(
                f"  ❌ {ref['table']}.{ref['field']} ({ref['group']}) "
                f"— 字段不存在于表 schema"
            )
            continue
        if ftype in FORBIDDEN_FILTER_TYPES:
            violations.append(
                f"  ❌ {ref['table']}.{ref['field']} ({ref['group']}) "
                f"— 字段类型 '{ftype}' 不允许用在 filter_rules"
            )

    if violations:
        sys.stderr.write(
            f"\n[_validate_role] 校验失败: {os.path.basename(role_path)} 引用了非法字段:\n"
        )
        for v in violations:
            sys.stderr.write(v + "\n")
        sys.stderr.write(
            "\n修复指南:\n"
            "  把 filter 引用的 lookup/formula/link 等字段改造为 select/text/number 等基础字段,\n"
            "  由 skill 写入时主动同步。详见 references/feishu-permission-limits.md\n\n"
        )
        return 1

    print(f"  ✅ {os.path.basename(role_path)} 校验通过")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("role_path", help="role JSON 文件路径")
    ap.add_argument(
        "--config-dir",
        default=os.environ.get("PM_SKILL_CONFIG_DIR")
        or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "configs", "fields"
        ),
        help="字段定义目录,默认 ../configs/fields",
    )
    args = ap.parse_args()
    sys.exit(validate(args.role_path, args.config_dir))


if __name__ == "__main__":
    main()
