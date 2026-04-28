# 故障排查

> 当用户遇到错误时读这个文件。按错误现象索引,给出诊断 + 修复路径。

## 1. 飞书登录 / 插件类

### 1.1 `lark-cli: command not found`

**原因**:OpenClaw 飞书插件未安装。

**修复**:让用户跑

```bash
npx -y @larksuite/openclaw-lark install
```

约 30 秒装好。完成后在 skill 内输 `r` 重试。

### 1.2 `flightcheck failed: 飞书未登录`

**原因**:OpenClaw 通常自动保持登录,出现这条说明 token 过期或切换过账号未重连。

**修复**:让用户回到 OpenClaw,通过飞书机器人重新连接,完成后输 `r` 重试。

### 1.3 想切换飞书账号

skill 内**无法直接切**(OpenClaw 飞书插件托管登录态)。
让用户:
1. 回到 OpenClaw,通过飞书机器人重新绑定其他账号
2. 输 `r` 重试 skill

## 2. 网络类

### 2.1 "网络无法访问飞书"

**排查步骤**:

1. 浏览器打开 `https://open.feishu.cn` —— 能打开吗?
   - 不能 → 公司网络/VPN 屏蔽,联系 IT 加白名单
2. 用户在 VPN 里吗?
   - 是 → 关 VPN 重试
3. 飞书自身宕机?查 status.feishu.cn

### 2.2 API 限速 `Rate limit exceeded`

**原因**:短时间内调用太多 API。

**自动处理**:skill 自动等 60 秒后重试。
**手动**:把 wizard 暂停,15 分钟后再续跑。

## 3. 权限类

### 3.1 `Permission denied [99991679]` 调用 +base-create

**原因**:用户飞书租户禁用了"多维表格"或权限不足。

**修复**:
- 联系 IT 开通"多维表格"应用权限
- 个人飞书可能受限,建议升级到企业版

### 3.2 `403 Forbidden` 操作已存在 Base

**原因**:
- 用户不是该 Base 的超管 → 联系空间所有者授权
- Base 已被删除或在回收站

### 3.3 `Permission denied bitable:app:readonly` 调用 lark-cli api

**原因**:走了裸 API 路径,scope 不够。

**修复**:**改用 `lark-cli base +xxx` 包装命令**,不要走 `lark-cli api`。

## 4. 字段冲突类

### 4.1 字段名重复

**原因**:wizard 之前中断遗留,部分字段已建。

**修复**:
1. 选 [r] 重试,skill 自动跳过已存在的字段
2. 或选 [u] 撤销,完全删除空间从头来过(`pm init --reset`)

### 4.2 `role name cannot be empty` 调用 role-update

**原因**:`role-update` 是 delta merge,但 `role_name` + `role_type` 必须传(即使值不变)。

**修复**:
```bash
lark-cli base +role-update --base-token <base> --role-id <role> \
  --json '{"role_name":"项目经理","role_type":"custom_role","members":[...]}' --yes
```

不传 role_name 或 role_type 都会报这个错。

### 4.3 `Required.search_fields` 调用 record-search

**原因**:`record-search` 必须传 `search_fields` 数组。

**修复**:
```bash
lark-cli base +record-search --base-token <base> --table-id <tid> \
  --json '{"keyword":"X","search_fields":["任务编号"]}'
```

## 5. 飞书容量类

### 5.1 `已达单 Base 表数量上限(20)`

**原因**:多任务表方案下加了太多项目(免费版 ~20 张表上限)。

**修复路径**:
1. 归档老项目(`pm archive-project`)→ 不真删表但减少视觉负担
2. 升级到多空间方案(`pm migrate-to-multi-spaces`)→ 拆分到多个 Base
3. 升级飞书租户到付费版(高级版 50 张表)

## 6. 数据丢失恢复

### 6.1 误删了一个任务

飞书回收站(15 天):
1. 打开任务表 → 工具栏 → 回收站
2. 找到该记录 → 还原

### 6.2 误删了一整张任务表

同样 15 天回收站:
1. 飞书工作台找到该 Base → 右键 → 历史版本
2. 选删除前的版本恢复

### 6.3 误删了整个空间

Base 级回收站(15 天):
1. 飞书工作台 → 回收站
2. 找到该 Base → 还原

## 7. wizard 状态问题

### 7.1 上次状态文件损坏

**修复**:

```
pm init --reset
```

会清空本地状态从头开始。
飞书内已建的部分需要手动删除(或用 `pm clean` 清残留)。

### 7.2 多次 Ctrl+C 后状态混乱

```
pm init --reset
```

强制重置。

## 8. Dashboard 问题

### 8.1 Dashboard text block 换行没保留

**原因**:飞书 API 剥离 `\n`。

**修复**:用 `\r\n` 代替 `\n`(API 保留 `\r`)。

### 8.2 `+dashboard-arrange` 把 text block 顶到顶部

**原因**:arrange 默认把 text 放第一位。

**修复**:**先 arrange 4 个图表,后 create text** —— text 默认追加到最后。

### 8.3 Dashboard filter 对 link 字段 contains 不工作

**原因**:飞书 dashboard filter 对 link 字段的 `contains` 操作符返回 0 条。

**修复**:加一个 `所属项目名称` lookup 字段(从 link 字段拉文本),filter 改用 text 字段的 `is` 操作符。

## 9. 视图配置问题

### 9.1 「我的任务」视图找不到"当前用户"过滤选项

**原因**:部分飞书租户/版本不支持"当前用户"动态变量(常见于个人版)。

**Fallback 方案**:
- 让每个成员自己**复制**「我的任务」视图为「我的任务-自己名字」
- 给复制的视图加筛选 `负责人 = 自己具体名字`
- 飞书视图复制默认开放,每人复制只他自己用

也可以告诉用户:
- 权限规则已经做了行级过滤,即使「我的任务」视图无过滤,成员打开任何视图也只看到自己的(权限层挡其他)
- 所以视图过滤只是 UX 优化,不影响功能

## 10. 部署完成后访问问题

### 10.1 团队成员说没收到飞书通知

**排查**:
1. `lark-cli drive permission.members create` 是否传了 `need_notification: "true"`?
2. 用户飞书消息是否被静音?
3. 是否分享 Base 时用了错误的 open_id(用 `lark-cli contact user.search` 验证)?

### 10.2 团队成员打开 Base 看不到任何内容

**排查**:
1. 角色绑定是否成功?(`lark-cli base +role-get` 看 members 数组)
2. 高级权限是否已启用?(`lark-cli base +advperm-enable`)
3. 行级过滤条件是否正确?(项目成员应能看到自己负责的)

## 11. 安装/卸载

### 11.1 想完全卸载 skill

```
pm uninstall
```

会列出 skill 创建过的所有空间,让用户逐个选保留 / 删除。删除本地缓存(`~/.pm-skill/`)。

⚠️ **不会自动删空间**,防止误操作。

### 11.2 个人版飞书能用吗?

可以,但有限制:
- ✅ 多维表格创建、字段、视图、dashboard 全部可用
- ⚠️ "高级权限"功能可能受限,3 角色权限隔离弱化
- ⚠️ Base 表数量上限可能更严

建议:个人版玩耍 OK,企业用建议升级付费租户。

## 12. 升级失败

### 12.1 `pm upgrade` 中途挂了

skill 会写一个升级日志 `~/.pm-skill/upgrade.log`。

**修复**:
1. 看日志最后一步是什么
2. 如果是某张表加字段失败,手动跑 `lark-cli base +field-create ...`
3. 跑 `pm verify --base <token>` 确认是否补齐
4. 如果差异列表显示已无新增,说明已升级完(只是日志没写完)

## 13. 常见问题杂项

### 13.1 我的所有项目的"模块"字段不一样,能统一吗?

可以。跑 `pm config edit-modules`,选项会全 Base 同步。

### 13.2 改完 schema 想生效,要做什么?

skill 改的是模板。已存在的项目任务表**不会自动同步**。
需要跑 `pm upgrade` 把 schema 变更应用到所有现有任务表。

### 13.3 想看哪些表是 skill 建的?

```
pm list-bases
```

读 `~/.pm-skill/registered_bases.json`。

## skill 处理用户报错时的规则

1. **三档展示错误信息**:简短提示 → 展开详情(d) → 联系支持(s)
2. **永远给"下一步"**:不要只丢一个错误码,要给具体修复步骤或重试选项
3. **明确说"这是飞书平台限制还是 skill bug"**,让用户知道找谁解决
