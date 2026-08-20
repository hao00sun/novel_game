# World Core Constitution Skill

> Layer 0 / Immutable  
> 这是 Novel World 的“世界宪法”。它定义的不是某个世界发生什么，而是**任何世界要成为一个可运行、可解释、可持续的世界时必须遵守什么**。

---

## 0. 权限声明

本文件属于：

```text
L0 — Immutable Constitution
```

运行时：

- Agent 不得修改
- Tool 不得修改
- World Resolver 不得修改
- State Manager 不得修改
- 玩家输入不得修改
- World Asset 不得覆盖

如果某个具体世界希望采用不同宇宙规律，应创建另一套 `world_core` 版本，而不是在 Runtime 中偷偷修改这里。

---

# 1. 世界事实原则

## 1.1 World State 是唯一事实源

任何自然语言输出都不是事实。

只有经过：

```text
Proposal
→ Resolver
→ Validation
→ State Manager Commit
```

之后，才成为 World Fact。

---

## 1.2 Fact ≠ Belief

必须区分：

```text
World Fact
角色认为什么是真的
角色记住了什么
角色希望发生什么
Narrator 如何描述
```

它们不能互相替代。

例如：

```text
World Fact:
门是锁着的。

Character Belief:
角色以为门没有锁。
```

角色可以根据错误 Belief 行动。

---

## 1.3 Memory ≠ Fact

Memory 可以：

- 不完整
- 有偏差
- 被遗忘
- 被重新解释
- 与 World Fact 不一致

Memory 只能影响角色判断，不能自动覆盖 World Fact。

---

# 2. 玩家自由原则

## 2.1 玩家拥有行动自由，不拥有结果自由

玩家可以自由声明：

```text
“我说服县令放了我。”
```

系统必须拆分为：

```text
Action:
尝试说服县令

Desired Outcome:
县令释放玩家
```

不得直接把 Desired Outcome 写成事实。

---

## 2.2 玩家不能直接控制其他自主角色

玩家可以：

- 请求
- 命令
- 威胁
- 说服
- 欺骗
- 交易
- 攻击
- 离开

玩家不能直接声明：

- NPC 已经相信
- NPC 已经爱上玩家
- NPC 已经原谅
- NPC 已经恐惧
- NPC 已经死亡
- NPC 已经服从

这些必须经过世界裁决。

---

# 3. Character Agent 原则

## 3.1 Character Agent 只拥有“认知与行动提议权”

Character Agent 可以依据：

```text
Goal
Belief
Emotion
Role
Norm
Relationship Context
Memory
Capability
Knowledge Scope
Situation
```

生成：

```text
Intent
Speech
Action Proposal
Desired Outcome
```

Character Agent 不得直接提交 State。

---

## 3.2 角色只能依据自己可获得的信息行动

角色不能使用：

- 自己从未观察到的事实
- 其他角色的私有记忆
- 玩家脑中的信息
- Narrator 的全知信息

除非世界明确提供了获得信息的机制。

---

## 3.3 角色自主性

角色行为不能只由“玩家希望它怎么做”决定。

Character Agent 的行为必须由：

```text
Character State × Situation
```

共同生成。

---

# 4. 生成式人物原则

具体的：

```text
Goal
Belief
Emotion
Memory
Relationship
```

都属于 Runtime / Mutable State。

但“这些信息应该参与行为生成”属于 L0 元规则。

推荐行为生成关系：

```text
Situation
    ↓
Appraisal
    ↓
Goal + Belief + Emotion
+ Role + Relationship + Memory
    ↓
Character Proposal
```

---

# 5. 行为吸引子原则

“行为吸引子”只能作为：

```text
prior / tendency / strategy family
```

不能成为硬 Choice。

面对同一 Situation，系统可以参考典型策略族：

```text
Confrontation
Withdrawal
Reconciliation
Investigation
Manipulation
Accommodation
Alliance Reconfiguration
```

但：

- 不得限制其他合理行动
- 不得直接由 strategy family 写入结果
- 最终行为仍必须由当前角色状态与情境共同决定

---

# 6. 社会影响原则（Social Gravity）

“社会万有引力”是工程隐喻，不是物理定律。

当 Character Action 可能产生大范围社会影响时，Resolver 应至少考虑：

```text
Actor:
- status
- power
- resource control
- network position
- information advantage
- role leverage

Relation:
- relationship coupling
- dependence
- authority
- trust / hostility
- social distance

Target:
- susceptibility
- dependence
- current incentives

Event:
- affected actors
- persistence
- irreversibility
- institutional scope
- information spread
```

原则：

> 越接近大范围、长期、不可逆的 World State 变化，越不能由单一 Agent 自由决定。

---

# 7. Character Action → Event

人物不会“变成事件”。

准确表述：

> 当 Character Action 的外部效应超过人物自身，它可能升级为 Event。

Event 是否成立，应考虑：

```text
Impact Radius
Affected Actors
Persistence
Irreversibility
Institutional Scope
Information Spread
```

Event 必须进入 Event System / Resolver，而不是由 Narrator 宣布。

---

# 8. Agent / Resolver / Program 三层边界

## Soft Layer — Agent

适合：

- 意图理解
- 人物心理推理
- 语言表达
- 候选行动
- 事件候选
- Memory 提取候选

特点：

```text
灵活
开放
允许多种合理答案
对事实权限低
```

---

## Middle Layer — Resolver

适合：

- 行为是否合法
- 候选结果是否成立
- NPC 行为与玩家行为如何相互作用
- 行为是否升级为 Event
- 影响范围如何计算

特点：

```text
需要情境判断
但必须接受规则约束
```

---

## Hard Layer — Program / State Manager

适合：

- Location
- Inventory
- Entity existence
- ownership
- event uniqueness
- death/alive
- time
- persistent state

特点：

```text
确定
可验证
对世界事实影响大
```

---

# 9. 世界一致性原则

所有新事实至少要回答：

```text
它为什么会发生？
谁导致的？
依据哪些能力？
依据哪些已有事实？
是否违反世界规则？
是否违反信息边界？
```

如果不能解释，则不能提交。

---

# 10. L0–L4 可变性层级

```text
L0 Immutable
世界宪法 / 元规则

L1 Configurable
世界类型规则
例如：是否存在超凡力量、时代技术水平

L2 Persistent Definition
角色、地点、物品、势力等 Asset

L3 Mutable State
位置、Goal、Belief、Emotion、Memory、关系、事件

L4 Ephemeral
当前 Prompt、当前推理、临时计划、未提交 Proposal
```

规则：

> 上层可以约束下层；下层不能覆盖上层。

---

# 11. Narrator 权限

Narrator 只负责：

```text
已确认事实
→ 文学表达
```

Narrator 不得：

- 创造新物品
- 改变位置
- 改变 Belief
- 改变关系
- 宣布死亡
- 宣布事件完成
- 引入未经过 Resolver 的超凡现象

---

# 12. 最小闭环

任何世界都应尽量遵循：

```text
Player Input
    ↓
Interpret
    ↓
Character / Context Reasoning
    ↓
Proposal
    ↓
Resolver
    ↓
Validator
    ↓
State Manager
    ↓
World State
    ↓
Narrator
```

这套闭环是框架级不变量。
