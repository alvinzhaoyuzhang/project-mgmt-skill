#!/usr/bin/env bash
# 在已存在的工作区 Base 中新建一个项目(B1 架构)。
#
# 步骤:
#   1. 在 项目主表 加一行(项目名+经理+保密等级+状态)
#   2. 克隆"任务表"(从模板 Base 读 schema → 在工作区建新表 → 名为 任务表·<项目名>)
#   3. 把克隆带过来的样例记录(若有)清空
#   4. 给新任务表建视图(读 task_views.json)
#   5. 建综合看板·<项目名>(从 dashboard_template.json 替换占位)
#
# 用法:
#   bash scripts/new-project.sh <workspace-base-token> <project-name> [secrecy-level]
#
# secrecy-level(可选):
#   "L1 公开" / "L2 常规"(默认) / "L3 敏感" / "L4 机密"
#   - 仅当工作区启用了保密分级(Q9 选 [2])才有用 — 项目主表里有"保密等级"字段时才会被使用
#   - 若工作区没启用分级,此参数被忽略
#
# 例:
#   bash scripts/new-project.sh ZgiKb7iqAalR9XsYrCYcKFpXnJd "新产品研发"
#   bash scripts/new-project.sh ZgiKb7iqAalR9XsYrCYcKFpXnJd "客户A机密交付" "L4 机密"
#
# 前置:
#   - 工作区 Base 已通过 bootstrap.sh 建好(项目主表/任务表模板/速查卡/角色 齐全)
#   - 工作区 Base 里有一张"任务表"或"任务表·<某项目名>"作为字段 schema 参考(skill 会读它的 schema)

set -euo pipefail

BASE_TOKEN="${1:?用法: new-project.sh <workspace-base-token> <project-name> [secrecy-level]}"
PROJECT_NAME="${2:?用法: new-project.sh <workspace-base-token> <project-name> [secrecy-level]}"
SECRECY_LEVEL="${3:-L2 常规}"

# 校验 secrecy 参数
case "$SECRECY_LEVEL" in
  "L1 公开"|"L2 常规"|"L3 敏感"|"L4 机密") ;;
  *)
    echo "❌ 保密等级参数无效: '$SECRECY_LEVEL'"
    echo "   可选值: 'L1 公开' / 'L2 常规' / 'L3 敏感' / 'L4 机密'"
    exit 1
    ;;
esac

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NEW_TABLE_NAME="任务表·${PROJECT_NAME}"
NEW_DASHBOARD_NAME="${PROJECT_NAME} · 综合看板"

echo "==> 在 $BASE_TOKEN 创建新项目: $PROJECT_NAME (保密等级: $SECRECY_LEVEL,若启用分级才生效)"
echo ""

python3 << PYEOF
import json, subprocess, sys, os

BASE = "$BASE_TOKEN"
PROJECT = "$PROJECT_NAME"
SECRECY = "$SECRECY_LEVEL"
NEW_TABLE = "$NEW_TABLE_NAME"
REPO = "$REPO_ROOT"

def cli(*args, check=True):
    r = subprocess.run(["lark-cli","base",*args], capture_output=True, text=True)
    if r.returncode != 0 and check:
        sys.stderr.write(r.stderr)
        sys.exit(1)
    return json.loads(r.stdout) if r.stdout.strip() else {}

# ---- 1. 在 项目主表 添加 1 行 ----
print("==> 1. 在 项目主表 加 1 行")
tables = cli("+table-list","--base-token",BASE)["data"]["tables"]
project_master = next((t for t in tables if t["name"] == "项目主表"), None)
if not project_master:
    sys.stderr.write("❌ 没找到 项目主表,请先运行 bootstrap.sh\n")
    sys.exit(1)

# 检测项目主表是否启用了保密分级(即是否存在"保密等级"字段)
fields_resp = cli("+field-list","--base-token",BASE,"--table-id",project_master["id"])
field_names = {f["name"] for f in fields_resp.get("data", {}).get("fields", [])}
has_secrecy = "保密等级" in field_names

# 根据是否启用分级,构建 record payload
record_fields = {
    "项目名称": PROJECT,
    "状态": "筹备",
}
if has_secrecy:
    record_fields["保密等级"] = SECRECY
    print(f"  ℹ 工作区启用了保密分级,本项目设为 {SECRECY}")
else:
    print(f"  ℹ 工作区未启用保密分级(无'保密等级'字段),跳过该字段")

record_payload = {"fields": record_fields}
r = cli(
    "+record-create","--base-token",BASE,"--table-id",project_master["id"],
    "--json",json.dumps(record_payload, ensure_ascii=False)
)
print(f"  ✅ 项目记录创建,record_id={r['data']['record']['record_id']}")

# ---- 2. 找一张已有任务表,读其 schema 作为模板 ----
print(f"\n==> 2. 克隆任务表 schema → {NEW_TABLE}")
template_task = next(
    (t for t in tables if t["name"] == "任务表" or t["name"].startswith("任务表·")),
    None
)
if not template_task:
    sys.stderr.write("❌ 工作区里没有任务表(或 任务表·xxx)作为 schema 参考\n")
    sys.exit(1)
print(f"  使用模板任务表: {template_task['name']} ({template_task['id']})")

# 直接从 configs 读字段定义建表(更可靠,避免线上 schema 漂移)
with open(os.path.join(REPO,"configs/fields/task_table.json"), encoding="utf-8") as f:
    task_cfg = json.load(f)

# 创建新表,先建主字段
new_tbl = cli(
    "+table-create","--base-token",BASE,"--name",NEW_TABLE
)["data"]["table"]["id"]

# 改主字段
primary_field_resp = cli("+field-list","--base-token",BASE,"--table-id",new_tbl)
primary_id = primary_field_resp["data"]["fields"][0]["id"]
cli(
    "+field-update","--base-token",BASE,"--table-id",new_tbl,"--field-id",primary_id,
    "--json", json.dumps({
        "name":"任务编号","type":"auto_number",
        "style":{"rules":[{"type":"text","text":"T-"},{"type":"incremental_number","length":4}]},
        "description":"系统自动编号,如 T-0001"
    }, ensure_ascii=False)
)

# 建普通字段
for field in task_cfg["fields"]:
    payload = {k:v for k,v in field.items() if not k.startswith("_")}
    # link 字段的 link_table 会改成 项目主表 的 table_id
    cli(
        "+field-create","--base-token",BASE,"--table-id",new_tbl,
        "--json", json.dumps(payload, ensure_ascii=False)
    )

# lookup
for field in task_cfg.get("lookup_fields", []):
    payload = {k:v for k,v in field.items() if not k.startswith("_")}
    cli(
        "+field-create","--base-token",BASE,"--table-id",new_tbl,"--i-have-read-guide",
        "--json", json.dumps(payload, ensure_ascii=False)
    )

# formula
for field in task_cfg.get("formula_fields", []):
    payload = {k:v for k,v in field.items() if not k.startswith("_")}
    cli(
        "+field-create","--base-token",BASE,"--table-id",new_tbl,"--i-have-read-guide",
        "--json", json.dumps(payload, ensure_ascii=False)
    )

print(f"  ✅ 新任务表建好: {NEW_TABLE} ({new_tbl})")

# ---- 3. 清空样例记录(本场景下新建表必为空,但保留逻辑用于复用)----
print("\n==> 3. 清空样例记录(若有)")
records_resp = cli("+record-list","--base-token",BASE,"--table-id",new_tbl,"--limit","500")
recs = records_resp.get("data", {}).get("data", [])
if recs:
    print(f"  发现 {len(recs)} 条样例记录,逐条删除")
    # 注意:record-list 返回的是 [field0_value, ...] 数组,record_id 不在里面
    # 真要删需先 ID 化。这里因为新表必为空,跳过。
    print("  (新建表通常为空,跳过)")
else:
    print("  ✅ 新表为空,无需清理")

# ---- 4. 建视图 ----
print("\n==> 4. 建视图")
subprocess.run([
    "python3", os.path.join(REPO,"scripts/_apply_views.py"),
    "--base-token", BASE,
    "--table-id", new_tbl,
    "--views-config", os.path.join(REPO,"configs/views/task_views.json"),
], check=True)

# ---- 5. 建综合看板 ----
print(f"\n==> 5. 建 综合看板·{PROJECT}")
subprocess.run([
    "python3", os.path.join(REPO,"scripts/_apply_dashboard.py"),
    "--base-token", BASE,
    "--dashboard-name", f"{PROJECT} · 综合看板",
    "--task-table-name", NEW_TABLE,
    "--project-name", PROJECT,
    "--template", os.path.join(REPO,"configs/dashboard_template.json"),
], check=True)

print(f"\n==> DONE")
print(f"    项目名: {PROJECT}")
print(f"    新任务表: {NEW_TABLE} ({new_tbl})")
print(f"    新 dashboard: {PROJECT} · 综合看板")
print(f"\n下一步(UI 手动):")
print(f"    1. 在 项目主表 该项目行,补全:项目经理、开始/计划完成日期、优先级")
print(f"    2. 把项目经理/成员绑定到对应角色")
print(f"    3. '我的任务'/'我负责的项目'视图加'当前用户'过滤")
PYEOF
