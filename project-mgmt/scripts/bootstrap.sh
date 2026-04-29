#!/usr/bin/env bash
# Bootstrap: 从零创建一个"项目管理中心"工作区 Base
#
# 前置:已装飞书 CLI (lark-cli, 即 npm 包 @larksuite/cli) 并已 auth login
# 用法:bash <skill>/scripts/bootstrap.sh "项目管理中心·业务方向"
# 输出:新 Base 的 base_token 和 URL
#
# 幂等说明:
#   - 视图 / dashboard 步骤已加幂等检测(同名存在则复用,不会因 conflict 中止)
#   - base / table / field / role 创建**不幂等**:中途失败时,推荐删除半成品 Base 重新跑
#   - 字段 / 角色创建失败时,会显示完整 lark-cli 错误明细(stderr + stdout JSON)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BASE_NAME="${1:-项目管理中心(通用模板)}"

echo "==> 创建 Base: $BASE_NAME"
CREATE_OUT=$(lark-cli base +base-create --name "$BASE_NAME" --time-zone Asia/Shanghai)
BASE_TOKEN=$(echo "$CREATE_OUT" | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['base']['base_token'])")
BASE_URL=$(echo "$CREATE_OUT" | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['base']['url'])")
echo "    base_token: $BASE_TOKEN"
echo "    url: $BASE_URL"

# 默认表 id
DEFAULT_TBL=$(lark-cli base +table-list --base-token $BASE_TOKEN | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['tables'][0]['id'])")

echo "==> 改名默认表为'项目主表'"
lark-cli base +table-update --base-token $BASE_TOKEN --table-id $DEFAULT_TBL --name "项目主表" > /dev/null

echo "==> 改默认主字段为'项目名称'"
PRIMARY_ID=$(lark-cli base +field-list --base-token $BASE_TOKEN --table-id $DEFAULT_TBL | python3 -c "
import json,sys
for f in json.load(sys.stdin)['data']['fields']:
    if f['type']=='text': print(f['id']); break
")
lark-cli base +field-update --base-token $BASE_TOKEN --table-id $DEFAULT_TBL --field-id $PRIMARY_ID \
  --json '{"name":"项目名称","type":"text","description":"项目的简短标识名,作为主字段"}' > /dev/null

echo "==> 删除默认其他字段"
lark-cli base +field-list --base-token $BASE_TOKEN --table-id $DEFAULT_TBL | python3 -c "
import json,sys,subprocess
for f in json.load(sys.stdin)['data']['fields']:
    if f['name'] != '项目名称':
        subprocess.run(['lark-cli','base','+field-delete','--base-token','$BASE_TOKEN','--table-id','$DEFAULT_TBL','--field-id',f['id'],'--yes'])
"

echo "==> 建项目主表其他字段"
python3 << EOF
import json, subprocess, sys
with open('$SKILL_ROOT/configs/fields/project_table.json') as f:
    cfg = json.load(f)
for field in cfg['fields']:
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    r = subprocess.run(
        ['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$DEFAULT_TBL','--json',json.dumps(payload, ensure_ascii=False)],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        sys.stderr.write(f"\n❌ 创建字段 '{field['name']}' 失败 (项目主表)\n")
        if r.stderr.strip(): sys.stderr.write(f"   stderr:\n{r.stderr}\n")
        if r.stdout.strip(): sys.stderr.write(f"   stdout:\n{r.stdout}\n")
        sys.exit(1)
    print(f"  created: {field['name']}")
EOF

echo "==> 建任务表"
TASK_TBL=$(lark-cli base +table-create --base-token $BASE_TOKEN --name "任务表" | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['table']['id'])")
echo "    task table_id: $TASK_TBL"

echo "==> 更新任务表主字段为'任务编号' auto_number"
TASK_PRIMARY=$(lark-cli base +field-list --base-token $BASE_TOKEN --table-id $TASK_TBL | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['fields'][0]['id'])")
lark-cli base +field-update --base-token $BASE_TOKEN --table-id $TASK_TBL --field-id $TASK_PRIMARY \
  --json '{"name":"任务编号","type":"auto_number","style":{"rules":[{"type":"text","text":"T-"},{"type":"incremental_number","length":4}]},"description":"系统自动编号,如 T-0001"}' > /dev/null

echo "==> 建任务表其他字段(不含 lookup)"
python3 << EOF
import json, subprocess, sys
with open('$SKILL_ROOT/configs/fields/task_table.json') as f:
    cfg = json.load(f)
for field in cfg['fields']:
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    r = subprocess.run(
        ['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$TASK_TBL','--json',json.dumps(payload, ensure_ascii=False)],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        sys.stderr.write(f"\n❌ 创建字段 '{field['name']}' 失败 (任务表)\n")
        if r.stderr.strip(): sys.stderr.write(f"   stderr:\n{r.stderr}\n")
        if r.stdout.strip(): sys.stderr.write(f"   stdout:\n{r.stdout}\n")
        sys.exit(1)
    print(f"  created: {field['name']}")
EOF

echo "==> 建任务表 lookup 字段"
python3 << EOF
import json, subprocess, sys
with open('$SKILL_ROOT/configs/fields/task_table.json') as f:
    cfg = json.load(f)
for field in cfg.get('lookup_fields', []):
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    r = subprocess.run(
        ['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$TASK_TBL','--i-have-read-guide','--json',json.dumps(payload, ensure_ascii=False)],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        sys.stderr.write(f"\n❌ 创建 lookup 字段 '{field['name']}' 失败\n")
        if r.stderr.strip(): sys.stderr.write(f"   stderr:\n{r.stderr}\n")
        if r.stdout.strip(): sys.stderr.write(f"   stdout:\n{r.stdout}\n")
        sys.exit(1)
    print(f"  created lookup: {field['name']}")
EOF

echo "==> 建任务表 formula 字段"
python3 << EOF
import json, subprocess, sys
with open('$SKILL_ROOT/configs/fields/task_table.json') as f:
    cfg = json.load(f)
for field in cfg.get('formula_fields', []):
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    r = subprocess.run(
        ['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$TASK_TBL','--i-have-read-guide','--json',json.dumps(payload, ensure_ascii=False)],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        sys.stderr.write(f"\n❌ 创建 formula 字段 '{field['name']}' 失败\n")
        if r.stderr.strip(): sys.stderr.write(f"   stderr:\n{r.stderr}\n")
        if r.stdout.strip(): sys.stderr.write(f"   stdout:\n{r.stdout}\n")
        sys.exit(1)
    print(f"  created formula: {field['name']}")
EOF

echo "==> 建速查卡表"
CHEAT_TBL=$(lark-cli base +table-create --base-token $BASE_TOKEN --name "速查卡·字段分级权限" | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['table']['id'])")
echo "    cheat_card table_id: $CHEAT_TBL"
CHEAT_PRIMARY=$(lark-cli base +field-list --base-token $BASE_TOKEN --table-id $CHEAT_TBL | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['fields'][0]['id'])")
lark-cli base +field-update --base-token $BASE_TOKEN --table-id $CHEAT_TBL --field-id $CHEAT_PRIMARY \
  --json '{"name":"序号","type":"auto_number","style":{"rules":[{"type":"incremental_number","length":3}]}}' > /dev/null
python3 << EOF
import json, subprocess, sys
with open('$SKILL_ROOT/configs/fields/cheat_card_table.json') as f:
    cfg = json.load(f)
for field in cfg['fields']:
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    r = subprocess.run(
        ['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$CHEAT_TBL','--json',json.dumps(payload, ensure_ascii=False)],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        sys.stderr.write(f"\n❌ 创建字段 '{field['name']}' 失败 (速查卡表)\n")
        if r.stderr.strip(): sys.stderr.write(f"   stderr:\n{r.stderr}\n")
        if r.stdout.strip(): sys.stderr.write(f"   stdout:\n{r.stdout}\n")
        sys.exit(1)
EOF

echo "==> 填充速查卡数据"
(cd $SKILL_ROOT/configs && lark-cli base +record-batch-create --base-token $BASE_TOKEN --table-id $CHEAT_TBL --json @./cheat_card_data.json)

echo "==> 启用高级权限"
lark-cli base +advperm-enable --base-token $BASE_TOKEN > /dev/null

echo "==> 校验 3 个角色配置(预防 lookup/formula/link 等字段误用在 filter)"
for ROLE_FILE in $SKILL_ROOT/configs/roles/super_admin.json $SKILL_ROOT/configs/roles/project_manager.json $SKILL_ROOT/configs/roles/project_member.json; do
  python3 $SKILL_ROOT/scripts/_validate_role.py "$ROLE_FILE" || {
    echo "❌ 角色校验失败,bootstrap 中止。请按上方提示修复对应 JSON 后重试。"
    exit 1
  }
done

echo "==> 创建 3 个角色"
python3 << EOF
import json, subprocess, sys, os
SKILL_ROOT = "$SKILL_ROOT"
BASE_TOKEN = "$BASE_TOKEN"
for rf in ["configs/roles/super_admin.json","configs/roles/project_manager.json","configs/roles/project_member.json"]:
    full = os.path.join(SKILL_ROOT, rf)
    with open(full, encoding="utf-8") as f:
        d = json.load(f)
    cleaned = {k: v for k, v in d.items() if not k.startswith("_")}
    r = subprocess.run(
        ["lark-cli","base","+role-create","--base-token",BASE_TOKEN,
         "--json", json.dumps(cleaned, ensure_ascii=False)],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        sys.stderr.write(f"❌ 创建角色 {rf} 失败:\n{r.stderr}\n")
        sys.exit(1)
    print(f"    ✅ role created: {rf}")
EOF

echo "==> 建项目主表视图"
python3 $SKILL_ROOT/scripts/_apply_views.py \
  --base-token "$BASE_TOKEN" \
  --table-id "$DEFAULT_TBL" \
  --views-config $SKILL_ROOT/configs/views/project_views.json

echo "==> 建任务表视图"
python3 $SKILL_ROOT/scripts/_apply_views.py \
  --base-token "$BASE_TOKEN" \
  --table-id "$TASK_TBL" \
  --views-config $SKILL_ROOT/configs/views/task_views.json

echo "==> 建综合看板·模板"
DASHBOARD_OUT=$(python3 $SKILL_ROOT/scripts/_apply_dashboard.py \
  --base-token "$BASE_TOKEN" \
  --dashboard-name "综合看板·模板" \
  --task-table-name "任务表" \
  --project-name "示例项目:Q2新产品发布" \
  --template $SKILL_ROOT/configs/dashboard_template.json)
echo "$DASHBOARD_OUT"
DASH_ID=$(echo "$DASHBOARD_OUT" | grep -E "^Dashboard ID:" | awk '{print $3}')

echo ""
echo "==> 写状态文件 ~/.pm-skill/state/last_bootstrap.json"
mkdir -p ~/.pm-skill/state
python3 << PYEOF
import json, subprocess, os, sys
from datetime import datetime

BASE_TOKEN = "$BASE_TOKEN"

# 拿所有角色 id
roles_resp = subprocess.run(
    ["lark-cli","base","+role-list","--base-token",BASE_TOKEN],
    capture_output=True, text=True
)
role_ids = {}
if roles_resp.returncode == 0:
    try:
        d = json.loads(roles_resp.stdout)
        items = json.loads(d.get("data",{}).get("data","{}")).get("base_roles", [])
        for raw in items:
            r = json.loads(raw)
            if r.get("role_type") == "custom_role":
                role_ids[r["role_name"]] = r["role_id"]
    except Exception as e:
        sys.stderr.write(f"⚠️  解析 role-list 失败: {e}\n")

state = {
    "base_token": BASE_TOKEN,
    "base_name": "$BASE_NAME",
    "url": "$BASE_URL",
    "tables": {
        "项目主表": "$DEFAULT_TBL",
        "任务表": "$TASK_TBL",
        "速查卡·字段分级权限": "$CHEAT_TBL",
    },
    "dashboard_id": "$DASH_ID",
    "roles": role_ids,
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "schema_version": "v1.1.3",
}

state_path = os.path.expanduser("~/.pm-skill/state/last_bootstrap.json")
with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print(f"    ✅ 状态已写入 {state_path}")
print(f"    💡 后续操作(new-project / 任务批改 / 报告等)需要 base_token / table id 时,请直接 cat 这个文件读,不要从对话上下文中猜或拼凑")
PYEOF

echo ""
echo "==> DONE"
echo "    base_token: $BASE_TOKEN"
echo "    url: $BASE_URL"
echo "    项目主表 id: $DEFAULT_TBL"
echo "    任务表 id: $TASK_TBL"
echo "    速查卡 id: $CHEAT_TBL"
echo "    dashboard_id: $DASH_ID"
echo ""
echo "  💾 完整状态:cat ~/.pm-skill/state/last_bootstrap.json"
echo ""
echo "下一步:"
echo "  1. UI 手动配置:'我的任务'/我负责的项目'视图加'当前用户'过滤;甘特图按状态着色"
echo "  2. 添加项目 → 用 scripts/new-project.sh"
