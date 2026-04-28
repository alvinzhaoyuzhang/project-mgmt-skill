# 飞书权限规则限制 · 速查表

> **何时读这个文件**:在配置 / 改造**角色权限规则(role.filter_rules)**时,先来这里查一下要用的字段类型是否被允许。
>
> 这个文件是踩过坑后的总结。bootstrap.sh / new-project.sh 在创建角色前会跑 `scripts/_validate_role.py` 自动校验,但你手动改 JSON 时如果先看这个文件,可以省掉一次失败重试。

## 核心规则:filter_rules 中的 field_name 不能引用以下字段类型

| 字段类型 | 为什么不行 | 替代方案 |
|---|---|---|
| **lookup** | 飞书引擎不允许跨表 lookup 进入权限过滤逻辑(性能 + 一致性原因) | 把要过滤的值改成**实体字段**,由 skill 写入时主动同步(如本仓库的「任务保密等级」改造) |
| **formula** | 计算结果在记录写入瞬间才确定,过滤评估顺序无解 | 把驱动 formula 的输入字段(select / number / text)直接放过滤里 |
| **link**(单向 / 双向 / 双向关联) | link 字段值是 record_id 数组,不支持 `is/contains` 文本匹配 | 加一个 lookup 把对方表的"项目名称"等文本字段拉过来 — **但 lookup 又不能用在 filter**!所以**要么走"用户多选"映射(把成员/PM 同步成 user 字段),要么用 select 字段让 skill 维护值** |
| **auto_number**(如「任务编号」T-0001) | 自动编号写入瞬间才生成,过滤里一般也不需要它 | 直接用 record_id 系统字段(skill 内部) |
| **created_time / modified_time / updated_at** | 时间字段在 filter 中只支持有限的相对操作符,且不支持文本类操作 | 改成你需要的 datetime 字段(自定义),skill 写入时同步 |
| **created_by / updated_by** | 系统字段不暴露在权限引擎可访问列表里 | 改成 user 字段(自定义),skill 同步 |
| **attachment** | 附件本身没有"内容值"可比较 | 不要用附件做权限过滤,这设计本身就奇怪 |

## 允许在 filter 中使用的字段类型(白名单)

| 类型 | 常见用法 |
|---|---|
| **text** | 包含 / 等于 关键词,如"任务名称 contains 'X'" |
| **number** | `> < =`,如"进度 > 50" |
| **select / multi_select** | `is / contains`,如"状态 is '已完成'"、"模块 contains 'API'" |
| **user / multi_user** | `contains 当前用户` 是最关键的"个人视图"过滤 |
| **datetime / date** | `>= today / <= today + 7d` 等时间相对运算 |
| **checkbox** | `is true / false` |
| **phone / email / url** | 文本类操作 |

## 设计原则:碰到 lookup/formula 想做权限过滤怎么办

**核心思路:把 lookup 改造成"select 实体字段 + skill 同步写入"**

具体步骤(以本仓库「任务保密等级」改造为参考):

1. **task_table.json**:把字段从 `lookup_fields` 移到 `fields`,声明为 select(选项与源字段对齐)
2. **role JSON**:在 filter 里引用这个**新建的 select 字段**(不是源 lookup)
3. **skill 流程**(见 `references/task-operations.md`):
   - 创建任务时,**主动从所属项目读「保密等级」**,赋值给新任务的「任务保密等级」
   - 改任务的「所属项目」时,同步重读
   - 用户改了项目「保密等级」后,跑 `scripts/_sync_secrecy.py` cascade 到所有相关任务
4. **加注释**:在字段 description 里明确"由 skill 自动同步,请勿手动改"
5. **加预校验**:`_validate_role.py` 拦截下次有人不小心又把 lookup/formula 字段写进 filter

## 已知坑(实际遇到过的)

### 1. lookup 字段导致角色创建失败

**报错**:
```
错误:字段"项目保密等级"不支持在任务表的权限过滤规则中使用
```

**触发条件**:role JSON 的 `record_rule.read_filter_rule_group` / `edit_filter_rule_group` 里 `field_name` 是 lookup 字段。

**修复**:本仓库已把「项目保密等级」(lookup)改造为「任务保密等级」(select 实体)。如果未来发现别的 lookup 字段被引用,跑一次 `_validate_role.py` 拦住,然后按上面的"设计原则"改造。

### 2. link 字段做"按项目过滤"的 dashboard 也踩过

**问题**:`所属项目` 是 link 字段,在飞书 dashboard 里的"按项目过滤"做不到。
**解决**:任务表加一个 lookup 字段「所属项目名称」(纯文本,从项目主表取项目名),dashboard 用它过滤。**但这个 lookup 字段不能用在 role filter** — 同一个字段在 dashboard filter 和 role filter 的支持度不同,要分开评估。

### 3. multi_select 字段在 contains operator 上的语义坑

`select` 多选字段做 `contains` 是 OR 关系("含 A 即匹配"),不是 AND。如果你想要 AND 语义("既含 A 又含 B"),需要把 filter 拆成两条 AND 关系的规则,每条 contains 一个值。

## 参考资料

- 飞书官方权限文档:https://open.feishu.cn/document/server-docs/docs/bitable-v1/advanced-permission/role
- 本仓库的预校验脚本:`scripts/_validate_role.py`
- 本仓库的 cascade 同步脚本:`scripts/_sync_secrecy.py`
- 角色配置 JSON:`configs/roles/*.json`(顶部都有 `_warning_filter_field_types` 提醒)
