---
name: project-mgmt
description: "在飞书租户内搭建并维护一套结构化项目管理工作区(基于多维表格 Base),并辅助 PM 和成员日常运行项目。三类核心场景:(1)结构搭建类 — 用户明确要建立项目管理工具、搭建任务跟踪系统、管理多个并行项目、追踪 WBS/里程碑/工作包、配置角色权限,或在已有项目管理空间加项目/邀请成员/做维护;(2)日常运行类 — 已有空间的项目经理或成员要更新任务进度、标记任务完成/阻塞/延期、添加任务、查询自己或项目的工作状态、重新分配任务、处理阻塞、写日报周报、做跨项目巡检;(3)文档驱动类 — 用户提供飞书云文档(会议纪要/周报/工作计划/PRD/OKR docx 链接)要求基于文档内容批量建立项目结构、批量加任务、或批量更新任务完成情况。典型触发短语:'帮我搭一套项目管理'、'我的项目管理空间加新项目'、'帮我把这个任务标完成'、'我的 X 任务进度更新到 75%'、'我的任务卡住了帮我标阻塞'、'帮我看下哪些任务延期了'、'把张三的任务转给李四'、'根据这份会议纪要在我的项目管理空间建任务'、'根据周报批量更新任务进度'、'PRD 里列的任务帮我加进去'、'项目管理空间报错怎么办'。特别注意:用户自称'项目经理 / PM / 我管 X 个项目'并询问任务状态(哪些任务卡住/延期/P0 P1 阻塞/负责人负载)时,即使未明说'飞书',也属本 skill 服务范围 — 默认上下文是该 PM 已装本 skill 的项目管理空间。本 skill 还提供:**AI 拆解辅助**(给个项目目标 → 推荐里程碑/工作包/叶子任务结构);**自动周报 / 风险预警 / 复盘报告**(读飞书数据自动出 markdown 报告);**从云文档(docx)批量建任务或更新进度**。本 skill 通过对话引导完成结构搭建、主动帮用户在飞书内修改任务记录、查询项目状态、调整分工。不要为以下场景触发:单纯讨论项目管理理论/方法论(WBS、敏捷、Scrum 等)、非飞书的项目工具(Asana/Notion/Trello/Jira)、与项目管理空间无关的飞书表操作(单纯查表、改单条数据 → 让 lark-base skill 处理)、纯文档操作(转格式/写文档 → 让 lark-doc skill 处理)、飞书项目(MeegoOS / lark project)产品(那是不同产品族)。"
metadata:
  requires:
    bins: ["lark-cli"]
  cliHelp: "lark-cli base --help"
---

# 飞书项目管理工作区 · 安装与维护

> **前置条件**:OpenClaw 已装飞书插件 (`lark-cli`),用户已登录飞书账号。
> **底层依赖**:本 skill 通过 `lark-cli base/drive` 命令操作飞书,**不写裸 API**。

## 1. 何时使用本 skill

### 1.1 触发场景

仅在用户表达**明确的飞书项目管理意图**时使用:

- 用户要在飞书内**搭建一套**项目管理工具(首装)
- 用户已有"项目管理中心"空间,要**加新项目 / 邀请成员**
- 用户问 PM 或成员**怎么用**这个空间
- 用户要**维护**(加字段、改字段选项、归档项目、健康检查)
- 用户**遇到报错**(网络、权限、字段冲突等)

### 1.2 不触发场景

- 用户讨论项目管理**理论/方法论**(WBS、敏捷、Scrum 等抽象概念)
- 用户提到**非飞书的项目工具**(Asana / Notion / Trello / Jira / Monday)
- 用户做**抽象任务管理**询问("怎么管理任务"无飞书上下文)
- 用户已经在用飞书但要做的事跟"项目管理空间"无关(单纯查表、改单条数据等 → 让 lark-base skill 处理)

## 2. 前置约束(执行前必检)

执行任何写飞书操作前,跑过下面检查清单:

```bash
# 1. 飞书插件就位
lark-cli --version  # 期望 ≥ 1.0.18

# 2. 用户已登录(skill 应假设已登录;未登录时引导用户去 OpenClaw 重新连接)
lark-cli auth whoami
```

**不要**在 SKILL.md 主流程里 OAuth 用户 — OpenClaw 的飞书插件已托管登录,例外路径由它自己处理(详情见 `references/troubleshooting.md` 第 1 节)。

## 3. 主流程 · 场景路由

skill 启动后,**先判断用户意图属于 4 大场景中的哪个**,再进入对应流程:

| 用户意图 | 进入场景 | 核心动作 | 频率 | 主要身份 |
|---|---|---|---|---|
| 第一次用 / 没有任何空间 | **A · 首次安装** | 跑 9 阶段 wizard,产出 1 个空间 | 一次 | admin |
| 已有空间,要加新项目 | **B · 加项目** | 跑 G+ 子流程,产出 1 张新任务表 + 1 个 dashboard | 偶尔 | admin / PM |
| 已有空间,**主动操作任务** | **C · 日常任务操作** | **skill 帮用户在飞书内修改任务记录** | **每天** | **PM + 成员** |
| 已有空间,要维护 / 排错 | **D · 维护排错** | 路由具体操作或排查文档 | 偶尔 | admin |
| **用户给了飞书 docx 链接 + 要建/更新** | **E · 文档驱动** | **委托 lark-doc 读 doc → 解析 → 路由到 B 或 C 的批量分支** | 偶尔 | admin / PM / 成员 |

**判断方式**:
- 用户提"建 / 搭 / 加项目 / 邀请成员" → A 或 B
- 用户提**具体任务操作**("更新 / 完成 / 阻塞 / 转给 / 查"+ 任务名)→ C
- 用户提"加字段 / 改字段 / 归档 / 报错" → D
- 用户提**飞书 docx URL** + "根据/按这份文档" → **E**(委托 lark-doc 读 doc 后,再决定走 B 批量加任务 还是 C 批量更新任务)

如果歧义,**默认问一句确认**再路由,不要乱猜。

完整逻辑见 `references/wizard-screens.md` 阶段 C 的判断流程。

## 4. 场景 A · 首次安装(9 阶段 wizard)

完整对话设计(每屏文案、校验、错误处理)在:**[references/wizard-screens.md](references/wizard-screens.md)**

### 4.1 高层骨架

| 阶段 | 内容 | 大约耗时 |
|---|---|---|
| A · 欢迎 + 环境检查 | 检查插件版本、登录态、网络 | 30s |
| C · 路径分流 | 判断首装 vs 已有空间 | 10s |
| D · 规模规划 | 团队人数 + 项目并发数 → 推断架构 | 30s |
| E · 命名 + 业务方向 | 选预设方向(产品研发/客户交付/...) | 30s |
| F · 复杂度选择 | 任务层级深度 + 保密分级 | 30s |
| G · Preview | 显示要创建的清单,等待 confirm | 20s |
| H · 执行 | 跑 `scripts/bootstrap.sh` | 2-3 min |
| I · 验证 | 跑 `scripts/verify-template.sh` + 提示 UI 手动配置 | 10s |
| J · 引导建第一个项目(可跳) | 衔接到 G+ 子流程 | 1 min |

### 4.2 关键决策点(架构推断)

skill 根据"团队规模 × 项目并发"自动推断架构,**不让用户看 B1/B2 这种术语**:

| Q4 团队 × Q5 项目 | 推荐 |
|---|---|
| <5 × 1-3 | **轻量共享**(所有任务在 1 张表) |
| 5-15 × 4-10 | **多任务表(B1)**(每项目独立任务表) |
| 15+ 或 ≥10 个项目 | **多空间分离(B2)** + 警告稍复杂 |

详细决策树见 `references/architecture-decision.md`。

### 4.3 执行阶段调用的命令

```bash
bash $SKILL_ROOT/scripts/bootstrap.sh "项目管理中心·<业务方向>"
```

bootstrap.sh 会自动:建 Base → 建 3 张表 + 字段 → 填速查卡 → 启用高级权限 → 建 3 角色 → 建视图 → 建综合看板模板。

## 5. 场景 B · 加新项目

完整流程:**[references/new-project-flow.md](references/new-project-flow.md)**

### 5.1 G+ 子流程(4 题)

```
G+1 · 项目叫什么名字?
G+2 · 谁是项目经理?(搜索姓名/邮箱选人)
G+3 · 哪些人是成员?(可多选,可跳过)
G+4 · 保密等级?(仅当用户首装时选了保密分级)
```

### 5.2 ⚠️ 触发飞书通知前必须明示

G+ Preview 时**必须**告知用户:
> "下一步会发送飞书通知:[李经理]、[张三]、[李四]、[赵五] 将立即收到加入空间的提示"

让用户选 [1] 确认通知 / [2] 不通知静默加入 / [3] 取消。

### 5.3 执行命令

```bash
bash $SKILL_ROOT/scripts/new-project.sh <workspace-base-token> "<项目名>"
```

## 6. 场景 C · 日常任务操作(skill 高频帮做)

这是 skill **每天**会被触发的场景。用户身份可能是 PM 或成员,意图都是**让 skill 替我去飞书里改/查任务**。

详细操作清单:**[references/task-operations.md](references/task-operations.md)**

### 6.1 成员视角操作

- **更新任务进度**:"我的'实现登录接口'做到 80% 了,顺便填下最近更新"
- **标记完成 + 填交付物**:"X 任务做完了,交付链接是 https://..."
- **标阻塞 + 填风险**:"X 任务卡住了,等后端 Y 接口"
- **改截止日期 / 加协作人**

### 6.2 PM 视角操作

- **跨项目状态查询**:"我所有项目里有哪些 P0 任务卡住了?"
- **重新分配任务**:"把张三的'前端组件'转给李四"
- **批量加任务**:"在 Q3 项目里加 3 个测试任务,负责人都是赵五"
- **调整优先级 / 里程碑归属**

### 6.3 二者都常用

- **查任务详情**:"我的'部署文档'任务现在啥状态"
- **加新任务**:"在 Q3 项目下加一个任务'修复登录 bug',父任务是开发里程碑,负责人张三"
- **补"最近更新"字段**

### 6.4 操作通用流程(给 skill 看)

1. **识别用户身份**:`lark-cli auth whoami` → 拿当前用户 open_id
2. **识别项目上下文**:用户没明确说哪个项目时,看 `~/.pm-skill/registered_bases.json` 默认空间;多项目时让用户指明
3. **找任务**:用户说的是任务名(模糊)→ `+record-search` 拿候选 → 多个匹配时让用户选
4. **改字段**:确认改什么 → preview → `+record-batch-update` 写入
5. **回执**:告诉用户改了哪些字段,值是什么

详细操作模板(每个动作的 prompt 流 + Bash 命令)见 `references/task-operations.md`。

### 6.5 兼带"思维方式引导"

成员问"我每天该看什么" / PM 问"站会怎么开",路由到长篇引导文档:

| 角色 | 读 |
|---|---|
| 项目经理 | `references/pm-daily-guide.md` |
| 项目成员 | `references/member-daily-guide.md` |

但**优先识别是不是具体操作意图**(操作 → task-operations,引导 → daily-guide)。

## 6.5 场景 F · AI 拆解辅助(给个项目目标 → 推荐结构)

用户表达**项目搭建意图但信息不全**(只给项目名 / 大致时间 / 团队规模),不知道怎么拆任务时:

1. **收集 4 个关键信息**:项目类型 / 时长 / 团队规模 / 关键交付物
2. **推荐结构**:基于业务方向预设 + LLM 推理,生成树状拆解(🎯 → 🏁 → 📦 → 📋)
3. **Preview 给用户审改**:支持"改名/拆分/合并/重生成"
4. **批量写入**:跑 `new-project.sh` + 批量 `+record-batch-create` 按层级建任务

完整流程:**[references/decompose-flow.md](references/decompose-flow.md)**

⚠️ **如果用户已有 PRD/工作计划文档**,优先走场景 E(文档驱动),拆解辅助只在"无文档参考"场景兜底。

## 6.7 场景 G · 报告与分析(周报 / 风险预警 / 复盘)

用户要看**周报、风险预警、复盘报告**时:

| 用户诉求关键词 | 调脚本 |
|---|---|
| 周报、本周进展、汇报、本周完成 | `scripts/weekly_report.py` |
| 风险、卡住、阻塞、延期、临期、health | `scripts/risk_check.py` |
| 复盘、回顾、总结报告、retrospective | `scripts/retrospective.py` |

```bash
bash $SKILL_ROOT/scripts/weekly_report.py --base-token <base> --project-name "<项目名>"
bash $SKILL_ROOT/scripts/risk_check.py --base-token <base> --project-name "<项目名>"
bash $SKILL_ROOT/scripts/retrospective.py --base-token <base> --project-name "<项目名>"
```

输出 markdown 直接展示给用户。完整使用指南:**[references/reports-and-analytics.md](references/reports-and-analytics.md)**

## 6.6 场景 E · 文档驱动(委托 lark-doc 读文档后路由到 B 或 C)

用户给飞书 docx 链接(会议纪要 / 周报 / 工作计划 / PRD / OKR)时:

1. **先委托 lark-doc skill** 用 `lark-cli docs +fetch --doc-token <token>` 读取内容
2. **解析**(LLM 推理):识别项目名 / 里程碑 / 任务清单 / 负责人 / 时间 / 状态更新片段
3. **路由**:
   - 文档主要描述**新工作** → 走场景 B 加项目 / 批量加任务
   - 文档主要描述**进展更新**(周报、站会记录等)→ 走场景 C 批量更新任务
4. **必 Preview**:LLM 解析有误识别风险,逐条让用户确认再批量执行

完整对话流和处理细节:**[references/from-doc-flow.md](references/from-doc-flow.md)**

⚠️ **跨 skill 协作原则**:本 skill **不重复实现读 docx 能力**,优先调用 lark-doc skill / `lark-cli docs +fetch` 完成读取。如果 wiki 链接,先 `lark-cli wiki spaces get_node` 解析再 fetch。

## 7. 场景 D · 维护与排错

| 用户诉求 | 读 |
|---|---|
| 加字段 / 改选项 / 归档 / 删除项目 | `references/maintenance-ops.md` |
| 网络/权限/字段冲突等故障 | `references/troubleshooting.md` |
| 健康检查 | 跑 `scripts/verify-template.sh <base-token>` |

## 8. 关键安全约束

skill **写飞书数据**,误操作不可逆。以下原则不可违反:

### 8.1 写操作必须 preview + confirm

任何会创建/修改/删除飞书内容的动作,**先口头列出"将要做什么"**,等用户明确说"是 / 确认 / 继续"才执行。

例外:用户已经在 wizard 内确认过的批量动作(如执行 bootstrap.sh)不需要再逐字段确认,但**整体清单仍要列**。

### 8.2 触发飞书通知前必须明示

任何会让真人收到飞书消息的动作(分享 Base、绑定角色、@ 通知),**用文字明示通知对象 + 通知内容**,让用户决定是否触发。

### 8.3 破坏性操作有冷却期

- **删除项目**:必须先归档(`pm archive-project`),冷却 7 天后才可删除
- **删除字段**:要求用户输 `DELETE` 大写确认
- **撤销整个空间**:wizard 执行中失败时给 `[u] 撤销` 选项,跑 `lark-cli base +base-delete`

### 8.4 dry-run 优先

阶段 G(Preview)必须支持 dry-run,**不真执行,只展示要做的事**。这样用户可以"先试一遍再决定"。

### 8.5 不私自跑实操指令

不要因为用户讨论需求时就开始建 Base。**永远等用户明确说"现在执行"或"继续"才动手**。

## 9. References 索引

| 文件 | 内容 | 何时读 |
|---|---|---|
| [references/wizard-screens.md](references/wizard-screens.md) | 9 阶段 wizard 每屏文案 + 校验 + 错误处理 | 进入场景 A 时 |
| [references/architecture-decision.md](references/architecture-decision.md) | 团队规模 × 项目并发 → 架构选择决策树 | 阶段 D 推断架构时 |
| [references/new-project-flow.md](references/new-project-flow.md) | G+ 子流程 4 题 + Preview + 飞书通知约束 | 场景 B 时 |
| **[references/task-operations.md](references/task-operations.md)** | **日常任务操作清单(更新/完成/阻塞/分配/查询等)+ 后端命令模板** | **场景 C 任务操作时(高频)** |
| **[references/from-doc-flow.md](references/from-doc-flow.md)** | **从飞书 docx(纪要/周报/工作计划/PRD)批量建项目或批量更新任务** | **场景 E 用户给 docx 链接时** |
| **[references/decompose-flow.md](references/decompose-flow.md)** | **AI 拆解辅助:项目目标 → 推荐里程碑/工作包/叶子任务结构** | **场景 F 用户要建项目但没文档参考** |
| **[references/reports-and-analytics.md](references/reports-and-analytics.md)** | **周报 / 风险预警 / 复盘报告 三个命令使用指南** | **场景 G 用户要看报告** |
| [references/pm-daily-guide.md](references/pm-daily-guide.md) | PM 早巡 / 站会 / 周报 / 阻塞处理(思维方式引导) | 场景 C 用户问"每天该看什么" |
| [references/member-daily-guide.md](references/member-daily-guide.md) | 成员每日工作流 / 进展填报格式 | 场景 C 用户问"我该做什么" |
| [references/maintenance-ops.md](references/maintenance-ops.md) | 12 个维护操作(加字段/归档/升级 schema 等) | 场景 D 维护时 |
| [references/troubleshooting.md](references/troubleshooting.md) | 13 类常见故障 + 修复路径 | 场景 D 排错时 |

## 10. Scripts 索引

skill 通过 Bash 调用以下脚本完成实际飞书操作:

| 脚本 | 用途 | 调用时机 |
|---|---|---|
| `scripts/bootstrap.sh <空间名>` | 从 0 建模板/工作区 Base 完整结构 | 场景 A 阶段 H |
| `scripts/new-project.sh <base-token> <项目名>` | 在已有空间内克隆出新项目的任务表 + dashboard | 场景 B 执行 |
| `scripts/verify-template.sh <base-token>` | 校验 Base 与 configs JSON 是否一致 | 场景 A 阶段 I 或场景 D 健康检查 |
| `scripts/_apply_views.py` | 批量建视图(被前两个脚本调用) | 内部 helper |
| `scripts/_apply_dashboard.py` | 批量建 dashboard block(被前两个脚本调用) | 内部 helper |
| `scripts/weekly_report.py <base> <项目名>` | 自动生成周报 markdown | 场景 G · 周报诉求 |
| `scripts/risk_check.py <base> <项目名>` | 风险预警(严重/关注/临期/资源紧张) | 场景 G · 风险诉求 |
| `scripts/retrospective.py <base> <项目名>` | 项目复盘报告 | 场景 G · 项目结束 |
| `scripts/_report_helpers.py` | 三个 report 脚本共用 helper | 内部 |

## 11. configs/ 目录(skill 自带数据)

| 路径 | 内容 |
|---|---|
| `configs/fields/{project,task,cheat_card}_table.json` | 3 张表的字段定义模板 |
| `configs/views/{project,task}_views.json` | 项目主表 4 视图 + 任务表 9 视图配置 |
| `configs/roles/{super_admin,project_manager,project_member}.json` | 3 角色权限规则 |
| `configs/cheat_card_data.json` | 速查卡 34 条规范文案 |
| `configs/dashboard_template.json` | 综合看板 5 block 配置(占位形式) |

修改 configs 等于修改模板;**修改前先思考是否影响已存在用户的空间**(可能造成 schema 漂移)。

## 12. 常见错误速查

仅列高频。详见 `references/troubleshooting.md`。

| 报错 / 现象 | 原因 | 解决 |
|---|---|---|
| `lark-cli: command not found` | 飞书插件未装 | 让用户跑 `npx -y @larksuite/openclaw-lark install` |
| `Permission denied [99991679]` 调用 `+base-create` | 用户飞书权限不足 | 联系飞书管理员开通"多维表格"权限 |
| `Required.search_fields` | record-search 没传 search_fields | 改用 `+record-list` 或加 `--json '{"keyword":"X","search_fields":["Y"]}'` |
| 字段冲突(role_name cannot be empty) | role-update delta 必须含 role_name + role_type | 加这两个字段(用 role-get 拿当前值) |
| Dashboard text block 换行没保留 | API 剥离 `\n` | 用 `\r\n` 代替 `\n` |
| `+dashboard-arrange` 把 text block 顶到顶部 | arrange 默认逻辑 | 先 arrange 图表,后 create text |

## 13. 执行规则总结

1. 路由 → 选场景(A/B/C/D)→ 读对应 reference
2. 写操作前必须 preview + confirm,触发通知必须明示对象
3. 用 `scripts/*.sh` 执行,不要自己拼 lark-cli 命令(已封装好的不重复造)
4. 跑完写操作后默认调 `verify-template.sh` 验收
5. 出错时分级提示(简短 / 展开详情 / 联系支持),给用户选项

> **最后一条提醒**:本 skill 的核心价值不是"写代码",是"引导用户做对的决策"。当用户犹豫或问"我该怎么办",优先给 2-3 个选项让他选,而不是替他决定。
