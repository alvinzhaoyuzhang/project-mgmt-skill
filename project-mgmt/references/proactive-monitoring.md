# 主动监控 · 让 skill 7×24 守望项目

> **核心理念**:用户付费买的不是"问 → 答"的工具,是"**有个助手帮你看着**"的伙伴。
>
> OpenClaw 提供心跳 / 定时任务机制,本 skill 利用它做 5 类监控,让用户离开对话时项目仍被持续关注。

---

## 为什么要主动监控

传统模式(无主动监控):
- 用户记得早上 9 点查项目 → 跑 `pm risk-check` → 看到阻塞
- 用户**忘了** → 项目卡 5 天才发现

主动监控模式:
- 每天 9:00 自动跑早巡 → 有阻塞就**主动飞书 IM 推送**给用户
- 用户**不需要记得** — skill 替他记

**这是 skill 从"工具"升级为"陪伴"的关键能力**。

---

## 5 个推荐定时任务模板

| 模板 | 触发节奏 | 推送对象 | procedure 文件 |
|---|---|---|---|
| 🌅 **每日项目晨检** | 工作日 9:00 | 超级管理员 | `monitors/daily-morning-check.md` |
| 📊 **周报自动生成** | 每周五 10:00 | 超级管理员 | `monitors/weekly-report.md` |
| ⚠️ **阻塞任务实时预警** | 每小时(only when 有变化) | 项目经理(各项目独立) | `monitors/blocker-alert.md` |
| 🎯 **里程碑到期预警** | 每天 9:00 | 项目经理 | `monitors/milestone-warning.md` |
| 📋 **月度复盘提醒** | 每月 1 号 10:00 | 超级管理员 | `monitors/monthly-retro-prompt.md` |

每个 procedure 文件含完整执行步骤(查哪些数据 / 判定规则 / 输出格式 / 通知方式),OpenClaw 在 isolated session 跑时严格按文件执行。

---

## 用户怎么设置(对话指令模板)

skill 把以下 5 段话作为**复制粘贴模板**给用户。用户挑选想启用的复制给 OpenClaw,OpenClaw 自动建对应 cron 任务。

### 模板 1 · 每日项目晨检(推荐启用)

```
帮我设置一个定时任务:每个工作日早上 9:00 跑项目晨检,
按 ~/.openclaw/workspace/skills/project-mgmt/references/monitors/daily-morning-check.md
里的 procedure 执行,有发现就发飞书消息给我(超级管理员),没发现就静默。

定时任务名:项目晨检
schedule:cron "0 9 * * 1-5" (Asia/Shanghai)
session 模式:isolated
通知方式:announce(飞书 IM 推送)
```

### 模板 2 · 周报自动生成(推荐)

```
帮我设置每周五 10:00 自动生成项目周报,
按 ~/.openclaw/workspace/skills/project-mgmt/references/monitors/weekly-report.md 执行。

定时任务名:周报自动生成
schedule:cron "0 10 * * 5" (Asia/Shanghai)
session 模式:isolated
通知方式:announce
```

### 模板 3 · 阻塞实时预警(强烈推荐 PM 用)

```
帮我设置每小时一次的阻塞任务监控,只在有"新增阻塞"或"持续 24h 未跟进"时通知,
按 ~/.openclaw/workspace/skills/project-mgmt/references/monitors/blocker-alert.md 执行。
通知**对应项目的 PM**(从项目主表的"项目经理"字段找)。

定时任务名:阻塞预警
schedule:every 3600000 (每小时)
session 模式:isolated
通知方式:announce
```

### 模板 4 · 里程碑到期预警(推荐)

```
帮我设置每天 9:00 检查未来 7 天到期的里程碑,
按 ~/.openclaw/workspace/skills/project-mgmt/references/monitors/milestone-warning.md 执行。
只对 🔴 高危 / 🟡 关注的里程碑发预警,通知对应项目 PM。

定时任务名:里程碑预警
schedule:cron "0 9 * * *" (Asia/Shanghai)
session 模式:isolated
通知方式:announce
```

### 模板 5 · 月度复盘提醒(可选)

```
帮我设置每月 1 号 10:00 提醒"该做复盘的项目",
按 ~/.openclaw/workspace/skills/project-mgmt/references/monitors/monthly-retro-prompt.md 执行。
通知超级管理员。

定时任务名:月度复盘提醒
schedule:cron "0 10 1 * *" (Asia/Shanghai)
session 模式:isolated
通知方式:announce
```

---

## 推送对象分级原则

| 监控 | 推送对象 | 理由 |
|---|---|---|
| 早巡(全空间汇总) | 超级管理员 | 跨项目视角,只有超管在乎全空间 |
| 周报(全项目汇总) | 超级管理员 | 同上 |
| 月度复盘提醒(空间级) | 超级管理员 | 决策"是否做复盘"是空间级议题 |
| 阻塞预警(项目内) | 项目经理 | 阻塞影响项目,PM 是直接负责人 |
| 里程碑预警(项目内) | 项目经理 | 里程碑达成是 PM 的核心职责 |

(未来可考虑更细 — 如"叶子任务到期前 1 天提醒任务负责人",但首批 5 个模板覆盖 80% 价值。)

---

## skill 何时主动 prompt 用户考虑设置监控

为防止用户**忘了这个能力**,skill 应在以下时机主动提醒:

### 时机 1 · bootstrap.sh 完成后(场景 A 阶段 J)

```
🎉 项目管理空间已建好!

💡 强烈建议你顺便设置 1-2 个定时监控任务,让我每天/每周自动帮你巡检项目,
   不用你记得。最常用的两个:

[1] 每日晨检(工作日 9:00 自动看阻塞 / 临期 / P0 任务)
[2] 周报自动生成(每周五 10:00 自动出周报推飞书)

你要现在就设置吗?(选 1+2 我帮你配,选 [跳过] 之后回来 references/proactive-monitoring.md 看)
```

### 时机 2 · 加完第一个项目后(场景 B 完成屏)

```
🎉 项目"X"已建好!

💡 项目级的监控特别建议:
[3] 阻塞预警(每小时检查,有阻塞推 PM)
[4] 里程碑预警(每天检查未来 7 天到期里程碑)

要启用吗?
```

### 时机 3 · 用户主动问"还有什么我没用的功能"

skill 主动列 5 个监控模板。

### 不要在以下时机主动 prompt(避免骚扰)

- 用户每次跑普通任务操作时
- 用户问 troubleshooting 时
- 用户跑 risk_check / weekly_report 等手动报告后(可能 user 不喜欢自动化)

---

## 状态文件契约(给定时任务读)

所有 procedure 都基于 `~/.pm-skill/state/` 下的状态文件读取 base / 项目 / table id 信息。

**契约**:bootstrap.sh / new-project.sh **必须**写完整状态文件(已在 v1.1.3 实现):
- `~/.pm-skill/state/last_bootstrap.json` — 含 base_token / 三表 id / dashboard_id / role_id
- `~/.pm-skill/state/projects/<项目名>.json` — 每项目的 record_id / task_table_id / dashboard_id

procedure 读这些文件 + 用 OpenClaw 的 `feishu_bitable_app_table_record` 等 native tools 查飞书,**不依赖 lark-cli / Python 脚本**(因为 isolated session exec 命令需 approval,跑不了)。

---

## 已知限制 + 未来扩展

| 限制 | 短期解决 | 长期想做 |
|---|---|---|
| 无法精准定位"项目经理"是谁(项目主表 user 字段是 user_open_id) | 退化:推送给超管 | 把 user_open_id → 飞书 user 信息查出来 |
| OpenClaw 心跳 cron 跨重启是否保留 | 由 OpenClaw 平台决定 | 让用户在每次重启后 OpenClaw 主动列出已设的定时任务 |
| 单空间多项目并发分析慢 | 每个 procedure 内部 page_size=200 | 异步并行查所有项目表 |
| isolated session 没法跑用户授权才能做的事 | 推送提醒给用户,让 ta 手动处理 | 加一个"需要用户确认"队列,user 下次进 main session 一并处理 |

---

## 不要做的事

- ❌ **不要默认全启用** — 用户可能不喜欢被推送轰炸,只在 prompt 时让 ta 自选
- ❌ **不要让定时任务调 lark-cli** — exec 需要 approval,定时跑会卡住
- ❌ **不要在监控里直接改飞书数据** — 监控者只发现+通知,不改状态(改状态需用户授权)
- ❌ **不要把 5 个监控合并成"超级监控任务"** — 各自独立,用户可单独开关
