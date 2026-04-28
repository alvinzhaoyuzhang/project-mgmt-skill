#!/usr/bin/env bash
# 校验线上 Base 与本地 configs/ 是否一致。
#
# 用法:
#   bash scripts/verify-template.sh <base-token>
#
# 检查:
#   1. 表是否齐全(项目主表 / 任务表 / 速查卡)
#   2. 字段名集合是否一致(每张表 vs 对应 JSON config)
#   3. 角色是否齐全(超级管理员 / 项目经理 / 项目成员)
#   4. dashboard 是否存在 + block 数量
#
# 不检查:
#   - 字段细节(option 值、formula 表达式 - 这些差异需要进表对比)
#   - 视图细节(filter/sort/group)
#   - 速查卡记录数

set -euo pipefail

BASE_TOKEN="${1:?用法: verify-template.sh <base-token>}"

echo "校验 Base: $BASE_TOKEN"
echo ""

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 << PYEOF
import subprocess, json, sys, os

BASE = "$BASE_TOKEN"
REPO = "$REPO_ROOT"

def cli(*args):
    r = subprocess.run(["lark-cli","base",*args], capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        return None
    return json.loads(r.stdout) if r.stdout.strip() else {}

def load(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as f:
        return json.load(f)

issues = []

# 1. 表是否齐全
tables_resp = cli("+table-list","--base-token",BASE)
tables = tables_resp["data"]["tables"]
table_names = {t["name"]: t["id"] for t in tables}

want_tables = ["项目主表", "速查卡·字段分级权限"]
# 任务表可能是 "任务表" 或 "任务表·xxx"(B1)
task_tables = [n for n in table_names if n == "任务表" or n.startswith("任务表·")]
if not task_tables:
    issues.append("❌ 没有任何任务表(应有 任务表 或 任务表·项目X)")

for t in want_tables:
    if t not in table_names:
        issues.append(f"❌ 缺表:{t}")

print(f"  表数量: {len(tables)} | 任务表数量: {len(task_tables)}")
for n in table_names:
    print(f"    - {n}")
print()

# 2. 字段名集合对比
def check_fields(table_id, table_name, config_path, exclude=None):
    cfg = load(config_path)
    expected = set()
    for k in ("fields", "lookup_fields", "formula_fields"):
        for f in cfg.get(k, []):
            if f.get("name", "").startswith("_"):
                continue
            # 跳过 _workspace_only 字段(只在工作区 Base 用,模板不带)
            if f.get("_workspace_only"):
                continue
            expected.add(f["name"])
    if cfg.get("primary_field"):
        expected.add(cfg["primary_field"]["name"])

    fields_resp = cli("+field-list","--base-token",BASE,"--table-id",table_id)
    actual = {f["name"] for f in fields_resp["data"]["fields"]}

    if exclude:
        expected -= set(exclude)

    missing = expected - actual
    extra = actual - expected
    if missing:
        issues.append(f"❌ [{table_name}] 缺字段: {sorted(missing)}")
    if extra:
        # 模板自动加的字段(双向link 反向、_workspace_only 模块字段等)是 OK 的
        print(f"  [{table_name}] 额外字段(可能 OK): {sorted(extra)}")
    if not missing:
        print(f"  ✅ [{table_name}] 字段齐全({len(expected)} 个)")
    print()

if "项目主表" in table_names:
    check_fields(table_names["项目主表"], "项目主表", "configs/fields/project_table.json")

for t in task_tables:
    check_fields(table_names[t], t, "configs/fields/task_table.json")

if "速查卡·字段分级权限" in table_names:
    check_fields(table_names["速查卡·字段分级权限"], "速查卡·字段分级权限", "configs/fields/cheat_card_table.json")

# 3. 角色齐全
roles_resp = cli("+role-list","--base-token",BASE)
role_names = set()
if roles_resp and roles_resp.get("data"):
    raw = roles_resp["data"].get("data")
    # 兼容两种格式:dict 直接含 base_roles,或 string 需 json.loads
    if isinstance(raw, str):
        outer = json.loads(raw)
    else:
        outer = raw or roles_resp["data"]
    for entry in outer.get("base_roles", []):
        try:
            role = json.loads(entry) if isinstance(entry, str) else entry
            role_names.add(role.get("role_name", ""))
        except Exception:
            continue
want_roles = {"超级管理员","项目经理","项目成员"}
missing_roles = want_roles - role_names
if missing_roles:
    issues.append(f"❌ 缺角色: {sorted(missing_roles)}")
else:
    print(f"  ✅ 3 角色齐全: {sorted(role_names & want_roles)}")
print()

# 4. dashboard
dash_resp = cli("+dashboard-list","--base-token",BASE)
if dash_resp and dash_resp.get("data"):
    dashboards = dash_resp["data"].get("items", dash_resp["data"].get("dashboards", []))
    print(f"  Dashboard 数量: {len(dashboards)}")
    for d in dashboards:
        name = d.get("name","?")
        did = d.get("dashboard_id","?")
        block_resp = cli("+dashboard-block-list","--base-token",BASE,"--dashboard-id",did)
        bc = len(block_resp["data"]["items"]) if block_resp else 0
        print(f"    - {name} (block={bc})")
print()

# 总结
if issues:
    print(f"\n❌ 发现 {len(issues)} 个问题:")
    for i in issues:
        print(f"  {i}")
    sys.exit(1)
else:
    print("\n✅ 校验通过")
PYEOF
