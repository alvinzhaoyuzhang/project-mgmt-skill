---
name: project-mgmt
description: "在飞书租户内搭建并维护一套结构化项目管理工作区(基于多维表格 Base),并辅助 PM 和成员日常运行项目。三类核心场景:(1)结构搭建类 — 用户明确要建立项目管理工具、搭建任务跟踪系统、管理多个并行项目、追踪 WBS/里程碑/工作包、配置角色权限,或在已有项目管理空间加项目/邀请成员/做维护;(2)日常运行类 — 已有空间的项目经理或成员要更新任务进度、标记任务完成/阻塞/延期、添加任务、查询自己或项目的工作状态、重新分配任务、处理阻塞、写日报周报、做跨项目巡检;(3)文档驱动类 — 用户提供飞书云文档(会议纪要/周报/工作计划/PRD/OKR docx 链接)要求基于文档内容批量建立项目结构、批量加任务、或批量更新任务完成情况。典型触发短语:'帮我搭一套项目管理'、'我的项目管理空间加新项目'、'帮我把这个任务标完成'、'我的 X 任务进度更新到 75%'、'我的任务卡住了帮我标阻塞'、'帮我看下哪些任务延期了'、'把张三的任务转给李四'、'根据这份会议纪要在我的项目管理空间建任务'、'根据周报批量更新任务进度'、'PRD 里列的任务帮我加进去'、'项目管理空间报错怎么办'。特别注意:用户自称'项目经理 / PM / 我管 X 个项目'并询问任务状态(哪些任务卡住/延期/P0 P1 阻塞/负责人负载)时,即使未明说'飞书',也属本 skill 服务范围 — 默认上下文是该 PM 已装本 skill 的项目管理空间。本 skill 还提供:**AI 拆解辅助**(给个项目目标 → 推荐里程碑/工作包/叶子任务结构);**自动周报 / 风险预警 / 复盘报告**(读飞书数据自动出 markdown 报告);**从云文档(docx)批量建任务或更新进度**。本 skill 通过对话引导完成结构搭建、主动帮用户在飞书内修改任务记录、查询项目状态、调整分工。不要为以下场景触发:单纯讨论项目管理理论/方法论(WBS、敏捷、Scrum 等)、非飞书的项目工具(Asana/Notion/Trello/Jira)、与项目管理空间无关的飞书表操作(单纯查表、改单条数据 → 让 lark-base skill 处理)、纯文档操作(转格式/写文档 → 让 lark-doc skill 处理)、飞书项目(MeegoOS / lark project)产品(那是不同产品族)。"
metadata:
  requires:
    bins: ["lark-cli"]
  cliHelp: "lark-cli base --help"
---

# 飞书项目管理工作区 · 安装与维护

> **前置条件**:已装飞书 CLI(`lark-cli`,即 npm 包 `@larksuite/cli`)并完成 `lark-cli auth login`。在 Claude Code 和 OpenClaw 内使用本 skill 都需要此前置(OpenClaw 自带的"飞书官方插件"是另一回事,本 skill 不依赖)。
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
# 1. 飞书 CLI 就位
lark-cli --version  # 期望 ≥ 1.0.9

# 2. 用户已登录(skill 应假设已登录;未登录时引导用户跑 lark-cli auth login)
lark-cli auth status
```

**不要**在 SKILL.md 主流程里 OAuth 用户 — 登录通过 `lark-cli auth login` 由用户自行完成,例外路径见 `references/troubleshooting.md` 第 1 节。

### 2.1 lark-cli 未装时的自动安装引导

如果 `lark-cli --version` 失败(`command not found`),**不要直接报错让用户卡死**——主动引导:

1. **告知用户**:"我注意到飞书 CLI 还没装。我可以帮你装,大约 2-3 分钟,全程不用碰终端。"
2. **优先方式 — 让 AI 自己跑**:用 WebFetch 拉这个官方安装指南并按步执行:
   ```
   https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md
   ```
   或直接用 Bash 跑 `npx @larksuite/cli@latest install`(交互式,默认"创建新应用" + 简体中文)。
3. **关键提醒(必说)**:"装完后**必须重启 AI 工具**(Claude Code / OpenClaw),否则 skill 还是会报 lark-cli: command not found。"
4. **重启后再回来**:让用户重启完后重新触发 skill,你再跑 `lark-cli auth login`(也是 Bash 或让用户跑)完成飞书授权。
5. **完整指引详见** `references/troubleshooting.md` 第 1.1 节。

> 给小白用户的"魔法咒语"(可让他们自己粘贴):**"帮我安装飞书 CLI:https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md"**

### 2.2.1 ID 字符串处理 — 严禁从对话上下文猜,必须从状态文件读

**实测发现的 LLM 行为 bug**(2026-04-29):用户跑完 bootstrap 后,LLM 给用户的 base_token 是 `ElClD9`(6 字符),但真实 token 是 `JMOabxdsFanu9OsO6XEcXWMTnGf`(26 字符)。LLM **虚构 / 截断了长字符串 ID**,导致后续所有操作 NOTEXIST 失败。

**强制规则**(对所有长 ID:base_token / record_id / table_id / dashboard_id / role_id):

1. **状态落盘机制**:`bootstrap.sh` / `new-project.sh` 末尾**自动写**状态文件:
   - `~/.pm-skill/state/last_bootstrap.json` — 最近一次 bootstrap 的所有 ID
   - `~/.pm-skill/state/projects/<项目名>.json` — 每个项目的 record_id / 任务表 id / dashboard_id

2. **任何后续操作需要长 ID 时,必须从状态文件读,不要从对话上下文凭印象引用**:
   ```bash
   # ✅ 对的做法
   BASE_TOKEN=$(cat ~/.pm-skill/state/last_bootstrap.json | python3 -c "import json,sys; print(json.load(sys.stdin)['base_token'])")

   # ❌ 错的做法
   "我记得 token 是 ElClD9..."  # ← LLM 截断/虚构,99% 错
   ```

3. **理由**:LLM 不能可靠转述长随机字符串。这不是 prompt 设计能修的,是 LLM 的本质局限。状态落盘 + cat 文件读是唯一可靠方案。

### 2.2 诊断纪律(出错时必读)

**这是流程契约,不是建议:** 用户报告"X 失败了"时,你**不能**直接跳到"我来手动建 / 等会再试 / 找飞书支持"这种套话。**先诊断再下结论**。

**强制 3 步**:

1. **拿原始报错** — 看 lark-cli 的 stdout JSON,**不要**只看 Python 的 `CalledProcessError`
2. **看 detail.code 飞书错误码**:
   - `800005008` 名称冲突 → 用 list + 决定是 skip 还是 delete-recreate
   - `800008006` internal_error → **大概率 silent success**(资源实际已建,API 谎报失败)
   - 其他码:查 `references/troubleshooting.md` 第 0 节通用 SOP
3. **list 该资源验证实际状态** — 已建?跳过。未建?单步 retry。**不要重试整个 bootstrap.sh**(会创建重复资源)

**反例(实际发生过 4 次)**:OpenClaw 看到 dashboard create 报 internal_error,直接给"建议手动建"。**没先 list 看,导致资源已建出来还在折腾**。下次别这样。

完整 SOP 在 `references/troubleshooting.md` 第 0 节(通用诊断 SOP)和第 8.4/8.5 节(dashboard 相关)。

### 2.3 卡住时不能默认让用户手 UI(违反自动化承诺)

**实测发现的反模式**(2026-04-29):OpenClaw 在 approval 超时 / 脚本失败 / dashboard 出错时,**反复**(多次贴相同消息)建议"你直接在飞书 UI 里手动加"。这违反 skill 的自动化承诺 — 用户付费买 skill 是为了**自动化**,不是 LLM 卡住时把工作甩回用户手上。

**正确处理顺序**(从优到差):

1. **retry 同一命令 1-2 次** — 飞书 internal_error 经常 transient,等 3 秒再试
2. **list 验证实际状态** — 看资源是不是其实已建出来(silent-success)
3. **减小批次** — 27 任务 batch_create 失败?试 5 任务一批
4. **建议用户在本地终端跑同一脚本** — OpenClaw 沙箱 approval 超时 ≠ lark-cli 不可用。本地终端跑 `bash scripts/new-project.sh ...` 不需要 OpenClaw approval
5. **手 UI 是最后兜底,且必须明示这是兜底** — "我已尝试 retry / list / 减批次 / 建议本地跑,都不行,作为最后兜底建议你 UI 手配"

**严禁**:第一次失败就跳到"你 UI 手做"。这是 LLM 偷懒。

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

> ⚠️ **流程契约 · wizard 文案必须 verbatim 展示,严禁压缩/简化/自创/重新编号**
>
> **真实测试中观察到的失败模式**(LLM 把 wizard 文案"自己整理"):
> - ❌ 压缩 5 选项为 4 行 + 丢 ⓘ 提示
> - ❌ 把 `[1] [2] [3]` 改成 `•` 或 `1. 2. 3.`
> - ❌ 自创选项(如把"行政流程/市场活动"换成"内部运营/资产管理")
> - ❌ 用 "Q4 Q5 Q6 Q7" 七题节奏,不用 skill 的 9 阶段编号
> - ❌ 把"空间级开关"等关键术语丢掉
>
> **这一类压缩 = 跳过安全网 = 用户被推错架构 = skill 价值归零。**
>
> 解决方法:**关键 wizard 文案就在下面 §4.4 内联**,你不需要去翻 references。
> 必须 verbatim 复制 `<wizard-screen-q*>` 标签内的内容给用户,不能改一个字。

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

### 4.2 关键决策点(架构推断)— **必须用确定性脚本,严禁 LLM 凭感觉**

🚫 **禁止行为**:看到 Q4 + Q5 答案后,LLM **不能**自己脑补推荐(实测 LLM 经常错推 — 5-15 人 + 10+ 项目应推 B2,LLM 推 B1)。

✅ **必须行为**:跑确定性脚本拿矩阵结果:

```bash
python3 $SKILL_ROOT/scripts/_recommend_arch.py \
  --team "<Q4 答案: <5 / 5-15 / 15+>" \
  --projects "<Q5 答案: 1-3 / 4-10 / 10+>"
```

返回 JSON 含 `arch / arch_name / rationale / warnings`。**直接把 rationale 显示给用户,不要改**。

矩阵详情见 `references/architecture-decision.md`(本脚本就是该矩阵的代码化)。

### 4.3 Q5 = 10+ 安全网 — **强制独立追问**

不管用户是不是批量答的,只要 Q5 答了 "10+",**必须独立问一遍**(在跑 `_recommend_arch.py` 之前):

<wizard-screen-q5-safety-net>

```
你选了「10+ 个项目」 — 我想再确认下:

  这 10+ 个项目是不是都属于**同一个业务方向**?
  (比如都是产品研发,或都是客户交付)

  [1] 是 — 都是同方向,需要在一个空间里统一管
       └ skill 推荐 B2 多空间架构(每项目独立 Base)
  [2] 否 — 跨多个方向,可以拆
       └ skill 建议你**先建当前最主要方向的空间**,
          这次只填那个方向的项目数(可能就 4-10 而已),
          其他方向回主菜单单独建

▸ 选 1-2:
```

</wizard-screen-q5-safety-net>

**逻辑分支**:
- 用户选 [1] → 用 Q5 = "10+" 跑 `_recommend_arch.py`(会推 B2)
- 用户选 [2] → **跳回 Q5 重问**:"那你这次要建的主方向空间,大概放几个项目?",拿到新答案再跑 `_recommend_arch.py`

**这个安全网即使在批量模式下也必须独立问**。理由:它的输出会改变后续走 B1 还是 B2,影响整套 base 设计。

### 4.4 wizard 关键屏 verbatim 文案(LLM 必须原样复制)

**重要规则**:进入对应阶段时,从下面找到 `<wizard-screen-q*>` 标签,**把标签内的代码块原样复制给用户**。不能压缩、不能简化、不能自创选项、不能改编号格式。

#### Q4 团队规模(阶段 D 屏 1)

<wizard-screen-q4>

```
👥  规模规划 (1/2)

你的团队大概多少人?(指要用这个空间的人,不是公司总人数)

   [1] <5 人(小团队 / 个人玩耍)
   [2] 5-15 人(主流)
   [3] 15+ 人(中型团队)

ⓘ 人数指你计划用这个空间的人,不一定是公司总人数

▸ 选 1-3:
```

</wizard-screen-q4>

答案映射:[1]→`<5`,[2]→`5-15`,[3]→`15+`(传给 `_recommend_arch.py --team`)

#### Q5 项目并发(阶段 D 屏 2) — **关键消歧义点,文案严禁压缩**

<wizard-screen-q5>

```
📊  规模规划 (2/2)

**这一个空间**里大概要装多少个项目?

   [1] 1-3 个 — 单条线 / 一个产品 / 一组紧密相关的事
   [2] 4-10 个(主流) — 多条线并行,同一业务方向
   [3] 10+ 个 — 项目密集(通常说明该按业务方向拆多个空间)

ⓘ 关键:这里只算**这一个空间**会装的项目数,**不是你团队总共管多少**。
   - 你可能管 20 个项目,但分散在产品研发 / 客户交付 / 行政事务等不同方向
   - 建议**每个业务方向单独建一个空间**,回主菜单可继续建第二、三个空间
   - 例:产品研发 8 个项目 → 一个空间;客户交付 5 个 → 另一个空间

ⓘ "项目" = 一条独立工作流(一个产品 / 一个客户 / 一次交付),不是单个任务

▸ 选 1-3:
```

</wizard-screen-q5>

答案映射:[1]→`1-3`,[2]→`4-10`,[3]→`10+`(传给 `_recommend_arch.py --projects`)

**[3] 触发 §4.3 安全网,必须独立追问**。

#### Q7 空间名确认(阶段 E 屏 3)— 必问,不能跳过

<wizard-screen-q7>

```
✏️  空间命名

我准备给你的空间起名:**项目管理中心·<Q6 选的业务方向>**
(例:项目管理中心·产品研发)

  [Enter / 1] 用这个默认名
  [2] 自定义命名(例:朗晖项目管理 / Q3冲刺空间)

▸ 选 1-2 (默认 [1]):
```

</wizard-screen-q7>

**重要**:Q7 必问,**不能跳到 Q8 / Preview**。bootstrap.sh 的第一个参数是空间名,没传会用默认 `项目管理中心(通用模板)` — 这不是用户想要的体验。

如果用户选 [2] 自定义,follow-up 问:

```
✏️  起一个名字

为这个空间起个简短描述,作为飞书内识别标签。
例:DataOps · 数据团队 · 营销联盟

⚠️ 不超过 20 字,不能用 / \ : * ? " | 等特殊字符

▸ 输入名字:
```

#### Q6 业务方向(阶段 E 屏 1)

<wizard-screen-q6>

```
🎯  业务方向

这个空间用来管什么类型的项目?
我会根据你的选择,自动配好"模块标签"等预设字段。

  [1] 产品研发  · 软件/硬件/AI 产品开发
  [2] 客户交付  · 项目制咨询 / 外包 / 服务
  [3] 行政流程  · 内部流程 / 合规 / HR 项目
  [4] 市场活动  · 营销 / 品牌 / 活动
  [5] 自定义    · 自己起名

ⓘ 选错也没关系,后续可改
ⓘ 团队同时做多个方向?**建议每个方向建一个独立空间**(数据更清晰、
   权限更易管)。先建最主要的那个,其他方向之后回主菜单选
   「[2] 创建一个新空间」继续建即可。

▸ 选 1-5:
```

</wizard-screen-q6>

**严禁**:把 5 选项改成"产品研发/客户交付/内部运营/资产管理/其他混合型"等自创版本。**严格按上面 [1]-[5] 给用户**。

#### Q8 任务层级(阶段 F 屏 1)

<wizard-screen-q8>

```
🎯  任务层级深度

  [1] 极简 · 一个项目 30 任务以下
       └ 2 级层次(目标 + 任务)
  [2] 中等 · 一个项目 30-100 任务
       └ 3 级层次(🎯 → 🏁 → 📋)
  [3] 完整 · 一个项目 100+ 个任务
       └ 4 级层次(🎯 → 🏁 → 📦 → 📋)

ⓘ 选错可后续切换;但 [1] 转 [3] 要重新拆任务

▸ 选 1-3 (推荐 [3]):
```

</wizard-screen-q8>

#### Q9 保密分级(阶段 F 屏 2)

<wizard-screen-q9>

```
🔒  保密分级 (2/2)

你的团队需要按项目设置不同的保密等级吗?(空间级开关)

  [1] 不需要 — 所有项目统一可见,简化权限
       └ 项目主表不会建"保密等级"字段
       └ 所有成员都能看所有项目

  [2] 需要 — 启用 L1-L4 四档分级
       └ 项目主表加"保密等级"字段(L1 公开 / L2 常规 / L3 敏感 / L4 机密)
       └ 加项目时再单独问"这个项目分到哪一级"
       └ 不同等级的项目对成员的可见性不同

ⓘ 这只是**空间级开关** — 决定整套分级机制是否启用。
   具体每个项目分到哪一级,后面 G+4 加项目时才问。
ⓘ 选 [1] 后续不能直接升 [2](等于重置权限)

▸ 选 1-2 (默认 [1]):
```

</wizard-screen-q9>

**Q9 = [2] 后须告知**:"加项目时还会单独问每个项目的等级"。

---

(其他屏幕文案 — Q4/Q7 空间名 / Preview / 阶段 G+ 加项目流程 等 — 在 `references/wizard-screens.md` 完整,**进入对应阶段时去那里找,同样 verbatim 复制**。)

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

### 6.0 引导式陪跑 — 不只是"问 → 答工具"

⚠️ **重要的设计原则**:很多用户操作意图描述是**模糊的**(如"X 卡住了" / "改下优先级" / "看下项目")。skill **必须主动追问 + 分析连锁影响**,而不是闷头改字段。

| 用户描述模糊度 | skill 应做 | 参考文档 |
|---|---|---|
| **"看下项目状况"等全景诉求** | 不反问,直接 4 层 brief | `references/pm-onboarding.md` |
| **"X 卡住了"等动作意图** | 标阻塞 + 引导式 4-5 问(在等什么/多久/影响下游/要不要 @) | `task-operations.md` Op-M3 |
| **"X 改 P0"等优先级调整** | 拉当前 P0 列表 + 算挤压风险 + 让用户选 1-3 | `task-operations.md` Op-PM4 |
| **"加新任务"等结构调整** | 4 问:父任务归属 / 负责人容量 / 挤压谁 / 里程碑容量 | `task-operations.md` Op-PM3 + `task-cascade-effects.md` |
| **"项目延期一周"等全局重排** | 拉甘特 → 问"延谁" → preview 批量改清单 → 留痕 | `task-operations.md` Op-PM8 + `task-cascade-effects.md` 类型 1 |

**详细方法论**(改之前看什么 / 怎么追问 / 何时给建议):**[references/task-cascade-effects.md](references/task-cascade-effects.md)**

### 6.1 成员视角操作

- **更新任务进度**:"我的'实现登录接口'做到 80% 了,顺便填下最近更新"
- **标记完成 + 填交付物**:"X 任务做完了,交付链接是 https://..."
- **标阻塞 + 填风险**(引导式 5 问 — 见 `task-operations.md` Op-M3)
- **改截止日期 / 加协作人**

### 6.2 PM 视角操作

- **跨项目状态查询**:"我所有项目里有哪些 P0 任务卡住了?"
- **重新分配任务**:"把张三的'前端组件'转给李四"
- **批量加任务**(引导式 — 先问连锁,见 Op-PM3)
- **调整优先级 / 里程碑归属**(提到 P0 必问挤压,见 Op-PM4)
- **项目状况全景询问**(主动 4 层 brief,见 Op-PM7 + pm-onboarding.md)
- **项目延期重排**(全局影响版,见 Op-PM8)

### 6.3 二者都常用

- **查任务详情**:"我的'部署文档'任务现在啥状态"
- **加新任务**:"在 Q3 项目下加一个任务'修复登录 bug',父任务是开发里程碑,负责人张三"
- **补"最近更新"字段**

### 6.4 操作通用流程(给 skill 看)

1. **识别用户身份**:`lark-cli auth status` → 解析 JSON 里的 `userOpenId`
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

## 6.8 场景 H · 主动监控(7×24 项目守望者)

> **这是 v1.2 的杀手级能力**。利用 OpenClaw 心跳/cron 让 skill 在用户离开对话时仍持续看着项目。

5 个推荐定时监控,把 skill 从"问 → 答工具"升级为"持续陪伴":

| 监控 | 节奏 | 推送对象 | procedure |
|---|---|---|---|
| 🌅 **每日项目晨检** | 工作日 9:00 | 超级管理员 | `references/monitors/daily-morning-check.md` |
| 📊 **周报自动生成** | 周五 10:00 | 超级管理员 | `references/monitors/weekly-report.md` |
| ⚠️ **阻塞实时预警** | 每小时 | 项目经理(分项目) | `references/monitors/blocker-alert.md` |
| 🎯 **里程碑到期预警** | 每天 9:00 | 项目经理 | `references/monitors/milestone-warning.md` |
| 📋 **月度复盘提醒** | 每月 1 号 10:00 | 超级管理员 | `references/monitors/monthly-retro-prompt.md` |

**关键约束**:监控 procedure **必须用 OpenClaw native 飞书 tool**(`feishu_bitable_app_table_record` 等),**不能调 lark-cli / Python 脚本**(因为 isolated cron session 里 exec 命令需 approval,跑不了)。

**状态读取**:每个 procedure 从 `~/.pm-skill/state/last_bootstrap.json` + `state/projects/*.json` 读 base_token / table_ids 等(v1.1.3 已落盘)。

### 6.8.1 何时主动 prompt 用户考虑设置监控

LLM 必须在以下时机**主动**提示用户考虑启用监控(否则用户记不得这个能力):

- **bootstrap.sh 完成后**(场景 A 阶段 J):提示设置 [1] 晨检 + [2] 周报
- **加完第一个项目后**(场景 B 完成屏):提示 [3] 阻塞预警 + [4] 里程碑预警
- **用户主动问"还有什么我没用的功能"**:列 5 个监控

**严禁**在以下时机骚扰式 prompt:每次任务操作 / troubleshooting / 跑完手动报告后。

### 6.8.2 用户怎么设置监控

复制粘贴对话指令模板给 OpenClaw — 完整 5 个模板见 `references/proactive-monitoring.md`。

例(每日晨检):
```
帮我设置每个工作日 9:00 跑项目晨检,按
~/.openclaw/workspace/skills/project-mgmt/references/monitors/daily-morning-check.md
执行,有发现就发飞书消息给我。

定时任务名:项目晨检
schedule:cron "0 9 * * 1-5" (Asia/Shanghai)
session 模式:isolated
通知方式:announce(飞书 IM 推送)
```

完整指南:**[references/proactive-monitoring.md](references/proactive-monitoring.md)**

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
| [references/feishu-permission-limits.md](references/feishu-permission-limits.md) | 飞书角色权限规则限制速查表(哪些字段类型不能用在 filter) | 改 role JSON / 设计权限规则前 |
| **[references/pm-onboarding.md](references/pm-onboarding.md)** | **PM "我刚回项目 / 看下状况" 时的 4 层主动 brief** | **场景 C · Op-PM7 项目状况全景询问时** |
| **[references/task-cascade-effects.md](references/task-cascade-effects.md)** | **任务变化的下游影响分析方法论(延期/优先级/加任务/标阻塞)** | **场景 C 改任务关键属性前必读** |
| **[references/proactive-monitoring.md](references/proactive-monitoring.md)** | **5 个定时监控模板入口(晨检/周报/阻塞/里程碑/复盘)** | **场景 H · 主动监控设置时** |
| references/monitors/*.md | 5 个 monitor procedure(给 OpenClaw isolated cron session 看的执行步骤) | 定时任务自动触发时 |

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
| `scripts/_validate_role.py <role_json>` | 角色配置预校验,拦截 lookup/formula/link 字段误用在 filter | 在 bootstrap.sh 执行 role-create 前自动调用 |
| `scripts/_sync_secrecy.py --base-token X --project-name Y` | cascade 项目「保密等级」到该项目所有任务的「任务保密等级」 | 用户改了项目保密等级后(场景 D · Op-PM6) |
| `scripts/_recommend_arch.py --team <size> --projects <count>` | 确定性架构推荐,把 B1/B2 决策从 LLM 手里收回(矩阵化) | wizard 阶段 D 屏 3 推荐架构前**强制调用**,详见 §4.2 |
| `scripts/_apply_sample_project.py --base-token X` | 写入示例项目数据(1 项目 + 25 任务,涵盖各种状态/优先级/日期分布)让 dashboard 立刻可见 | bootstrap.sh 末尾默认调用,可加 `--no-sample` 跳过 |

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
| `lark-cli: command not found` | 飞书 CLI 未装 / 装完未重启 | **主动 offer 帮装**:"帮我安装飞书 CLI:https://open.feishu.cn/document/no_class/mcp-archive/feishu-cli-installation-guide.md" → Bash 跑 `npx @larksuite/cli@latest install` → 让用户**重启 AI 工具** → `lark-cli auth login`。详见 §2.1 + troubleshooting.md §1.1 |
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
