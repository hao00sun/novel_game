# Novel World 开发原则

> 版本：v0.4（Action 与 Runtime Entity 基础完成）  
> 适用范围：Novel World 的代码、资产、测试与协作开发。  
> 本文不是世界设定、存档或 L0 世界宪法；L0 规则以 `skills/world_core/SKILL.md` 为准。

## 1. 项目目标

Novel World 是资产驱动的生成式交互世界框架，而不是“LLM 续写器”或固定选项剧情树。

玩家拥有自由文本的**行动表达权**，不拥有世界结果的决定权。所有可持续的世界事实必须经过确定性边界验证与正式提交。

```text
玩家文本
  ↓
IntentAgent：Intent / ActionBundle 候选
  ↓
Action Validator：结构合法性
  ↓
Resolver：世界规则、前置条件与裁决
  ↓
StateManager：唯一正式提交
  ↓
L3 Runtime State
  ↓
Narrator：只把已确认结果表达给玩家
```

## 2. 不可破坏的原则

1. **行动自由，不等于结果自由。** 玩家可以尝试说服、攻击、调查或移动；不能以一句话直接改写 NPC、物品归属或世界结局。
2. **World State 是唯一事实源。** LLM 输出、Narrator 文本、Agent Proposal、未裁决 Action 与未提交 Event 都不是事实。
3. **StateManager 是 L3 唯一正式写入口。** Tool、Agent、Resolver 和 Narrator 都不得直接修改输入 state。
4. **事实、信念、记忆、叙事必须分离。** 一个角色相信或说出某事，不会自动成为 World Fact。
5. **显示名不等于内部标识。** Runtime 中使用稳定 ID；玩家界面使用 `name` 等可读字段。
6. **失败应被解释或拒绝，不能靠编造补齐。** 无法确认的感知、攻击、使用等行为保留为请求或候选，不伪造成功结果。

## 3. L0–L4 数据边界

| 层级 | 含义 | 例子 | 修改规则 |
| --- | --- | --- | --- |
| L0 | 跨世界的不可变宪法 | Fact/Belief 分离、唯一 Commit | 仅经过明确设计变更 |
| L1 | 世界规则配置 | 超凡是否启用、题材边界 | 由具体 World Asset 定义 |
| L2 | 持久定义资产 | 人物、地点、物品、技能 | 资产驱动，不属于本局状态 |
| L3 | 本局 Runtime State | 位置、持有者、inventory、事件 | 仅 StateManager 正式提交 |
| L4 | 临时推理数据 | Intent、ActionBundle、Proposal、请求 | 未提交即非事实 |

L0 定义“世界如何保持自洽”；L1 定义“这个世界允许什么”；不得把两者混为同一种规则。

## 4. 模块职责

| 模块 | 可以做 | 不可以做 |
| --- | --- | --- |
| IntentAgent | 解释玩家文本、生成 ActionBundle 候选 | 直接认定结果、修改 state |
| CharacterAgent | 生成 NPC 意图、言行 Proposal | 代替 Resolver 改变世界事实 |
| ToolRegistry | 检查可确定前置条件、产生候选变更或请求 | 直接写 L3、虚构不确定结果 |
| ActionValidator | 验证 Tool 名称与参数结构 | 判断可达性、成功率、NPC 意愿 |
| ToolDispatcher | 安全调用已公开且 Schema 暴露的 Tool | 调用私有方法或任意代码 |
| WorldResolver | 检查世界边界、聚合结果、决定可否继续 | 绕过 StateManager 直接提交 |
| StateManager | 预览候选变更、单次正式 Commit | 推断或创造事实 |
| Narrator | 表达已确认结果 | 添加具有语义影响的新事实 |

程序应负责可验证、影响事实的部分；Agent 应负责开放理解与候选生成；Resolver 负责两者间的世界裁决。

## 5. Action System 原则

### 5.1 统一行动表示

`ActionAtom` 是玩家已声明的单个候选 Tool 调用：

```python
ActionAtom(
    tool="equip",
    args={"object_id": "lu_chen_hunting_knife"},
    desired_outcome=None,
    raw_text="装备猎刀",
)
```

`ActionBundle` 保存原始文本、按原声明顺序排列的 Action，以及歧义说明。

语义分解不是自主规划：系统不得替玩家补充未声明的中间步骤。

### 5.2 Schema 与验证

Tool Schema 从 `ToolRegistry` 公开方法签名派生，避免 Prompt、Validator 与 Tool 定义长期漂移。

Validator 只检查：

- Tool 是否存在；
- 参数是否为字典；
- 必填参数是否缺失；
- 是否传入未知字段。

Validator 不检查物品是否可见、行为是否成功、目标是否同意或概率结果；这些属于 Tool 前置条件和 Resolver 的职责。

### 5.3 执行与提交

合法 Bundle 按声明顺序执行。每个成功 Action 的候选结果通过 `StateManager.preview()` 进入临时状态，使后续 Action 可以看到前一步结果；整回合结束后，Engine 只调用一次 `StateManager.apply()` 正式提交。

硬失败停止后续 Action；已确认的前序候选变更仍会在该回合统一提交。不得让新路径和 Legacy Intent 路径对同一句输入重复执行。

`talk` 仍经由 Legacy Intent + CharacterAgent 处理。超凡尝试必须回到 L1 世界规则检查，不能因 Action 解析而绕过禁用状态。

## 6. Runtime Entity 与物品原则

### 6.1 单一可信来源

`assets/beginner_world/objects.json` 是 Object/Item 的唯一完整定义来源。`characters.json` 的 `assets` 仅保存 Object ID，不复制物品名称、能力或属性。

```text
characters.json                 objects.json
lu_chen_hunting_knife  ─────→   { id, name: "猎刀", portable, equippable, ... }
```

AssetLoader 必须校验 Object ID 唯一、角色引用存在、一个初始物品不会拥有多个角色所有者，且角色持有物不同时作为场景物体出现。

### 6.2 Runtime 引用约定

L3 中的以下字段只能保存稳定 Entity ID：

- `player.inventory`、`held_items`、`equipped_items`
- `actors.<id>.inventory`、`held_items`、`equipped_items`
- `entities.<id>.holder`、`contained_in`、`contents`

字段语义：

```text
inventory      当前携带或拥有、可随身访问的 Entity ID 集合
held_items     当前直接拿在手中的 Entity ID 集合
equipped_items 当前处于装备状态的 Entity ID 集合
```

必须保持：

```text
held_items ⊆ inventory
equipped_items ⊆ inventory
inventory item 的 Entity.holder == owner.id
```

预设角色与 NPC 初始 `held_items`、`equipped_items` 均为空，除非未来的 L2 Asset 明确声明初始状态。自建角色初始三个集合均为空。

### 6.3 初始化与显示

Engine 从 L2 Object Definition 复制独立 L3 Entity：

- 场景物体：保留 `location`，`holder=None`；
- 角色初始物品：设 `holder=角色 ID`、`location=None`，并放入对应 inventory。

面向玩家的文本必须优先使用 Entity 的 `name`。内部 ID 只在 `/me`、`/state` 等明确的调试视图中暴露。

### 6.4 存档兼容

Prototype 不维护通用迁移框架。读取存档时必须验证物品集合、holder、container 引用与子集关系；旧版中文物品名或不一致引用必须被拒绝，并要求玩家执行 `/reset`，绝不能静默进入不一致 Runtime。

## 7. 信息与叙事边界

Reference Context 只能暴露当前可用信息：

- 静态地点；
- 当前地点、可交互的角色；
- 当前地点可见的场景 Entity；
- 玩家 inventory 中的 Entity，并标记 `relation: "inventory"`。

这使“检查我的猎刀”“装备猎刀”等文本可使用正式 Entity ID，而不会把中文显示名误作 Runtime 引用。

Narrator 只能表达 Outcome 中已经确认的信息；不得因为语言更自然而增添物品、动作、关系、证据、成功或失败。

## 8. 新功能的最小开发流程

新增系统前，依次回答：

1. 它属于 L0、L1、L2、L3 还是 L4？
2. 它应由 Agent、Tool、Resolver、StateManager 中谁负责？
3. 哪些输入可信，哪些必须验证？
4. 它如何保证不直接污染 L3？
5. 最小可复现失败案例与自动化测试是什么？

实现顺序应是：先复用现有资产、Schema、Tool 和 StateManager；再增加最小字段或分支；最后才考虑新抽象或新依赖。禁止为未来假设提前建设 ECS、通用规划器、完整经济、概率平台或大型 Agent 群。

每项非平凡逻辑至少保留一个会失败的自动化测试。修改前必须保护工作区已有改动；除非用户明确要求，不自动 commit 或 push。

## 9. 当前范围与后续进入条件

当前已稳定的基础：

- L0–L4 数据分层；
- 角色技能评估与场景观察；
- ActionAtom、ActionBundle、Schema、Validator 与安全分发；
- 顺序多 Action、临时预览与单次正式提交；
- Runtime Entity、物品所有权与旧存档拒绝。

当前不实现：Evidence、Belief/Memory 更新、概率、战斗伤害、时间重构、世界 Tick、NPC 自主行动、交易、制作、耐久、重量、装备槽、Web UI、数据库。

下一阶段若进入 Evidence Reference，必须从**已经裁决的感知结果**创建 Evidence；不能仅根据玩家文本、ActionAtom 的目标 ID 或未裁决的感知请求创建“证据”。

## 10. 完成与维护标准

一项变更完成前至少应满足：

- 不绕过 L0/L1、Resolver 或 StateManager；
- Runtime 引用使用稳定 ID，显示层使用可读名称；
- 原有行为与测试保持兼容；
- 新增行为覆盖成功、拒绝或边界案例；
- 运行 `python -m unittest discover -s tests -v`；
- 运行 `git diff --check`，并查看 `git status --short` 与 `git diff --stat`。

本文件应随已验证的架构变化更新。待实现的想法应进入 Roadmap 或设计提案，不应伪装成当前系统已经具备的能力。
