# 维护操作手册

> 当用户问"加字段 / 加成员 / 归档项目 / 升级 schema"等维护类问题时读这个文件。

## 通用原则

- **所有维护操作幂等**:跑两次结果一样,不用怕重试
- **写操作前必须 preview + confirm**:列出要做什么,等用户说"确认"
- **破坏性操作(删除)有冷却期或额外确认门**

## 12 个维护操作

### 1. 加新项目

```
pm new-project
```

进入 G+ 4 题流程(详见 [new-project-flow.md](new-project-flow.md))。

### 2. 加成员到现有项目

skill 交互:

```
要加什么角色的成员?
  [1] 项目经理(可改任务、协作人、状态)
  [2] 项目成员(只能改自己的任务)
▸ 2

搜索成员姓名/邮箱:
▸ 王明
```

底层执行:
```bash
# 先分享 Base
lark-cli drive permission.members create \
  --params '{"token":"<base>","type":"bitable","need_notification":"true"}' \
  --data '{"member_type":"openid","member_id":"<ou>","perm":"view","type":"user"}'

# 再绑角色(role-update delta merge,role_name+role_type 必传)
lark-cli base +role-update --base-token <base> --role-id <role> \
  --json '{"role_name":"项目成员","role_type":"custom_role","members":[...现有成员... + 新成员]}' --yes
```

⚠️ 注意:`role-update` 是**全量替换 members**,所以必须先 `role-get` 拿当前 members 列表,加上新人,再 update。

### 3. 移除成员

```
pm remove-member --project Q3新版本上线 --member 王明
```

会做 3 件事:
1. 把"负责人 = 王明"的任务,**改为留空**(等你重新分配)
2. 把"协作人"里包含王明的,**移除王明**
3. 解除王明在该项目的角色绑定(从 role.members 数组里移除)

⚠️ **不会**删除王明已经做完的任务记录(历史保留)。

### 4. 加字段(全项目)

要给**所有项目的任务表**加一个"客户类型"字段:

```bash
# 列出所有任务表
lark-cli base +table-list --base-token <base> | grep "任务表"

# 串行给每张表加字段(必须串行,飞书 API 不允许并发)
for tid in tbl_xxx tbl_yyy tbl_zzz; do
  lark-cli base +field-create --base-token <base> --table-id $tid \
    --json '{"name":"客户类型","type":"select","options":[{"name":"TOC"},{"name":"TOB"}]}'
done
```

skill 命令:
```
pm add-field --to all-tasks --name "客户类型" --type select --options "TOC,TOB"
```

只想加到某个项目:
```
pm add-field --to project Q3新版本上线 --name "客户类型" ...
```

### 5. 改字段选项

例:给"状态"字段加新值"待评审":

skill 自动 `field-list` 拿当前 options 数组 + 加新选项 + `field-update`:

```bash
lark-cli base +field-update --base-token <base> --table-id <tid> --field-id <状态字段-id> \
  --json '{"name":"状态","type":"select","options":[...所有原选项..., {"name":"待评审","hue":"Purple","lightness":"Light"}]}'
```

⚠️ **不能改字段类型**(如 select 改 text)— 这种破坏性操作 skill **拒绝执行**,要求用户手动建新字段然后迁移数据。

### 6. 删除字段(危险)

```
pm delete-field --field "客户类型" --from all-tasks
```

⚠️ **强警告**:
- 字段删除后,所有相关数据**永久丢失**(飞书回收站不保留字段级删除)
- 跑命令时 skill 会要用户输 `DELETE` 大写确认
- 有引用关系的字段(被 lookup/formula 引用)skill **拒绝删除**,要先解开引用

### 7. 归档项目

项目结束想归档(保留数据但不再活跃):

```
pm archive-project --project 客户A交付
```

会做:
1. 项目主表中该项目的"状态"改为"已归档"
2. **不删除**任务表,但任务表名前缀加 "[已归档]"
3. **不删除**综合看板,但 dashboard 名加 "[已归档]"
4. 解除所有成员的角色绑定(他们看不到)
5. 仅超管可访问

要重新激活:

```
pm reactivate-project --project 客户A交付
```

### 8. 删除项目(危险)

```
pm delete-project --project 客户A交付
```

⚠️ **强警告**:
- 任务表 + dashboard + 项目主表行 全部删除
- 飞书回收站保留 15 天,过期数据**完全丢失**
- skill 强制要求:
  1. **先 `pm archive-project` 归档(冷却期)**
  2. 至少 7 天后才能 `pm delete-project`

### 9. 升级 schema(skill 出新版)

skill 自身可能升级(比如加了新 formula 字段或新视图)。升级时:

```
pm upgrade
```

skill 会:
1. 对比线上 schema vs skill 当前版本的 schema
2. 显示差异清单(加了什么、改了什么)
3. 让用户逐项确认
4. 串行升级所有任务表
5. 验证

**例**:skill v1.1 加了"复盘日期"字段。升级时:

```
📦  schema 升级 v1.0 → v1.1

变更:
  + 任务表加字段「复盘日期」(datetime)
  + 综合看板加 block「按月任务量」

将影响:
  - 4 张任务表(加字段)
  - 4 个综合看板(加 block)

继续? [y / n / 看详情]
▸ 
```

### 10. 健康检查

```bash
bash $SKILL_ROOT/scripts/verify-template.sh <base-token>
```

**建议每周跑一次** 作为体检。输出:

```
🔍  健康检查
  ✅  3 张表齐全
  ✅  字段完整
  ✅  3 角色齐全
  ✅  综合看板 5 block 齐全

  ⚠️  发现 1 项风险:
      任务表「客户A交付」有 5 个 📋 任务无负责人
      → 提示用户处理
```

### 11. 导出全部数据备份

```
pm export --base <空间名> --output backup.zip
```

导出:
- 所有表的 CSV
- 所有 dashboard 的 JSON 配置
- 所有视图的 JSON 配置
- 角色 + 权限规则

### 12. 卸载 skill

```
pm uninstall
```

会:
1. 列出 skill 创建过的所有空间
2. 让用户逐个选保留 / 删除
3. 删除本地缓存(`~/.pm-skill/`)

⚠️ **不会自动删空间**,得用户逐个确认。

## skill 处理这些操作时的规则

1. **每个写操作前必须 preview**:列出要改什么,等"是 / 确认"
2. **批量操作要分批**:`add-field --to all-tasks` 跨 N 张表,每批后报告进度
3. **失败时不要继续**:某张表加字段失败,暂停问用户 [r 重试 / s 跳过此表 / a 中止全部]
4. **完成后跑 `verify-template.sh` 验收**
5. **状态文件记录变更日志**:`~/.pm-skill/maintenance.log` 记每次操作时间和内容,方便回溯
