<callout emoji="🎯" background-color="light-blue">
本文档是「项目管理中心」多维表格模板的**完整使用 SOP**,覆盖新建项目/项目管理/字段规范/权限体系/视图用法。任何人在第一次接手项目管理工作前,**请先通读本文 10 分钟**。
</callout>

## 一、双 Base 体系 —— 模板 vs 工作区

本体系由两个相互独立的飞书多维表格组成,职责明确分离:

<lark-table column-widths="150,280,280" header-row="true">
<lark-tr>
<lark-td>

**角色**

</lark-td>
<lark-td>

**项目管理中心(通用模板)**

</lark-td>
<lark-td>

**项目管理中心·XXX 工作区**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

定位

</lark-td>
<lark-td>

纯净的结构模板,**不存真实项目**

</lark-td>
<lark-td>

某个业务方向的实际项目集合

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

典型用例

</lark-td>
<lark-td>

- 新团队拿去克隆
- 定期迭代字段/视图定义
- 发布"标准版"供外部使用

</lark-td>
<lark-td>

- AI 产品开发工作区
- 行政合规工作区
- 市场活动工作区 ...

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

谁能改

</lark-td>
<lark-td>

仅超级管理员(目前是张诏瑜)

</lark-td>
<lark-td>

超管 + 对应项目经理

</lark-td>
</lark-tr>
</lark-table>

<callout emoji="⚠️" background-color="light-yellow">
**重要原则**:**不要在模板里填真实项目数据**。新项目总是克隆一个工作区,然后在工作区里新建项目记录。
</callout>

---

## 二、新建项目的 3 种方式

根据项目性质选择合适的入口:

### 方式 A · 加入现有工作区(推荐,最常用)

当你已经有对应方向的工作区(如"AI 产品开发"工作区),新项目直接加到该工作区里:

1. 打开对应工作区 Base
2. 切到「项目主表」→ 找到「**新建项目(卡片引导)**」表单视图
3. 按表单提示逐项填写(字段有引导说明)
4. 提交后自动创建项目记录
5. 回到项目主表,找到新项目,点击进入详情页,开始拆任务

### 方式 B · 为新业务方向新建工作区

当项目不属于任何现有工作区(例如第一次做"客户对账"方向):

1. 打开**通用模板** Base
2. 菜单 → 更多 → 复制副本 → 命名为 `项目管理中心·<业务方向>`
3. 在新 Base 里启用高级权限 + 配置角色(让超管 + 该方向 PM 知会)
4. 进入方式 A

### 方式 C · 极简/临时项目

仅在**跑一次就归档**的一次性工作中使用:
- 直接在「项目主表」点「+ 新增记录」逐字段填
- 不走表单引导(跳过保密等级等细节确认)

---

## 三、字段规范

### 项目主表 · 字段用法

<lark-table column-widths="140,100,370" header-row="true">
<lark-tr>
<lark-td>

**字段**

</lark-td>
<lark-td>

**类型**

</lark-td>
<lark-td>

**填写规范**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

项目名称

</lark-td>
<lark-td>

文本(主字段)

</lark-td>
<lark-td>

业务可识别的完整名称,避免缩写。例:「清产核资产品 MVP 版开发工作」

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

项目编号

</lark-td>
<lark-td>

文本

</lark-td>
<lark-td>

格式 `P<年份>-<3 位序号>`,例 `P2026-001`。按工作区内启动时序递增

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

项目状态

</lark-td>
<lark-td>

单选

</lark-td>
<lark-td>

筹备 → 进行中 → (暂停 ↔ 进行中) → 已完成 → 已归档

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

项目经理

</lark-td>
<lark-td>

人员(单选)

</lark-td>
<lark-td>

**每个项目只能有 1 位**。作为"项目经理角色"的权限触发依据

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

项目成员

</lark-td>
<lark-td>

人员(多选)

</lark-td>
<lark-td>

**必须包含项目经理本人**。作为"项目成员角色"的可见范围依据

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

项目目标

</lark-td>
<lark-td>

长文本

</lark-td>
<lark-td>

1-3 条,**可度量可验收**。避免"提高用户体验"这类模糊表述

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

保密等级

</lark-td>
<lark-td>

单选

</lark-td>
<lark-td>

见下文"四、权限体系"章节的详细定义。默认 L2 常规

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

开始日期 / 计划结束日期

</lark-td>
<lark-td>

日期

</lark-td>
<lark-td>

计划区间,不是实际区间。实际延期不改这里(延期信息看任务)

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

优先级

</lark-td>
<lark-td>

单选

</lark-td>
<lark-td>

P0 紧急(公司级不可替代)/ P1 高(本季 OKR)/ P2 中(一般业务)/ P3 低(长尾)

</lark-td>
</lark-tr>
</lark-table>

### 任务表 · 字段用法

<lark-table column-widths="140,100,370" header-row="true">
<lark-tr>
<lark-td>

**字段**

</lark-td>
<lark-td>

**类型**

</lark-td>
<lark-td>

**填写规范**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

任务编号

</lark-td>
<lark-td>

自动编号

</lark-td>
<lark-td>

T-0001 系统自动生成,不用手填

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

WBS 编号

</lark-td>
<lark-td>

文本

</lark-td>
<lark-td>

格式 `1 / 1.1 / 1.1.2 / 1.1.2.3`。**手工维护**,按父子关系顺序编号。主要用于排序和展示层级

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

任务名称

</lark-td>
<lark-td>

文本

</lark-td>
<lark-td>

一句话描述"做什么"。避免只写"开发 XX",要写"开发 XX(产出 YY)"

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

所属项目

</lark-td>
<lark-td>

关联

</lark-td>
<lark-td>

**必填**。指向项目主表

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

任务级别

</lark-td>
<lark-td>

单选

</lark-td>
<lark-td>

🎯 目标 / 🏁 里程碑 / 📦 一级工作 / 📋 二级工作 / 📌 三级工作。见下节"五、任务拆解标准"

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

父任务

</lark-td>
<lark-td>

关联自身

</lark-td>
<lark-td>

**除目标外都必填**。实现树状结构,是"全部任务(树状浏览)"视图能工作的前提

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

负责人

</lark-td>
<lark-td>

人员(单选)

</lark-td>
<lark-td>

**叶子任务必填唯一负责人**。负责人 = 可问责人,不是"参与者"

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

协作人

</lark-td>
<lark-td>

人员(多选)

</lark-td>
<lark-td>

参与本任务的其他成员。用于权限系统:协作人可见且可编辑本任务

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

状态 / 进度

</lark-td>
<lark-td>

单选 / 数字

</lark-td>
<lark-td>

未开始 → 进行中 → 已完成 | 阻塞/延期/已取消。进度 0-100,已完成必须 100

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

交付物

</lark-td>
<lark-td>

文本

</lark-td>
<lark-td>

可验收的产出。例:"GET /api/v2/xxx 接口 + 单测 + postman 集合"。写"完成 XX"不合格

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

风险与阻塞

</lark-td>
<lark-td>

长文本

</lark-td>
<lark-td>

正在发生的问题,不是假设的风险。例:"依赖数据中台 API,对方排期未确认"

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

最近更新

</lark-td>
<lark-td>

长文本

</lark-td>
<lark-td>

成员**每次动状态**时顺手更新。格式:`YYYY-MM-DD 做了X,下一步Y,需要Z支持`

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

任务保密等级

</lark-td>
<lark-td>

Select(skill 同步)

</lark-td>
<lark-td>

从所属项目"保密等级"由 skill 自动同步(创建任务/改所属项目时),用于权限过滤。不用手填(改了下次 cascade 会被覆盖)

</lark-td>
</lark-tr>
</lark-table>

---

## 四、任务拆解标准

### 五级层级定义

<callout emoji="🎯" background-color="light-green">
**核心原则**:层级不是越多越好。一般项目最多拆到 **📋 二级工作**,复杂项目才用 **📌 三级工作**。
</callout>

<lark-table column-widths="120,120,130,150,100" header-row="true">
<lark-tr>
<lark-td>

**级别**

</lark-td>
<lark-td>

**本质**

</lark-td>
<lark-td>

**数量建议**

</lark-td>
<lark-td>

**示例**

</lark-td>
<lark-td>

**是否分配责任人**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

🎯 目标

</lark-td>
<lark-td>

项目最终交付成果

</lark-td>
<lark-td>

1-3 个

</lark-td>
<lark-td>

"完成 MVP 验收交付"

</lark-td>
<lark-td>

项目经理即可

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

🏁 里程碑

</lark-td>
<lark-td>

关键阶段 / Gate / Sprint

</lark-td>
<lark-td>

3-7 个

</lark-td>
<lark-td>

"Sprint 1 开发冲刺"

</lark-td>
<lark-td>

该阶段负责人

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

📦 一级工作

</lark-td>
<lark-td>

里程碑下的工作包(**按统一维度**切分:模块/角色/交付阶段三选一)

</lark-td>
<lark-td>

每里程碑 3-5 个

</lark-td>
<lark-td>

"底层架构"、"对外前端"

</lark-td>
<lark-td>

工作包负责人

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

📋 二级工作

</lark-td>
<lark-td>

**叶子任务**,可估算可分配

</lark-td>
<lark-td>

每一级下 3-10 个

</lark-td>
<lark-td>

"OpenClaw 部署"

</lark-td>
<lark-td>

**必须有唯一负责人**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

📌 三级工作

</lark-td>
<lark-td>

仅复杂场景

</lark-td>
<lark-td>

尽量不用

</lark-td>
<lark-td>

(历史版本归档的子项)

</lark-td>
<lark-td>

必须

</lark-td>
</lark-tr>
</lark-table>

### 叶子任务(负责人唯一的)的三个硬标准

一个任务可以被登记为"二级工作"(即叶子任务),**必须同时满足**:

1. **可估算** — 从启动到完成能在 1-5 天完成,超过就拆
2. **可分配** — 能指定唯一负责人,模糊不清就拆
3. **可度量** — 有明确的"交付物"字段,能一眼看出做没做完

<callout emoji="⚠️" background-color="light-red">
**反模式**:
- 把"项目全部完成"写成一个二级工作 → 这是 🎯 目标
- 一个二级工作写了 3 个负责人 → 拆分成 3 个独立的二级工作
- 交付物写"完成开发" → 不够具体,应写"提交代码+合并到主分支+通过 CI"
</callout>

### 一级工作(📦) vs 模块(🏷️)—— 两个分类系统的分工

新手常把这两者搞混。简单说:**一级工作是"层级归属",模块是"内容标签"**。

<lark-table column-widths="130,280,280" header-row="true">
<lark-tr>
<lark-td>

**维度**

</lark-td>
<lark-td>

**📦 一级工作**(层级)

</lark-td>
<lark-td>

**🏷️ 模块**(字段)

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

回答什么问题

</lark-td>
<lark-td>

"这归谁管,在哪个阶段做?"

</lark-td>
<lark-td>

"这涉及哪些业务/技术模块?"

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

类型

</lark-td>
<lark-td>

结构性(父子层级)

</lark-td>
<lark-td>

描述性(多选标签)

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

唯一性

</lark-td>
<lark-td>

一个任务只能属于一个 📦

</lark-td>
<lark-td>

一个任务可能涉及多个模块

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

示例

</lark-td>
<lark-td>

底层架构 / 具体功能实现 / Gate

</lark-td>
<lark-td>

s03 对账 / s06 账务 / 编排面板

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

视图用途

</lark-td>
<lark-td>

进度聚合、里程碑汇报

</lark-td>
<lark-td>

跨里程碑查技术线、跨项目看技术栈

</lark-td>
</lark-tr>
</lark-table>

**实际配合**:`s03 对账引擎重构` 这条任务
- 📦 一级工作 = `具体功能实现`(属于 Sprint 1 下的功能实现工作包)
- 🏷️ 模块 = `s03 对账`(涉及 s03 这个业务模块)

两者**不冲突不冗余**:项目经理看层级(一级工作),技术 Owner 看切面(模块)。

---

## 五、权限体系

### 4 级保密等级

<lark-table column-widths="100,180,220,200" header-row="true">
<lark-tr>
<lark-td>

**等级**

</lark-td>
<lark-td>

**典型场景**

</lark-td>
<lark-td>

**可见性**

</lark-td>
<lark-td>

**可编辑性**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**L1 公开**

</lark-td>
<lark-td>

OKR、市场活动、对外文档

</lark-td>
<lark-td>

**全员可见**(含非成员)

</lark-td>
<lark-td>

仅成员改自己负责的

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**L2 常规**(默认)

</lark-td>
<lark-td>

大部分产品/开发项目

</lark-td>
<lark-td>

项目成员**可见全部任务**

</lark-td>
<lark-td>

PM 改全部,成员改自己的

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**L3 敏感**

</lark-td>
<lark-td>

涉客户/财务/合同

</lark-td>
<lark-td>

成员**仅见分配给自己**的任务

</lark-td>
<lark-td>

同上

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**L4 机密**

</lark-td>
<lark-td>

战略 / M&A / 合规

</lark-td>
<lark-td>

白名单制,单独授权

</lark-td>
<lark-td>

仅 PM + 授权人

</lark-td>
</lark-tr>
</lark-table>

### 3 个角色

<lark-table column-widths="120,280,200" header-row="true">
<lark-tr>
<lark-td>

**角色**

</lark-td>
<lark-td>

**权限范围**

</lark-td>
<lark-td>

**默认绑定**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

超级管理员

</lark-td>
<lark-td>

所有表 full_access,可管理所有项目和角色配置

</lark-td>
<lark-td>

Base owner(张诏瑜)

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

项目经理

</lark-td>
<lark-td>

可编辑"项目经理=自己"的项目,及其下所有任务

</lark-td>
<lark-td>

按项目动态绑定

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

项目成员

</lark-td>
<lark-td>

可读"项目成员包含自己"的项目 + 按保密等级读任务;仅可编辑"负责人=我 OR 协作人包含我"的任务

</lark-td>
<lark-td>

按项目成员字段动态绑定

</lark-td>
</lark-tr>
</lark-table>

<callout emoji="🔐" background-color="light-purple">
**关键**(v1.1 更新):权限系统基于「**任务保密等级** select 字段」驱动,该字段由 skill 在创建任务/改所属项目时**自动从项目主表「保密等级」同步**(原计划用 lookup 字段,但飞书禁止 lookup 用于角色 filter,改为 select + sync 方案)。新建项目时只要正确设置项目「保密等级」,任务字段同步后权限自动生效。
</callout>

### 表的编辑策略(表级权限矩阵)

<lark-table column-widths="160,150,180,170" header-row="true">
<lark-tr>
<lark-td>

**表**

</lark-td>
<lark-td>

**超级管理员**

</lark-td>
<lark-td>

**项目经理**

</lark-td>
<lark-td>

**项目成员**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**项目主表**

</lark-td>
<lark-td>

全权(增删改查)

</lark-td>
<lark-td>

可编辑"项目经理=自己"的项目;可见全部

</lark-td>
<lark-td>

只读,仅可见"项目成员包含自己"的项目

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**任务表**

</lark-td>
<lark-td>

全权

</lark-td>
<lark-td>

编辑全部任务;可增删记录

</lark-td>
<lark-td>

仅编辑"负责人=我 OR 协作人包含我"的任务;按保密等级读其他

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

**速查卡·字段分级权限**

</lark-td>
<lark-td>

全权(规范内容维护)

</lark-td>
<lark-td>

只读

</lark-td>
<lark-td>

只读

</lark-td>
</lark-tr>
</lark-table>

<callout emoji="📘" background-color="pale-gray">
**为什么速查卡锁定只读**:承载项目管理规范(分级标准、权限定义、命名规范等),属于"沉淀性参考",由超管统一把关更新。成员/PM 可以看,不能随意改,避免规范被稀释。
</callout>

---

## 六、视图使用指南

### 任务表 · 核心视图

<lark-table column-widths="200,430" header-row="true">
<lark-tr>
<lark-td>

**视图**

</lark-td>
<lark-td>

**用途**

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

全部任务(树状浏览)

</lark-td>
<lark-td>

**主视图**。按所属项目分组,按 WBS 编号升序,能看到完整的目标→里程碑→一级→二级层级

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

我的任务

</lark-td>
<lark-td>

每日晨会/个人跟进。**需在 UI 里添加「当前用户」过滤**(一次设置后保存)

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

里程碑看板

</lark-td>
<lark-td>

对外/对上汇报用。仅展示 🎯 目标 + 🏁 里程碑 两级

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

阻塞与延期

</lark-td>
<lark-td>

项目经理每日关注。自动筛选状态=阻塞/延期的任务

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

甘特图

</lark-td>
<lark-td>

时间线规划 + 关键路径识别

</lark-td>
</lark-tr>
<lark-tr>
<lark-td>

状态看板

</lark-td>
<lark-td>

按状态分组的卡片视图,拖拽推进进度

</lark-td>
</lark-tr>
</lark-table>

---

## 六点五、首次使用 · UI 手动配置清单

<callout emoji="⚠️" background-color="light-yellow">
以下配置 **CLI 无法完成**,必须在飞书 Web/App **UI 里手动点一次**,保存后对所有成员永久生效。
</callout>

### 🔧 必做(影响视图能否正常工作)

| # | 视图 | 操作 | 目的 |
|---|---|---|---|
| 1 | **我的任务**(任务表) | 筛选 → 添加条件:`负责人` 包含 `当前用户` **或** `协作人` 包含 `当前用户`(注意改成"或"关系) | 让视图显示每人各自的任务,不然所有人看到全量 |
| 2 | **我负责的项目**(项目主表) | 筛选 → 添加条件:`项目经理` 包含 `当前用户` | 让项目经理看到只自己负责的项目 |

### 🎨 建议做(体验优化)

| # | 视图 | 操作 | 目的 |
|---|---|---|---|
| 3 | 甘特图 | 工具栏 → 条形图样式 → 按字段着色 → 选「状态」 → 保存 | 不同状态显示不同颜色(灰=未开始,蓝=进行中,绿=已完成,红=阻塞) |
| 4 | 全部任务(树状浏览) | 鼠标拖"任务编号"列的右边界向左 | 主字段被系统强制为首列,UI 里拖窄省空间 |
| 5 | 甘特图 | 同上,拖窄任务编号 + WBS 编号列 | 左侧面板压缩,日期区域获得更多空间 |

### 💡 重要说明

**为什么 CLI 无法做 #1/#2**:飞书 Base 的"当前用户"是一种**动态占位符**,CLI 只能传静态值(具体 open_id);硬编码某人的 open_id 会让视图变成"某人专属",失去通用性。UI 里添加的动态筛选会自动解析为当前登录用户。

**一次配置,永久生效**:以上步骤只需做一次,保存后对所有成员都生效。新成员加入时无需重复。

---

## 七、日常维护清单

### 成员每日(5 分钟)

- [ ] 打开「我的任务」视图
- [ ] 更新昨日完成任务状态为"已完成",进度设为 100
- [ ] 今日要做的任务状态设为"进行中"
- [ ] 遇到阻塞的任务,状态改"阻塞",填写「风险与阻塞」字段
- [ ] 所有变更的任务,填写「最近更新」(一句话即可)

### 项目经理每周(15 分钟)

- [ ] 打开「阻塞与延期」视图,逐条处理或升级
- [ ] 打开「里程碑看板」,确认里程碑进度,不达标的调整计划
- [ ] 打开甘特图,评估是否需要调整时间线
- [ ] 每月最后一周评估是否需要调整项目状态(进行中 → 暂停/已完成)

### 超管每月(30 分钟)

- [ ] 检查「项目主表」所有项目状态是否合理
- [ ] 对已完成的项目执行"已归档",释放成员精力
- [ ] 评估是否需要调整保密等级定义或权限规则
- [ ] 根据新业务方向决定是否新建工作区

---

## 八、常见问题

<callout emoji="❓" background-color="pale-gray">
**Q1: 我在「我的任务」里看不到我被指派的任务?**

A: 检查视图过滤条件。CLI 创建时未设置"当前用户"过滤,需要你点"筛选" → 添加字段"负责人" contains "当前用户"(选"动态")保存即可。
</callout>

<callout emoji="❓" background-color="pale-gray">
**Q2: 父任务 / 子任务关联不生效,展开没反应?**

A: 确认你用的是「全部任务(树状浏览)」视图,该视图的排序是按 WBS 编号,才能看到树形层级。看板/甘特图视图不展示父子关系。
</callout>

<callout emoji="❓" background-color="pale-gray">
**Q3: 想新增一个项目但不知道放哪个工作区?**

A: 原则是"**同业务方向放同一个工作区**"。例如"AI 产品开发工作区"放所有 AI 产品类项目。如果你的新项目不属于任何现有工作区,超管(张诏瑜)会评估是否新建工作区。
</callout>

<callout emoji="❓" background-color="pale-gray">
**Q4: 保密等级选错了怎么办?**

A: 直接在项目主表改「保密等级」字段值即可,下次刷新后 Lookup 字段自动同步,权限立即生效。
</callout>

<callout emoji="❓" background-color="pale-gray">
**Q5: 我不想做项目经理了,怎么转交?**

A: 在「项目主表」对应项目的「项目经理」字段改成新的人。权限会自动切换到新 PM 身上(因权限是字段驱动的)。
</callout>

---

## 九、关键链接

- **通用模板**:`项目管理中心(通用模板)` — 用于克隆和版本迭代
- **AI 产品开发工作区**:`项目管理中心·AI产品开发` — 当前承载 MVP 项目

如需新建工作区,联系超管(张诏瑜)。

---

<callout emoji="📝" background-color="light-gray">
**文档维护**:本 SOP 随模板演进迭代,有修改需求请联系超管更新。版本 v1.0 · 2026-04-24 · 张诏瑜 起草
</callout>
