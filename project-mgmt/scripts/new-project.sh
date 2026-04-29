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
    "项目状态": "筹备",
}
if has_secrecy:
    record_fields["保密等级"] = SECRECY
    print(f"  ℹ 工作区启用了保密分级,本项目设为 {SECRECY}")
else:
    print(f"  ℹ 工作区未启用保密分级(无'保密等级'字段),跳过该字段")

# 幂等 — 如果项目主表里已有同名项目记录,跳过 record 创建并复用 record_id
# 注:lark-cli +record-list 返回是**列式**数据:
#   data.fields = [字段名数组]
#   data.data = [[一行的值列表], ...](值的顺序对应 fields)
#   data.record_id_list = [record_id, ...](平行于 data.data)
existing_proj_recs = cli("+record-list","--base-token",BASE,"--table-id",project_master["id"],"--limit","500")
proj_data = existing_proj_recs.get("data", {})
field_names_list = proj_data.get("fields", [])
rows = proj_data.get("data", [])
record_ids = proj_data.get("record_id_list", [])

# 找 "项目名称" 列的索引
try:
    name_col = field_names_list.index("项目名称")
except ValueError:
    name_col = -1

proj_record_id = "?"
if name_col >= 0:
    for i, row in enumerate(rows):
        cell = row[name_col] if name_col < len(row) else None
        # 文本字段值可能是 string 或 [{"text": "...","type":"text"}]
        if isinstance(cell, list) and cell:
            cell = cell[0].get("text") if isinstance(cell[0], dict) else cell[0]
        if cell == PROJECT:
            proj_record_id = record_ids[i] if i < len(record_ids) else "?"
            break

if proj_record_id != "?":
    print(f"  ⚠️ 项目记录 '{PROJECT}' 已存在,跳过创建,复用 record_id={proj_record_id}")
else:
    # lark-cli 没有 +record-create,用 +record-batch-create
    # 注:正确 payload 格式是 {fields: [字段名数组], rows: [[一行值数组]]},
    # 同 bootstrap.sh 里 cheat_card_data.json 的格式
    batch_payload = {
        "fields": list(record_fields.keys()),
        "rows": [list(record_fields.values())],
    }
    r = cli(
        "+record-batch-create","--base-token",BASE,"--table-id",project_master["id"],
        "--json",json.dumps(batch_payload, ensure_ascii=False)
    )
    # batch_create 返回 data.record_id_list(平行 data.data 列式数据)
    rids = r.get("data", {}).get("record_id_list", [])
    if rids:
        proj_record_id = rids[0]
    print(f"  ✅ 项目记录创建{(',record_id='+proj_record_id) if proj_record_id != '?' else '(record_id 未返回)'}")

# ---- 2. 找一张已有任务表,读其 schema 作为模板;新表幂等(同名复用)----
print(f"\n==> 2. 克隆任务表 schema → {NEW_TABLE}")

# 重新拿 table list(项目刚加可能有副作用)
tables = cli("+table-list","--base-token",BASE)["data"]["tables"]

# 幂等 — 如果同名任务表已存在,直接复用,不重建,跳过整个字段创建段
existing_new_tbl = next((t for t in tables if t["name"] == NEW_TABLE), None)
skip_field_creation = False
if existing_new_tbl:
    new_tbl = existing_new_tbl["id"]
    skip_field_creation = True
    print(f"  ⚠️ 任务表 '{NEW_TABLE}' 已存在,跳过建表 + 字段创建,复用 → {new_tbl}")
    print(f"     (假设字段已建齐。若字段不全请先删此表再重跑。)")
else:
    template_task = next(
        (t for t in tables if t["name"] == "任务表" or t["name"].startswith("任务表·")),
        None
    )
    if not template_task:
        sys.stderr.write("❌ 工作区里没有任务表(或 任务表·xxx)作为 schema 参考\n")
        sys.exit(1)
    print(f"  使用模板任务表: {template_task['name']} ({template_task['id']})")

    # 创建新表
    new_tbl = cli(
        "+table-create","--base-token",BASE,"--name",NEW_TABLE
    )["data"]["table"]["id"]

# 直接从 configs 读字段定义(后面字段创建逻辑用,新建表才会跑)
with open(os.path.join(REPO,"configs/fields/task_table.json"), encoding="utf-8") as f:
    task_cfg = json.load(f)

if not skip_field_creation:
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
DASHBOARD_NAME = f"{PROJECT} · 综合看板"
dash_proc = subprocess.run([
    "python3", os.path.join(REPO,"scripts/_apply_dashboard.py"),
    "--base-token", BASE,
    "--dashboard-name", DASHBOARD_NAME,
    "--task-table-name", NEW_TABLE,
    "--project-name", PROJECT,
    "--template", os.path.join(REPO,"configs/dashboard_template.json"),
], check=True, capture_output=True, text=True)
print(dash_proc.stdout)
# 从 _apply_dashboard.py stdout 解析 dashboard_id
dash_id = ""
for line in dash_proc.stdout.splitlines():
    if line.startswith("Dashboard ID:"):
        dash_id = line.split(":", 1)[1].strip()
        break

# ---- 6. 写状态文件 ----
import datetime as _dt
state_dir = os.path.expanduser("~/.pm-skill/state/projects")
os.makedirs(state_dir, exist_ok=True)
state = {
    "base_token": BASE,
    "project_name": PROJECT,
    "secrecy_level": SECRECY,
    "project_record_id": proj_record_id,
    "task_table_id": new_tbl,
    "task_table_name": NEW_TABLE,
    "dashboard_id": dash_id,
    "dashboard_name": DASHBOARD_NAME,
    "created_at": _dt.datetime.now().isoformat(timespec="seconds"),
}
state_path = os.path.join(state_dir, f"{PROJECT}.json")
with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

print(f"\n==> DONE")
print(f"    项目名: {PROJECT}")
print(f"    新任务表: {NEW_TABLE} ({new_tbl})")
print(f"    新 dashboard: {DASHBOARD_NAME} ({dash_id})")
print(f"    💾 状态已写入: {state_path}")
print(f"    💡 后续给该项目加任务/查任务时,从此文件读 base_token / task_table_id,不要从对话上下文猜")
print(f"\n下一步(UI 手动):")
print(f"    1. 在 项目主表 该项目行,补全:项目经理、开始/计划完成日期、优先级")
print(f"    2. 把项目经理/成员绑定到对应角色")
print(f"    3. '我的任务'/'我负责的项目'视图加'当前用户'过滤")
PYEOF
