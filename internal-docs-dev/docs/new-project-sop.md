# 新建项目 SOP(B1 方案)

> 每个项目 = 工作区 Base 里 1 张独立任务表 + 1 个独立 dashboard。
> 本文档描述手工执行流程;skill 封装后会提供 `+new-project 项目名` 一键命令。

## 前置条件

- 工作区 Base 已建好(通常按业务方向建,如"AI 产品开发")
- 通用模板 Base 可访问(用于读取字段 schema 作为参考)
- 有 admin 权限(或角色 = 超级管理员)

## 步骤

### 1. 项目主表加一行

在工作区 Base 的**项目主表**增加 1 行:

| 字段 | 填写 |
|---|---|
| 项目名称 | 如 `XX 产品开发` |
| 项目经理 | 选人 |
| 保密等级 | L1/L2/L3/L4 之一 |
| 状态 | 筹备 / 进行中 |
| 开始日期 / 计划完成日期 | 时间范围 |

CLI:

```bash
lark-cli base +record-create --base-token <workspace> --table-id <项目主表> \
  --json '{"项目名称":"XX","项目经理":[{"id":"ou_xxx"}],"保密等级":"L2 常规",...}'
```

**记录返回的 `record_id`**,后续要用。

### 2. 克隆任务表

从模板任务表(通用模板 Base 的 `任务表`)读出 schema,在工作区创建同结构表:

```bash
# 读模板字段
lark-cli base +field-list --base-token <template> --table-id <任务表模板> > /tmp/fields.json

# 根据 fields.json 构造 +table-create 的 --fields 参数
# 注意:link 字段要改 target_table 为当前工作区的项目主表 table_id
# 注意:lookup/formula 要保持引用关系
lark-cli base +table-create --base-token <workspace> \
  --name "任务表·XX产品开发" \
  --fields '<field schema>'
```

Skill 封装后自动处理 link 字段的 target_table 重绑。

### 2.5 清空样例记录 ⚠️ 必做

模板 Base 的任务表故意保留了 9 条样例任务,克隆后这些会一并复制过来,**必须先清空**:

```bash
# 列出克隆后新任务表的所有记录
lark-cli base +record-list --base-token <workspace> --table-id <新任务表> --limit 500

# 批量删除(从 record-list 拿 record_ids,循环删)
for rid in $(lark-cli base +record-list ... | jq -r '.data.data[][0]'); do
  lark-cli base +record-delete --base-token <workspace> --table-id <新任务表> --record-id $rid --yes
done
```

Skill `+new-project` 命令会自动做这一步。

### 3. 克隆视图

逐个建模板上的 9 个视图:

- 全部任务(树状浏览) · grid
- 我的任务 · grid(需 UI 手动加当前用户过滤)
- 里程碑看板 · grid
- 阻塞与延期 · grid
- 甘特图 · gantt
- 状态看板 · kanban
- 按模块浏览 · grid
- 状态异常监控 · grid
- 本周到期 · grid

```bash
lark-cli base +view-create --base-token <workspace> --table-id <新任务表> \
  --name "全部任务(树状浏览)" --view-type grid \
  --property '<view config>'
```

### 4. 克隆综合看板

通用模板 Base 里有 `综合看板·模板`(dashboard_id: `blko4ahuf9TE3vvn`)作为克隆源,5 个 block 结构:

1. 里程碑进度矩阵(按状态堆叠) · bar
2. 一级工作完成率对比(%) · column
3. 时间压力分布(按到期时段+状态) · column
4. 任务状态(按级别堆叠) · column
5. 说明 · text

```bash
# 列出模板 block
lark-cli base +dashboard-block-list --base-token <template> --dashboard-id blko4ahuf9TE3vvn

# 读每个 block 详情(拿 data_config 结构)
lark-cli base +dashboard-block-get --base-token <template> --dashboard-id blko4ahuf9TE3vvn --block-id <blockId>

# 在工作区新建 dashboard
lark-cli base +dashboard-create --base-token <workspace> --name "XX 产品开发 · 综合看板"

# 串行建 5 个 block,每个的 data_config 需要:
# - table_name 改为 "任务表·XX产品开发"
# - filter.所属项目名称 value 改为 "<新项目名>"
# 其他不动
# 顺序:先建 4 个图表 → 跑 arrange → 再建 text(让 text 落到底部)
```

Skill `+new-project` 命令会自动完成这些替换。

### 5. 绑定权限角色

```bash
# 给 PM 绑定项目经理角色(不授权整个 role,而是创建一个针对此项目的规则)
lark-cli base +role-update --base-token <workspace> --role-id <PM role> \
  --yes --json '<加上对本项目表的权限规则>'

# 或者在 角色 → 成员 中添加 PM 的 open_id
lark-cli base +role-assign --base-token <workspace> --role-id <PM role> \
  --member-id ou_xxx
```

细节见 design/03-permissions.md。

### 6. 分享 Base

在飞书 UI 里把 Base 分享给 PM + 成员(触发通知)。

## 要点 · 易错地方

1. **link 字段的 target_table** — 克隆任务表时,`所属项目` link 要重新绑到目标工作区的项目主表 table_id,不能沿用模板的
2. **lookup / formula 字段的引用** — 所有引用的其他字段名必须和新表里的一致(字段名相同即可)
3. **父任务 link 是自引用** — 克隆后自动指向新任务表自己
4. **综合看板 filter 必须按项目过滤** — `所属项目名称 is <项目名>`,不然会显示别的项目数据
5. **视图里的"当前用户"过滤** — CLI 无法建,成员首次用时在 UI 里手动加一次

## skill 自动化后的命令

```bash
skill project-mgmt new-project \
  --workspace-base <token> \
  --project-name "XX 产品开发" \
  --pm ou_xxxxxxx \
  --confidentiality L2 \
  --members ou_xx,ou_yy

# → 自动执行步骤 1-5,返回新任务表 ID 和 dashboard ID
```

## 删除项目

```bash
# 1. 软删:把项目主表该行的"状态"改为"已归档"
# 2. 硬删:依次删 dashboard、任务表、项目主表记录
#    注意:删任务表会删除其所有任务记录,不可逆,先导出
```
