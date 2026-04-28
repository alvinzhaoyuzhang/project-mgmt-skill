# 飞书项目管理 Skill · project-mgmt

> **一个让团队项目管理"丝滑"起来的 Claude Code / OpenClaw skill**
> 在飞书多维表格内自动搭建项目管理空间,并通过对话引导日常运营、风险预警、自动周报、AI 拆解等能力。

## 这是什么

`project-mgmt` 是一个安装到 [Claude Code](https://claude.com/claude-code) 或 OpenClaw 的 skill。安装后,团队成员通过自然语言对话就能完成:

| 场景 | 效果 |
|---|---|
| 🚀 **从 0 搭建项目管理空间** | 答 5-7 个问题,2-3 分钟自动建好飞书空间(项目主表 / 任务表 / 综合看板 / 3 角色权限 / 速查卡) |
| ➕ **加新项目** | 4 个问题搞定,自动建任务表 + dashboard + 邀请成员触发飞书通知 |
| 📝 **日常任务操作** | 用自然语言改任务进度、标完成、标阻塞、转给他人 |
| 📄 **文档驱动建任务** | 给一份飞书 docx(会议纪要/周报/PRD)→ 自动批量建任务或更新进度 |
| 🤖 **AI 拆解辅助** | 给项目目标 → AI 推荐里程碑/工作包/叶子任务结构,审改后批量入库 |
| 📊 **自动报告** | 一键出周报、风险预警清单、项目复盘报告 |
| 🔧 **维护与排错** | 加字段、改字段选项、归档项目、健康检查、故障诊断 |

## 适合谁用

- **中小团队的项目经理**(1-10 个并行项目)
- **需要在飞书内统一管项目的产品 / 业务 / 行政团队**
- **不想从零搭表、不想手写周报、不想每天巡检风险的人**

## 快速开始

### 前置条件

- ✅ 飞书账号(企业版或国际版)
- ✅ 已安装 [Claude Code](https://claude.com/claude-code) 或 OpenClaw
- ✅ 已安装飞书插件:
  ```bash
  npx -y @larksuite/openclaw-lark install
  ```
- ✅ 飞书账号已与 Claude Code / OpenClaw 连接

### 1. 安装 skill

**方式 A · 从打包文件安装(推荐)**:

```bash
# 下载最新发布的 .skill 文件,然后:
unzip -o project-mgmt.skill -d ~/.claude/skills/
```

**方式 B · 从源码安装**:

```bash
git clone https://github.com/<your-org>/project-mgmt-skill.git
ln -s "$(pwd)/project-mgmt-skill/project-mgmt" ~/.claude/skills/project-mgmt
```

### 2. 第一次使用

在 Claude Code 里直接对话:

```
你:我们公司 6 人产品团队,3 个并行项目,想用飞书做项目管理,帮我搞一套
```

skill 会自动:

1. 检查环境(网络 / 飞书插件 / 登录态)
2. 问 4 个关键问题(团队规模 / 项目数 / 业务方向 / 复杂度)
3. 推荐合适的架构方案(用户友好语言展示,不暴露内部代号)
4. **Preview 给你确认**
5. 执行 `bootstrap.sh` 建空间(2-3 分钟)
6. 验证健康度
7. 引导你建第一个项目

约 5-10 分钟,空间就建好了。

### 3. 后续使用

直接对话即可,例如:

```
"在我的'产品研发'空间加个新项目叫 V2.5 上线,PM 是李经理,组员张三李四"
"帮我把'实现登录接口'这个任务进度改成 60,最近更新写一下"
"我所有项目里这周哪些 P0 任务卡住了?"
"根据这份会议纪要 https://...feishu.cn/docx/abc 在 Q3 项目下加任务"
"给我 Q3 项目这周的周报"
"V2.5 项目结束了,出个复盘报告"
```

## 7 大场景

skill 内部按以下场景路由,但**用户不需要知道这些代号**,直接说人话即可:

| 代号 | 场景 | 何时触发 |
|---|---|---|
| A | 首次安装 | 第一次用 / 还没建空间 |
| B | 加新项目 | 已有空间,加项目 |
| C | 日常任务操作 | 改任务进度/状态/分配/查询 |
| D | 维护排错 | 加字段、归档、健康检查、报错 |
| E | 文档驱动 | 给飞书 docx 链接,要求批量建/改 |
| F | AI 拆解 | 没有文档参考,需要 AI 推荐结构 |
| G | 报告分析 | 周报、风险预警、复盘 |

## 架构概览

skill 在你飞书租户内创建以下结构(默认 B1 多任务表方案):

```
工作区 Base「项目管理中心·<业务方向>」
├── 项目主表        ← 所有项目的登记表(N 行 = N 项目)
├── 任务表·项目A    ← 每项目独立任务表
├── 任务表·项目B    
├── 综合看板·项目A  ← 每项目独立 dashboard(5 个图表 block)
├── 综合看板·项目B  
├── 速查卡          ← 字段使用规范
└── 3 角色 + 高级权限规则
    ├── 超级管理员   ← 全权限
    ├── 项目经理     ← 改自己负责项目的所有任务
    └── 项目成员     ← 改自己被分配的任务
```

任务分级:🎯 目标 → 🏁 里程碑 → 📦 工作包 → 📋 任务(可选 4 级)。

详细架构决策见 `project-mgmt/references/architecture-decision.md`。

## 安全与隐私

- ✅ **所有数据都在你自己的飞书租户内**,本 skill 不上传任何数据到第三方
- ✅ **写操作必须 preview + confirm**:每个会修改飞书的动作都会先列清单等用户确认
- ✅ **触发飞书通知前必须明示**:邀请成员、绑定角色等会发飞书消息的动作,会先列出通知对象
- ✅ **破坏性操作有冷却期**:删除项目要先归档 7 天

## 实测数据(生产环境)

在一个 80 任务 / 4 人团队 / 1 项目的真实工作区跑过:

| 指标 | 数值 |
|---|---|
| skill 内容评测 | 32/32 = **100%** |
| 描述触发评测 | 22/22 = **100%** |
| 与无 skill 基线对比 | **+62%** 准确率提升 |
| 单次首装耗时 | 约 2-3 分钟 |
| 单次加项目耗时 | 约 1 分钟 |

## 包结构

```
project-mgmt/
├── SKILL.md                    主入口(328 行)
├── references/                 详细文档(10 个 ref · 2300+ 行)
│   ├── wizard-screens.md       9 阶段安装向导
│   ├── architecture-decision.md  架构决策树
│   ├── new-project-flow.md     加项目流程
│   ├── task-operations.md      日常任务操作
│   ├── from-doc-flow.md        文档驱动
│   ├── decompose-flow.md       AI 拆解
│   ├── reports-and-analytics.md  报告与分析
│   ├── pm-daily-guide.md       PM 日常引导
│   ├── member-daily-guide.md   成员日常引导
│   ├── maintenance-ops.md      维护操作手册
│   └── troubleshooting.md      故障排查
├── scripts/                    可执行脚本(9 个 · 1400+ 行)
│   ├── bootstrap.sh            首装(场景 A)
│   ├── new-project.sh          加项目(场景 B)
│   ├── verify-template.sh      健康检查
│   ├── weekly_report.py        周报生成
│   ├── risk_check.py           风险预警
│   ├── retrospective.py        复盘报告
│   ├── _apply_views.py         视图建批量 helper
│   ├── _apply_dashboard.py     dashboard 建批量 helper
│   └── _report_helpers.py      报告共用 helper
├── configs/                    静态配置(13 文件)
│   ├── fields/{project,task,cheat_card}_table.json
│   ├── views/{project,task}_views.json
│   ├── roles/{super_admin,project_manager,project_member}.json
│   ├── cheat_card_data.json
│   └── dashboard_template.json
└── evals/                      测试用例
    └── evals.json
```

## 已知限制

| 限制 | 影响 | 缓解 |
|---|---|---|
| **UI 手动配置 2 项必做** | "我的任务"视图加当前用户过滤 / 甘特图按状态着色 | skill 安装完会主动告知,各 30 秒搞定 |
| **飞书 Base 表数量上限** | 免费版 ~20 张表,~10 项目上限 | 提供迁移命令到 B2 多空间方案 |
| **个人版飞书"高级权限"受限** | 3 角色权限隔离弱化 | 推荐企业版 |
| **不支持图片/PDF 转任务** | 只识别飞书原生 docx | 让用户先转 docx |
| **不主动定时跑** | 周报/风险检查需手动触发 | 用户可自配 cron |

## 开发

### 本地修改 + 调试

```bash
git clone https://github.com/<your-org>/project-mgmt-skill.git
cd project-mgmt-skill

# 软链接到 Claude Code skills 目录(改源码自动同步)
ln -s "$(pwd)/project-mgmt" ~/.claude/skills/project-mgmt
```

修改 `project-mgmt/SKILL.md` 或 `references/` 后,重启 Claude Code 会话即生效。

### 测试

skill 内容评测的 5 个 case 在 `project-mgmt/evals/evals.json`,包括 32 条 assertions。

### 打包

```bash
SKILL_CREATOR=~/.claude/claude-plugins-official/plugins/skill-creator/skills/skill-creator
cd $SKILL_CREATOR && python3 -m scripts.package_skill <path/to/project-mgmt>
```

输出 `project-mgmt.skill` 文件可直接分发。

### 内部文档

- `internal-docs-dev/design/` - 架构决策、字段设计、权限规则等内部文档
- `internal-docs-dev/state/CURRENT_STATE.md` - 开发期状态记录(含变更日志)
- `internal-docs-dev/docs/USER_SOP.md` - 完整用户手册(1107 行,供新人 / 支持参考)

## License

[TBD - 建议 MIT 或 Apache 2.0]

## 贡献

欢迎 issue 和 PR。常见贡献方向:

- 新增 references(更多业务方向预设、模板)
- 改进对话流(让 wizard 更"丝滑")
- 加新场景(如 OKR 联动、跨项目甘特图)
- 翻译为英文版

## 致谢

- [Claude Code](https://claude.com/claude-code) · 提供 skill 框架
- [skill-creator](https://github.com/anthropics/skills) · 提供打包标准
- 飞书 [lark-cli](https://github.com/larksuite/openclaw-lark) · 提供 Base 操作能力

## 联系

- GitHub Issues:`<your-repo>/issues`
- 反馈群:扫码加入(后续提供)

---

**🚀 让飞书项目管理变得丝滑 — 从今天开始**
