# 故障排查

> 当用户遇到错误时读这个文件。按错误现象索引,给出诊断 + 修复路径。

---

## 0. 通用诊断 SOP(任何报错先读这一节)

**这是流程契约,LLM 必须遵守:**

### 规则 0.1 · 出现任何"X 失败"类报错时,先 list 验证状态,再下结论

**禁止**只看 Python `CalledProcessError` / lark-cli 的 exit code 就直接给"建议手动建 / 等会再试 / 找飞书支持"这类套话。

**必做的诊断步骤**:

1. **拿原始报错** — 不要看用户/上层的转述,要看 lark-cli 的原始 stdout JSON,长得像:
   ```json
   {"entity":"user","error":{"type":"api_error","code":1,"message":"...","detail":{"code":"800xxxxx",...}}}
   ```
2. **看 detail.code** — 飞书 API 错误码定位真正问题:
   - `800005008` = 名称冲突(name 已存在)
   - `800008006` = 服务端 internal_error,**很可能是 silent success**(资源实际已建,API 谎报)
   - `1254xxx` = 权限不足
3. **list 验证实际状态** — 比如 dashboard create 报错,跑 `+dashboard-list` 看真不真存在
4. **根据 list 结果分流** — 实际成功 → 跳过该步;实际失败 → 决定 retry 还是改方案

### 规则 0.2 · `.py` 用 `python3` 跑,`.sh` 用 `bash` 跑

**别混用**。常见错误:`bash _apply_dashboard.py`(.py 是 Python 脚本)→ 立刻 SyntaxError。

**判断方式**:看脚本第一行 shebang
- `#!/usr/bin/env python3` → 用 `python3 some.py`(或 `./some.py` 如有 +x)
- `#!/usr/bin/env bash` → 用 `bash some.sh`(或 `./some.sh` 如有 +x)

### 规则 0.3 · 飞书 API `code=800008006: failed to get dashboard` 不是临时故障

这是反复观察到的**模式化 bug**:
- create 命令服务端实际成功,但 API 在 follow-up "get" 步骤失败
- 表现为脚本看到 error 退出,但 dashboard / block 实际已建
- 称为 **"silent success"**

**正确处理**:**绝对不要重试整个 bootstrap.sh**(会创建一堆重复资源)。
应当:
1. List 该资源(dashboard / block / table)看实际状态
2. 已建 → 跳过,继续下一步
3. 未建 → 单步 retry(2-3 次,每次间隔 3 秒)
4. v1.1.1 后的 `_apply_dashboard.py` 已自动处理这个模式,无需手动 retry

---

## 1. 飞书 CLI / 登录类

### 1.1 `lark-cli: command not found`

**原因**:飞书 CLI 未安装,或装完后 AI 工具没重启,系统 PATH 上找不到 `lark-cli` 命令。

#### 修复方式 A · 推荐:让 AI 替用户装(零终端操作)

skill 可以**主动**引导:

> "我注意到飞书 CLI 还没装,我帮你装,大约 2-3 分钟,你不用碰终端。开始吗?"

用户同意后,skill 走以下步骤:

1. **WebFetch 官方安装指南**(或直接 Bash 跑 npx,二选一):
   ```
   https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md
   ```
2. **执行 Bash 安装**:`npx @larksuite/cli@latest install`
   - 中途会问应用配置 → 默认"**创建新应用**" + 语言"**简体中文**"
3. **明确告知用户重启**:"装好了。现在请你**重启 Claude Code / OpenClaw**,然后重新进来,我再帮你做剩下的。"
   - 这步**绝对不能跳过** — 漏掉重启是用户反复装不上的最常见原因。
4. 用户重启后,再 Bash 跑 `lark-cli auth login`,引导用户在浏览器中确认。

#### 修复方式 B · 给老手用户的"魔法咒语"

如果用户是想自己掌控的开发者,告诉 ta 这一句直接发给 AI 工具就行:

```
帮我安装飞书 CLI:https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md
```

AI 会按上面方式 A 的步骤跑。

#### 修复方式 C · 纯手动(终端老用户)

```bash
npx @larksuite/cli@latest install   # 1. 装(交互式)
# 2. 重启 AI 工具
lark-cli auth login                  # 3. 授权
```

---

> 提示:`lark-cli` 是飞书官方开源 CLI(npm 包 `@larksuite/cli`),与 OpenClaw 的"飞书官方插件"是两码事——OpenClaw 插件是平台自己用的,本 skill 不依赖。

### 1.2 `flightcheck failed: 飞书未登录` / `lark-cli auth status` 报未登录

**原因**:`lark-cli` 的 token 过期、被清除,或还没登录过。

**修复**:让用户跑

```bash
lark-cli auth login
```

按提示在浏览器中确认授权。完成后输 `r` 重试。

### 1.3 想切换飞书账号

```bash
lark-cli auth logout
lark-cli auth login   # 用另一个账号登录
```

完成后输 `r` 重试 skill。

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

### 8.4 Dashboard 是空壳(看到 dashboard 但里面 0 个图表)

**症状**:打开 dashboard 是空白页 / `+dashboard-block-list` 返回 `total: 0`。

**根因**:`_apply_dashboard.py` 在创建 dashboard 时遇到飞书 `800008006: failed to get dashboard`(silent success — 服务端实际成功),退出。重跑时 v1.1.0 的幂等检测看到 dashboard 已存在就 skip,**导致 5 个 block 永远没机会建**。

**v1.1.1 已修复**:新版 `_apply_dashboard.py` 现在区分"已完整(>= 1 block)"vs"空壳(0 block)",空壳会**复用 dashboard_id 继续补建 block**。

**手动救场**(如果你卡在 v1.1.0):
```bash
# 1. 看实际 block 数
lark-cli base +dashboard-block-list --base-token <BASE> --dashboard-id <DASH>

# 2. 如果是 0,删掉空壳后重跑脚本(v1.1.0 的写法)
lark-cli base +dashboard-delete --base-token <BASE> --dashboard-id <DASH> --yes
python3 <SKILL_ROOT>/scripts/_apply_dashboard.py \
  --base-token <BASE> \
  --dashboard-name "综合看板·模板" \
  --task-table-name "任务表" \
  --project-name "示例项目:Q2新产品发布" \
  --template <SKILL_ROOT>/configs/dashboard_template.json
```

升级到 v1.1.1 后无需手动救场。

### 8.5 飞书 API 反复报 `800008006: failed to get dashboard`

**症状**:dashboard 或 block create 命令返回 `code=800008006`,看起来失败,但其实**资源已建出来**。

**根因**:飞书服务端在 create 流程的 "get-after-create" 步骤间歇性失败(API 内部 race condition)。这是飞书侧 bug,不是我们代码问题。

**正确处理 SOP**(详见 §0.3):
- ❌ 不要"等 5-10 分钟再试整个 bootstrap"(会重复建 + 撞 name 冲突)
- ✅ 先 list 看资源是否实际已建
- ✅ 已建 → 跳过该步,继续下一步
- ✅ 未建 → 单步 retry 2-3 次,间隔 3 秒
- ✅ v1.1.1 的 `_apply_dashboard.py` 已自动处理

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
