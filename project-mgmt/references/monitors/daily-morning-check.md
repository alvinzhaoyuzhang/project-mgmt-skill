# 每日项目晨检 · 监控 procedure

> 此文件由**定时任务**触发(默认 cron `0 9 * * 1-5`,工作日 9:00),非用户对话触发。
>
> **执行环境**:OpenClaw isolated session(没有人类判断力),按本文规则严格执行。
>
> **触发方**:OpenClaw 心跳/cron 机制按 schedule 调度。

## 任务目标

在用户开始一天工作前,扫描所有项目状态,**只在有需要关注的发现时**通知用户(无声运行原则,无内容时不打扰)。

## 执行步骤(严格按序)

### Step 1 · 读状态文件,拿 base_token / table id

```bash
cat ~/.pm-skill/state/last_bootstrap.json
```

提取:
- `base_token`
- `tables.项目主表` → 项目主表 table_id
- `tables.任务表` → 模板任务表 table_id (B1 架构)
- 或扫 `~/.pm-skill/state/projects/*.json` 拿每个项目的 task_table_id (B2 架构)

**没有状态文件?** → 静默退出(用户还没建过空间,这条 cron 暂不该跑)。

### Step 2 · 用 OpenClaw 飞书工具读任务表

调用 `feishu_bitable_app_table_record` action=list,**对每个任务表**:

```yaml
app_token: <base_token>
table_id: <task_table_id>
field_names: ["任务编号","任务名称","任务级别","状态","优先级","进度","计划完成日期","所属项目名称","负责人","风险与阻塞","最近更新"]
filter:
  conjunction: and
  conditions:
    - field_name: "任务级别"
      operator: "is"
      value: "📋 二级工作"     # 只看叶子任务
    - field_name: "状态"
      operator: "isNot"
      value: "已完成"
    - field_name: "状态"
      operator: "isNot"
      value: "已取消"
page_size: 200
```

### Step 3 · 三类发现的判定规则

把上一步拿到的活跃叶子任务,分到 3 类:

| 类别 | 判定规则 |
|---|---|
| 🔴 **严重风险** | 状态=阻塞 且 (今天 - 风险与阻塞填写日期) ≥ 3 天<br>**OR** 优先级=P0-紧急 且 (计划完成日期 - 今天) ≤ 3 天 且 状态 ∈ (进行中, 未开始) |
| 🟡 **关注项** | 状态=阻塞 且 阻塞 < 3 天<br>**OR** 状态=延期<br>**OR** 优先级=P1-高 且 (计划完成日期 - 今天) ≤ 3 天 |
| ⏰ **临期** | (计划完成日期 - 今天) ∈ [0, 3] 天 且 状态 ∈ (进行中, 未开始) 且 优先级 ∈ (P2, P3) |

### Step 4 · 决定是否通知

- **三类都为空** → 静默退出,不发任何消息(无声运行)
- **任一非空** → 进 Step 5

### Step 5 · 组装 markdown 推送给"超级管理员"

获取超管 user_id:从 `last_bootstrap.json.roles.超级管理员` 拿 role_id,然后 `feishu_bitable_app_table_record` 查角色绑定的 user_open_id(或直接用当前 OAuth 账号 = 超管)。

模板:

```markdown
📋 项目晨检报告 · {YYYY-MM-DD}

🔴 **严重风险**({count} 项 — 必须今天处理)

- **{任务编号}** {任务名称} — {负责人} — 阻塞 {n} 天
  - 阻塞:{风险与阻塞 字段值,截 80 字}
- **{任务编号}** {任务名称} — {负责人} — P0,后天到期但还没开始

🟡 **关注项**({count} 项 — 知情即可)

- **{任务编号}** {任务名称} — {负责人} — 延期
- ...

⏰ **临期**({count} 项 — 主动提醒,免遗忘)

- **{任务编号}** {任务名称} — 后天到期 — {负责人}
- ...

---
> 只列出活跃叶子任务(已完成/已取消不列)。
> 此报告由 project-mgmt skill 每工作日 9:00 自动生成。
```

### Step 6 · 通过 OpenClaw 发送

```yaml
tool: feishu_im_user_message
action: send
msg_type: text  (或 post 富文本)
content: <上面 markdown>
receive_id: <超管 user_open_id>
receive_id_type: open_id
```

## 边界情况

| 情况 | 处理 |
|---|---|
| 状态文件不存在 | 静默退出,不报错 |
| base 已被用户删除 | 状态文件还在但 base 404 → 在用户下次进 main session 时提示"检测到 base 已删,要不要清理状态文件?" |
| 飞书 API 报 internal_error 800008006 | retry 1 次,sleep 3s 再试;再失败就静默退出(非致命) |
| 用户没启用保密分级 | 没"任务保密等级"字段也不影响,该 procedure 不依赖此字段 |
| 单个项目内 0 活跃任务 | 跳过该项目,看下一个 |

## 不要做的事

- ❌ 不要发"今天没问题,一切正常"的报告 — 用户在场时这是过度通知,**有发现才打扰**
- ❌ 不要建议"要不要把 X 任务标完成?" — isolated session 无人确认,只汇报状态不动数据
- ❌ 不要尝试 retry 整个 cron 任务 — 一次失败就放过,等下次定时再跑
