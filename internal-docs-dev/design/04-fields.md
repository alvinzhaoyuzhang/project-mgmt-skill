# 字段规范

> 三个表的字段定义:项目主表、任务表、速查卡表。

## 项目主表

主字段 = `项目名称`(text)

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| 项目名称 | text(主) | 是 | 业务可识别的完整名称 |
| 项目编号 | text | 是 | 格式 `P<年份>-<3位序号>` |
| 项目状态 | select | 是 | 筹备 / 进行中 / 暂停 / 已完成 / 已归档 |
| 项目经理 | user(单) | 是 | 唯一 PM,权限触发依据 |
| 项目成员 | user(多) | 是 | 含 PM 本人,权限可见依据 |
| 项目目标 | text | 是 | 1-3 条可度量成果 |
| 项目描述 | text | 否 | 背景、范围、关键干系人 |
| 开始日期 | datetime | 是 | 计划启动 |
| 计划结束日期 | datetime | 是 | 计划完成 |
| 优先级 | select | 否 | P0 紧急 / P1 高 / P2 中 / P3 低 |
| **保密等级** | select | 是 | L1 公开 / L2 常规 / L3 敏感 / L4 机密 |
| 项目任务 | link(反向) | 自动 | 自动反向关联,无需手填 |

### 保密等级选项 hue

```json
{"name":"L1 公开","hue":"Green","lightness":"Lighter"},
{"name":"L2 常规","hue":"Blue","lightness":"Light"},
{"name":"L3 敏感","hue":"Orange","lightness":"Light"},
{"name":"L4 机密","hue":"Red","lightness":"Light"}
```

## 任务表

主字段 = `任务编号`(auto_number `T-0001`)

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| 任务编号 | auto_number(主) | 自动 | T-0001 系统生成 |
| 任务名称 | text | 是 | 一句话描述做什么 |
| 所属项目 | link → 项目主表 | 是 | 双向链接,反向字段名"项目任务" |
| 任务级别 | select | 是 | 🎯 目标 / 🏁 里程碑 / 📦 一级工作 / 📋 二级工作 / 📌 三级工作 |
| 父任务 | link → 任务表(自) | 除目标外必填 | 双向链接,反向字段名"子任务" |
| WBS 编号 | text | 是 | 格式 `1 / 1.1 / 1.1.2` |
| 任务描述 | text | 否 | 详细上下文 |
| 负责人 | user(单) | 叶子必填 | 可问责人 |
| 协作人 | user(多) | 否 | 参与者,权限可见依据 |
| 状态 | select | 是 | 未开始 / 进行中 / 已完成 / 阻塞 / 延期 / 已取消 |
| 进度 | number(progress) | 否 | 0-100,已完成必须 100 |
| 优先级 | select | 否 | P0 / P1 / P2 / P3 |
| 开始日期 | datetime | 否 | 叶子必填 |
| 计划完成日期 | datetime | 否 | 叶子必填 |
| 实际完成日期 | datetime | 否 | 状态=已完成时填 |
| 交付物 | text | 叶子必填 | 可验收的具体产物 |
| 风险与阻塞 | text | 否 | 正在发生的问题 |
| 最近更新 | text | 建议 | `YYYY-MM-DD 做了X,下一步Y,需要Z支持` |
| 附件 | attachment | 否 | 图纸、截图、参考文档 |
| **任务保密等级**(v1.1) | select(skill 同步) | skill 自动 | 从所属项目.保密等级**写入时同步**(原计划用 lookup,但飞书禁止 lookup 在角色 filter,改用 select 实体)|
| 更新时间 | updated_at | 自动 | 系统字段 |
| 更新人 | updated_by | 自动 | 系统字段 |

### 状态选项 hue

```json
{"name":"未开始","hue":"Gray","lightness":"Lighter"},
{"name":"进行中","hue":"Blue","lightness":"Light"},
{"name":"已完成","hue":"Green","lightness":"Light"},
{"name":"阻塞","hue":"Red","lightness":"Light"},
{"name":"延期","hue":"Orange","lightness":"Light"},
{"name":"已取消","hue":"Gray","lightness":"Standard"}
```

### 任务级别选项 hue

```json
{"name":"🎯 目标","hue":"Red","lightness":"Light"},
{"name":"🏁 里程碑","hue":"Orange","lightness":"Light"},
{"name":"📦 一级工作","hue":"Blue","lightness":"Light"},
{"name":"📋 二级工作","hue":"Blue","lightness":"Lighter"},
{"name":"📌 三级工作","hue":"Gray","lightness":"Lighter"}
```

### 工作区专用扩展字段

某些工作区可以加上**业务专属字段**,不进通用模板:

- **模块**(select) — AI 产品开发工作区的业务模块(s01/s06/s10/编排面板...)
- 其他工作区自行按需加

## 速查卡表

> 放在 Base 内供随手查阅,不进 SOP 文档(避免冗余)

主字段 = `序号`(auto_number)

| 字段 | 类型 | 说明 |
|---|---|---|
| 序号 | auto_number(主) | 自动 |
| 类别 | select | 任务分级标准 / 保密等级标准 / 角色权限 / 字段规范 / 拆解原则 / 日常维护 |
| 条目 | text | 单条说明的标题 |
| 说明 | text | 详细说明文本 |

数据内容:见 `configs/cheat_card_data.json` (34 条)。

## 字段命名原则

1. **用中文**,便于非技术成员理解
2. **不加"的"/"之"等虚词**,保持紧凑
3. **使用业务术语**,避免"是否完成"这类布尔形式(用单选更语义化)
4. **时间字段加"日期"后缀**,区别于动作(如"开始日期" vs "开始")
5. **人员字段统一"XX 人"**(负责人 / 协作人 / 创建人),便于筛选

## 字段变更的级联影响

添加或改名字段时必须检查:
- 引用该字段的 **lookup/formula** 是否失效
- 引用该字段的 **视图筛选/排序/分组** 是否失效
- 引用该字段的 **角色筛选条件** 是否失效
- **表单题目**的 `id` 映射是否失效

因此:**命名改动需要谨慎,加字段比改字段安全**。
