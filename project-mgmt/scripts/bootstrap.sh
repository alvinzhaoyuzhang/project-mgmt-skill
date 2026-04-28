#!/usr/bin/env bash
# Bootstrap: 从零创建一个"项目管理中心"工作区 Base
#
# 前置:OpenClaw 已装飞书插件 (lark-cli) 并已登录
# 用法:bash <skill>/scripts/bootstrap.sh "项目管理中心·业务方向"
# 输出:新 Base 的 base_token 和 URL

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
import json, subprocess
with open('$SKILL_ROOT/configs/fields/project_table.json') as f:
    cfg = json.load(f)
for field in cfg['fields']:
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    subprocess.run(['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$DEFAULT_TBL','--json',json.dumps(payload, ensure_ascii=False)], check=True)
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
import json, subprocess
with open('$SKILL_ROOT/configs/fields/task_table.json') as f:
    cfg = json.load(f)
for field in cfg['fields']:
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    subprocess.run(['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$TASK_TBL','--json',json.dumps(payload, ensure_ascii=False)], check=True)
    print(f"  created: {field['name']}")
EOF

echo "==> 建任务表 lookup 字段"
python3 << EOF
import json, subprocess
with open('$SKILL_ROOT/configs/fields/task_table.json') as f:
    cfg = json.load(f)
for field in cfg.get('lookup_fields', []):
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    subprocess.run(['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$TASK_TBL','--i-have-read-guide','--json',json.dumps(payload, ensure_ascii=False)], check=True)
    print(f"  created lookup: {field['name']}")
EOF

echo "==> 建任务表 formula 字段"
python3 << EOF
import json, subprocess
with open('$SKILL_ROOT/configs/fields/task_table.json') as f:
    cfg = json.load(f)
for field in cfg.get('formula_fields', []):
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    subprocess.run(['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$TASK_TBL','--i-have-read-guide','--json',json.dumps(payload, ensure_ascii=False)], check=True)
    print(f"  created formula: {field['name']}")
EOF

echo "==> 建速查卡表"
CHEAT_TBL=$(lark-cli base +table-create --base-token $BASE_TOKEN --name "速查卡·字段分级权限" | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['table']['id'])")
echo "    cheat_card table_id: $CHEAT_TBL"
CHEAT_PRIMARY=$(lark-cli base +field-list --base-token $BASE_TOKEN --table-id $CHEAT_TBL | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['fields'][0]['id'])")
lark-cli base +field-update --base-token $BASE_TOKEN --table-id $CHEAT_TBL --field-id $CHEAT_PRIMARY \
  --json '{"name":"序号","type":"auto_number","style":{"rules":[{"type":"incremental_number","length":3}]}}' > /dev/null
python3 << EOF
import json, subprocess
with open('$SKILL_ROOT/configs/fields/cheat_card_table.json') as f:
    cfg = json.load(f)
for field in cfg['fields']:
    payload = {k:v for k,v in field.items() if not k.startswith('_')}
    subprocess.run(['lark-cli','base','+field-create','--base-token','$BASE_TOKEN','--table-id','$CHEAT_TBL','--json',json.dumps(payload, ensure_ascii=False)], check=True)
EOF

echo "==> 填充速查卡数据"
(cd $SKILL_ROOT/configs && lark-cli base +record-batch-create --base-token $BASE_TOKEN --table-id $CHEAT_TBL --json @./cheat_card_data.json)

echo "==> 启用高级权限"
lark-cli base +advperm-enable --base-token $BASE_TOKEN > /dev/null

echo "==> 创建 3 个角色"
for ROLE_FILE in $SKILL_ROOT/configs/roles/super_admin.json $SKILL_ROOT/configs/roles/project_manager.json $SKILL_ROOT/configs/roles/project_member.json; do
  lark-cli base +role-create --base-token $BASE_TOKEN --json "$(cat $ROLE_FILE)" > /dev/null
  echo "    role created from: $ROLE_FILE"
done

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
python3 $SKILL_ROOT/scripts/_apply_dashboard.py \
  --base-token "$BASE_TOKEN" \
  --dashboard-name "综合看板·模板" \
  --task-table-name "任务表" \
  --project-name "示例项目:Q2新产品发布" \
  --template $SKILL_ROOT/configs/dashboard_template.json

echo ""
echo "==> DONE"
echo "    base_token: $BASE_TOKEN"
echo "    url: $BASE_URL"
echo "    项目主表 id: $DEFAULT_TBL"
echo "    任务表 id: $TASK_TBL"
echo "    速查卡 id: $CHEAT_TBL"
echo ""
echo "下一步:"
echo "  1. UI 手动配置:'我的任务'/我负责的项目'视图加'当前用户'过滤;甘特图按状态着色"
echo "  2. 添加项目 → 用 scripts/new-project.sh"
