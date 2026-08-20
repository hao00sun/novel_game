# DEVELOPMENT_PRINCIPLES.md

> **文件类型：项目协同开发设计原则与架构约束文档**
>
> **适用项目：Novel World**
>
> **文档版本：v0.2.1（新增概率 NPC 生成资产原则，并整合 v0.3 API 实测问题）**
>
> **用途：供开发者、Agent、代码生成工具和后续协作者统一理解项目边界、模块职责、数据分层和设计原则。**
>
> **注意：本文件不是世界设定文件，不是 Runtime State，不是具体 Scene 配置，也不是 `skills/world_core/SKILL.md`。**
>
> - `SKILL.md` 定义“世界运行时必须遵守的 L0 世界宪法”
> - 本文件定义“开发这个系统时，代码和资产应该如何组织、如何协作、哪些原则不能被破坏”

---

# 1. 项目目标

Novel World 的目标不是做一个简单的：

```text
LLM → 续写小说
```

也不是传统的：

```text
Scene → Choice A/B/C → Next Scene
```

而是建立一个：

> **资产驱动、状态可持续、角色具有自主性、玩家拥有自由行动能力、世界具有明确事实边界的生成式交互世界框架。**

核心循环：

```text
Player Input
    ↓
Intent / Action Interpretation
    ↓
Character / Context Reasoning
    ↓
Proposal
    ↓
World Resolver
    ↓
Validation
    ↓
State Manager
    ↓
World State
    ↓
Narrator
    ↓
Player
```

---

# 2. 最重要的设计原则

## 2.1 玩家拥有行动自由，但没有结果自由

玩家可以说：

```text
“我说服县令放了我。”
```

系统应理解为：

```text
Action:
尝试说服县令

Desired Outcome:
县令释放玩家
```

而不能直接写成：

```text
县令已经释放玩家
```

玩家控制：

- 自己尝试做什么
- 自己说什么
- 自己去哪里
- 自己希望达成什么

玩家不能直接控制：

- NPC 的思想
- NPC 的情绪
- NPC 的信念
- NPC 的服从
- 世界结果
- 事件结局

---

## 2.2 World State 是唯一事实源

任何以下内容都不是世界事实：

- LLM 输出
- Agent Proposal
- Narrator 文本
- Memory
- Character Belief
- 玩家描述
- 未提交 Event

只有经过：

```text
Proposal
→ Resolver
→ Validation
→ State Manager Commit
```

之后，才成为 World Fact。

---

## 2.3 Agent 可以提出事实变化，但不能直接成为事实

Agent 的输出应是：

```text
Intent
Proposal
Candidate Action
Candidate Event
Desired Outcome
Interpretation
```

而不是直接修改：

```text
location
inventory
belief
alive/dead
ownership
event status
world fact
```

---

# 3. 五层架构

整个项目使用 L0–L4 分层。

---

## L0 — Immutable Constitution

位置：

```text
skills/world_core/
```

内容：

- Fact / Belief / Memory 分离
- 玩家自由原则
- NPC 自主性
- Agent 权限边界
- Resolver 权限
- State Manager 唯一 Commit
- 信息边界
- 因果一致性
- Narrator 权限
- 行为吸引子原则
- 社会影响原则

特点：

```text
不可被 Runtime 修改
不可被 Agent 覆盖
不可被 World Asset 覆盖
```

---

## L1 — World Configuration

例如：

```text
assets/beginner_world/world.json
```

定义：

- 这是哪一种世界
- 是否存在超凡力量
- 技术水平
- 时代风格
- 世界类型
- 全局规则配置

示例：

```text
普通人类世界
抽象明末风格
超凡力量 disabled
```

换世界时可替换。

---

## L2 — Persistent Definition / Assets

包括：

```text
characters.json
locations.json
scene.json
items.json
factions.json
```

描述：

> “这个世界原本有什么。”

例如：

```text
沈青禾是谁
药铺在哪里
知县是什么身份
铁铺拥有什么工具
```

L2 是资产定义，不是运行时状态。

---

## L3 — Mutable Runtime State

描述：

> “这一局现在发生了什么。”

包括：

```text
location
inventory
injury
goal
belief
emotion
memory
relationship
events
current plan
knowledge
```

L3 必须允许变化。

---

## L4 — Ephemeral

一次推理过程中的临时数据：

```text
Intent
Proposal
Candidate Event
Temporary Plan
Prompt Context
Uncommitted Result
```

如果没有 Commit：

> L4 永远不能被视为事实。

---

# 4. Asset-Driven 原则

核心框架不能把具体世界写死。

错误示例：

```python
if character_name == "沈青禾":
    ...
```

正确方向：

```text
Character Asset
    ↓
AssetLoader
    ↓
Generic CharacterAgent
```

推荐目录：

```text
assets/
├── beginner_world/
├── xianxia_world/
├── cyberpunk_world/
└── ...
```

以后新增世界：

> 优先增加 Asset 和 World Rule，而不是修改核心 Engine。

---

# 5. Character Agent 设计原则

Character Agent 是当前最值得 Agent 化的模块之一。

角色行为建议由以下信息共同决定：

```text
Situation
+
Goal
+
Belief
+
Emotion
+
Role
+
Norm
+
Relationship Context
+
Memory
+
Capability
+
Knowledge Scope
```

可以理解为：

```text
Situation
    ↓
Appraisal
    ↓
Character State
    ↓
Proposal
```

---

## 5.1 Character Belief != World Fact

例如：

```text
World Fact:
商人确实在撒谎。

Character Belief:
角色认为商人说的是真话。
```

角色必须按照自己的 Belief 行动，而不是自动读取全局真相。

---

## 5.2 Character Memory != World Fact

Memory 可以：

- 错误
- 遗忘
- 片面
- 被重新解释

因此：

```text
Memory
→ 影响 Character Decision

不能：
Memory
→ 直接覆盖 World State
```

---

# 6. Agent / Resolver / Program 的分工

一个模块是否应该做成 Agent，应先判断：

> 它是否需要开放式理解、情境判断或存在多个合理答案？

---

## Agent

适合：

- 理解玩家意图
- NPC 行为生成
- 心理推理
- 语言生成
- 候选事件生成
- Memory 提取候选
- Narration

特点：

```text
灵活
开放
结果不唯一
世界修改权限低
```

---

## Resolver

适合：

- 这个行为是否成立
- 结果是否合理
- 影响是否超过角色自身
- 是否触发 Event
- 多个角色行为如何冲突
- 是否违反能力 / 信息 / 世界边界

特点：

```text
允许情境判断
但必须被规则约束
```

---

## Program / Tool / State Manager

适合：

- Location
- Inventory
- Ownership
- Entity existence
- Event uniqueness
- Time
- Alive / Dead
- 数据持久化
- 明确数值或资源变更

特点：

```text
确定
可验证
影响世界事实大
```

---

# 7. 一个重要判断原则

可以用下面三问判断模块应该放在哪一层：

```text
1. 这个问题有没有唯一正确答案？
2. 判断错误会不会污染世界事实？
3. 这个结果能不能被程序验证？
```

通常：

```text
开放性越高 → 越靠 Agent
事实影响越大 → 越靠 Program
处于中间 → Resolver
```

---

# 8. “强角色”与 Event

角色越重要，不代表一定“更强”。

需要拆成：

```text
status
power
resources
network position
information advantage
role leverage
relationship coupling
```

一个角色行动是否升级为 Event，可考虑：

```text
Impact Radius
Affected Actors
Persistence
Irreversibility
Institutional Scope
Information Spread
```

因此：

```text
Character Action
```

可能只是局部行为。

也可能因为社会影响扩大，成为：

```text
Event
```

---

# 9. 社会万有引力原则

“社会万有引力”是项目中的工程隐喻，不是物理定律。

用于提醒系统：

> 一个角色的行为产生多大社会影响，不应只看“力量值”。

应综合考虑：

```text
Actor:
- Status
- Power
- Resources
- Network Position
- Information

Relationship:
- Dependence
- Authority
- Trust
- Hostility
- Social Distance

Target:
- Susceptibility
- Incentive
- Dependency

Event:
- Impact Radius
- Persistence
- Information Spread
```

越接近：

```text
大范围
长期
不可逆
制度性
```

的变化，越不能只由单个 Agent 自由决定。

---

# 10. 行为吸引子原则

“行为吸引子”用于描述：

> 面对某些 Situation，人物行为虽然理论上无限，但往往会集中到有限的典型策略族。

例如：

```text
Confrontation
Withdrawal
Reconciliation
Investigation
Manipulation
Accommodation
Alliance Reconfiguration
```

但必须注意：

```text
行为吸引子 = prior / tendency
```

不是：

```text
固定 Choice A/B/C
```

禁止把行为吸引子重新做成传统 RPG 分支菜单。

---

# 11. Narrator 设计原则

Narrator 是：

```text
World Result → 文学表达
```

Narrator 可以：

- 描述动作
- 写对白
- 写环境
- 写气氛
- 调整文风

Narrator 不可以：

- 创造新事实
- 创建不存在的物品
- 修改角色位置
- 修改 Belief
- 修改关系
- 宣布死亡
- 宣布事件完成
- 擅自引入超凡能力

---

# 12. Tool 设计原则

Tool 应该：

```text
明确
小
可验证
职责单一
```

例如：

```text
move()
inspect()
talk()
transfer_item()
query_location()
get_character_context()
retrieve_memory()
```

Tool 不应该承担：

```text
“决定这个人物现在应该怎么活”
```

这种开放问题应该交给 Agent。

---

# 13. 自建角色与预设角色

当前原则：

## 预设角色

优势：

- 完整背景
- 既有社会关系
- 既有技能
- 既有资产
- 更高属性预算

代价：

- 身份自由度低

---

## 自建角色

优势：

- 身份自由
- 背景自由
- 行动路线自由

代价：

- 初始属性预算更低
- 初始社会资源更少

设计目标：

> 预设角色的优势来自“已存在于世界中的结构”，而不仅仅是数值更高。

---

# 14. 官身份角色

当前 v0.x 原则：

```text
官身份 NPC
→ 不允许作为玩家预设角色
```

原因：

- 官身份天然拥有较大的制度性影响
- 会放大 Event System 的复杂度
- 容易过早进入政治 / 制度模拟
- 不适合当前最小闭环验证

以后是否开放，应作为 World / Scenario 级规则，而不是核心框架硬编码永久禁止。

---

# 15. 超凡力量

当前：

```text
extraordinary.enabled = false
```

但框架保留：

```text
extraordinary_traits
system_id
capability hook
resolver hook
```

原则：

> 超凡力量属于 L1 世界规则 + L2 能力定义，不属于 L0 世界宪法。

因此未来可以：

```text
普通世界：
extraordinary = false

仙侠世界：
extraordinary = true
```

但两者都必须遵守：

```text
角色不能使用自己没有的能力。
```

---

# 16. 当前新手世界的范围

当前 Demo：

```text
勇者世界·凡俗层
↓
抽象中国明末风格
↓
澄源县
↓
单 Scene
```

当前阶段不要过早实现：

- 国家政治
- 战争
- 完整经济系统
- 多城池
- 大规模势力系统
- 完整超凡系统
- 长时序主线
- 复杂 RAG
- 数十个独立 Agent

当前首要任务：

> 验证一个小世界是否可以稳定、自洽地持续运行。

---

# 17. 开发时避免的常见错误

## 错误 1：把 Prompt 当数据库

不要：

```text
“Prompt 里写了，所以世界就是这样。”
```

---

## 错误 2：让 LLM 直接写 State

不要：

```python
state = llm_output
```

---

## 错误 3：所有模块都 Agent 化

不要为了架构看起来“智能”而创建：

```text
Inventory Agent
Location Agent
Save Agent
JSON Agent
```

如果程序能确定完成，就用程序。

---

## 错误 4：过早创建几十个人格参数

不要一开始创建：

```text
trust=72
anger=38
loyalty=91
...
```

先验证：

```text
Goal
Belief
Emotion
Role
Relationship Context
Memory
```

是否已经足够。

---

## 错误 5：把社会模型变成硬公式

社会万有引力、行为吸引子目前首先是：

```text
建模框架
生成先验
Resolver 参考因素
```

不是物理公式。

---

## 错误 6：重新退化成 Plot Graph

如果所有自由行为最后又变成：

```text
Choice A
Choice B
Choice C
```

则失去了本项目最重要的价值。

---

# 18. 新功能开发检查表

新增功能前，应回答：

```text
它属于 L0 / L1 / L2 / L3 / L4 哪一层？

它是 Agent、Resolver、Tool 还是 State Manager 的责任？

它是否会直接修改世界事实？

如果会，为什么不能由 State Manager 提交？

它使用的是 World Fact 还是 Character Belief？

它是否突破 Character Knowledge Boundary？

它是否应该成为 Asset，而不是代码？

换一个世界后，这段代码还能复用吗？
```

如果最后一个问题答案是：

```text
不能
```

应优先检查是否把世界内容 hard-code 到核心框架中了。

---

# 19. 当前阶段的开发路线：先证明“小世界可以长期自洽”

当前阶段不以“快速扩张世界规模”为目标。

第一阶段的核心目标应明确为：

> **证明一个只有一座县城的小世界，可以在玩家自由行动下长期保持事实一致、因果连续、角色自主和状态可持续。**

当前澄源县不是“完整世界”的缩小版，而是：

```text
实验场
+
世界规则验证器
+
失败案例生成器
```

在这一阶段，不急于加入：

```text
第二座城
国家政治
大型战争
完整经济
复杂势力
超凡体系
大规模多 Agent
```

先把一个小世界“跑活”。

---

# 20. 推荐开发飞轮

后续开发应优先遵循：

```text
① 运行小世界
        ↓
② 收集真实失败案例
        ↓
③ 判断问题属于哪一层
        ↓
④ 做最小修复
        ↓
⑤ 必要时抽象为宪法 / 法则 / Asset / Tool
        ↓
⑥ 增加一点新的复杂性
        ↓
⑦ 再运行
```

这比：

```text
先设计完整理论
→ 再一次性实现整个世界
```

更适合当前项目。

核心原则：

> **让规则从运行失败中长出来，而不是仅从理论想象中长出来。**

---

# 21. 新手村“跑通”的最低标准

在开始大规模扩充世界前，澄源县至少应稳定满足：

## 21.1 事实一致性

已经发生的事实不会：

```text
无原因消失
被 Narrator 改写
被玩家一句话覆盖
被另一个 Agent 随意修改
```

---

## 21.2 NPC 自主性

玩家不能通过：

```text
“你现在相信我”
“你马上爱上我”
“你立刻放了我”
```

直接控制 NPC 的内部状态或最终行为。

---

## 21.3 信息边界

NPC 只能使用：

```text
亲眼观察
别人告诉
合法推断
已有 Memory
已有 Knowledge
```

获得的信息。

必须避免：

```text
World Truth
自动泄漏给所有 NPC
```

---

## 21.4 因果连续

任何重要结果都应能回答：

```text
为什么会发生？
谁导致的？
依赖哪些前置事实？
角色是否有相应能力？
是否违反当前世界法则？
```

---

## 21.5 状态持续

以下状态应能跨回合保持：

```text
location
inventory
injury
relationship
belief
memory
event
ownership
```

---

## 21.6 自由行动

玩家不应被重新限制成：

```text
Choice A
Choice B
Choice C
```

自由文本即使不能执行，也应尽量被理解为：

```text
Action
Intent
Desired Outcome
```

---

## 21.7 合理失败

非法或当前不支持的行为应该：

```text
被解释
被拒绝
给出世界内合理原因
```

而不是：

```text
程序崩溃
模型乱编结果
```

---

## 21.8 存档恢复

退出并重新进入后：

```text
重要世界事实
人物状态
事件历史
```

不能丢失或重置。

---

# 22. 世界宪法与世界法则必须继续分离

这是后续扩世界时最重要的边界之一。

---

## 22.1 L0 世界宪法

描述：

> **什么样的世界才算一个自洽、合法、可运行的世界。**

它应尽量跨题材成立。

例如：

```text
World State 是唯一事实源
Fact != Belief != Memory
玩家有行动自由但没有结果自由
NPC 具有自主性
Agent 不直接修改 State
角色不能使用自己无法获得的信息
状态变化必须存在因果来源
```

即使未来切换到：

```text
仙侠
赛博朋克
西方奇幻
现代城市
```

这些原则仍然成立。

---

## 22.2 L1 世界法则

描述：

> **这个具体世界允许什么、禁止什么。**

例如当前凡俗世界：

```text
普通人不会飞
没有现代手机
人受到普通人体能约束
官府拥有制度权力
银两可以作为交换媒介
死亡通常不可逆
```

未来仙侠世界可能：

```text
御剑允许
灵力存在
寿命规则不同
死亡可能存在特殊逆转方式
```

因此：

```text
L0 = 世界如何保持自洽
L1 = 这个世界具体怎么运作
```

禁止把二者混在同一个规则文件中。

---

# 23. 规则升格原则：不要轻易把新想法写进 L0

新发现的问题默认不要直接写进世界宪法。

建议按照：

```text
一次失败
↓
局部修复

重复失败
↓
模块规则

多个世界都重复出现
↓
考虑升格为 L0 Constitution
```

例如：

玩家告诉 NPC：

```text
“县令是妖怪。”
```

NPC 下一轮直接把：

```text
县令是妖怪
```

当成 World Fact。

这说明可能缺少：

```text
Statement
Evidence
Belief
Fact
```

之间的边界。

如果这个问题在所有世界中都成立，才适合逐渐抽象成：

> **陈述 != 证据 != 信念 != 世界事实**

并考虑升格为 L0。

---

# 24. 世界扩充原则：一次只增加一种主要复杂性

不要一次加入：

```text
100 NPC
20 城市
国家
经济
战争
超凡
势力
完整任务系统
```

推荐路线类似：

```text
澄源县 v1
地点 + 人物
        ↓
澄源县 v2
人物关系
        ↓
澄源县 v3
Belief / Memory
        ↓
澄源县 v4
Event
        ↓
澄源县 v5
交易 / 经济
        ↓
澄源县 v6
时间流动
        ↓
澄源县 v7
NPC 离线行动
```

每增加一种复杂性：

```text
重新跑测试
重新攻击边界
记录新的 Failure Case
```

这样才能知道：

> **究竟是哪一种复杂性导致世界开始失控。**

---

# 25. Asset Schema 应从真实需求中生长

不要一开始设计一个百科全书式 Asset Schema。

当前已经存在：

```text
world
scene
locations
characters
```

只有当实际运行出现需要时，再新增资产。

例如：

如果出现：

> 铁匠卖给玩家一把刀，但系统无法表达这把刀的持久存在、属性和所有权。

这时再引入：

```text
items.json
```

如果出现：

> 县令、典史、衙役之间的制度关系反复需要描述。

再考虑：

```text
organizations.json
factions.json
```

如果出现：

> NPC 之间的重要历史需要被长期引用。

再完善：

```text
events
memory
relationships
```

原则：

> **Asset 是为了解决已经观察到的世界表达需求，不是为了让 Schema 看起来完整。**

---

# 26. “其他法则”也应从世界运行中长出来

未来可能逐渐出现：

```text
物理法则
信息法则
社会法则
经济法则
组织法则
战斗法则
时间法则
超凡法则
```

但新增“法则”前必须先判断：

```text
这是 L0？
还是某个世界特有的 L1？
还是普通 Program Rule？
还是 Resolver 的判断逻辑？
```

示例：

```text
物品所有权变化
→ Program / State Manager

NPC 愿不愿意卖
→ Character Agent

价格是否能够成交
→ Economy Resolver

交易最终完成
→ State Manager
```

继续遵守：

```text
软判断 → Agent
半确定判断 → Resolver
硬事实 → Program / State Manager
```

---

# 27. Failure Case 驱动开发

从现在开始，应正式积累：

> **Novel World Failure Dataset**

每次遇到异常行为，不要只立即修改代码。

建议记录：

```text
Failure ID

Player Action:
玩家做了什么？

Context:
当时世界和角色状态是什么？

Expected:
一个合理世界应该发生什么？

Actual:
系统实际发生了什么？

Violation:
违反了哪条规则？

Root Cause:
缺 Asset？
缺 Runtime State？
缺 Tool？
缺 Resolver？
缺 World Law？
缺 Constitution？
Prompt 问题？
模型能力问题？

Minimal Fix:
最小修复是什么？

Regression Test:
以后如何自动测试它不再发生？
```

推荐示例：

```markdown
## FAIL-0001

Player Action:
玩家告诉沈青禾“县令是妖怪”。

Expected:
沈青禾最多把它当作玩家陈述，并依据玩家可信度形成新的 Belief 候选。

Actual:
系统直接把“县令是妖怪”写成 World Fact。

Violation:
Statement != Fact

Root Cause:
缺少信息来源与 Evidence 层。

Minimal Fix:
新增 assertion/source/evidence 数据结构。

Regression Test:
同类未经验证陈述不得直接进入 World Truth。
```

长期来看，这份 Failure Dataset 可能比很多 Prompt 更有价值。

它可以用于：

```text
回归测试
模型对比
Prompt 对比
Resolver 对比
世界规则升级验证
```

---

# 28. 新功能必须优先解决“观察到的问题”

后续优先级不要按照：

```text
哪个功能听起来最高级
```

而按照：

```text
哪个失败最频繁？
哪个失败最破坏世界一致性？
哪个机制能够解决最多失败？
```

例如：

如果 v0.3 运行后最大的失败是：

```text
NPC 经常知道自己不该知道的信息
```

那么 v0.4 应优先做：

```text
Epistemic State
Knowledge Boundary
Evidence / Information Source
```

而不是先做：

```text
社会万有引力数学公式
```

如果最大的失败是：

```text
人物十轮以后忘记此前冲突
```

再优先做：

```text
Memory
```

---

# 29. 当前阶段的工作目标

现阶段不要把任务表述为：

> “继续丰富 Novel World。”

更准确的工程目标是：

> **构建并验证一个在玩家自由行动下仍能长期保持自洽的新手村小世界。**

只有当这个目标基本成立，再逐步扩张：

```text
更多人物
更多地点
更多社会关系
更多事件
更复杂的制度
新的世界资产
新的世界法则
```

---

# 30. 当前推荐的演化方式

整个项目应逐步形成：

```text
真实运行
    ↓
Failure Cases
    ↓
最小修复
    ↓
局部规则
    ↓
重复验证
    ↓
稳定抽象
    ↓
Asset / Law / Constitution
```

可以把它理解成：

> **Novel World 的“世界建模飞轮”。**

最终希望做到的不是：

```text
先写一套完美世界理论
```

而是：

> **通过越来越复杂的可运行小世界，逐步逼近一套稳定、可复用、可扩展的世界建模框架。**

# 31. 协同开发原则

多人 / 多 Agent 协同时：

## 修改 L0

必须慎重。

修改：

```text
skills/world_core/
```

意味着改变整个框架的世界哲学和事实边界。

---

## 修改 L1/L2

属于：

```text
世界设计 / 内容资产开发
```

原则上不应该影响 Engine。

---

## 修改 L3

只能通过：

```text
Runtime + StateManager
```

进行。

---

## 新增 Agent

必须说明：

```text
Agent 的职责
输入
允许输出
禁止操作
是否有 State 写权限
```

默认：

```text
State 写权限 = 无
```

---

## 新增 Tool

必须说明：

```text
Tool 操作对象
前置条件
返回值
可能产生的 state_changes
失败条件
```

---

# 32. 当前项目的总设计表达

可以把 Novel World 当前设计压缩成：

```text
世界宪法
决定什么叫“合法世界”

        ↓

World Rules
决定这是“什么世界”

        ↓

Assets
决定世界“原本有什么”

        ↓

Runtime State
决定世界“现在是什么样”

        ↓

Agent
产生理解、意图和候选行动

        ↓

Resolver
判断什么能够真正发生

        ↓

State Manager
把合法结果写入事实

        ↓

Narrator
把事实重新变成故事
```

最终目标不是：

> “让 AI 写出更多文字。”

而是：

> **让 AI 在一个具有事实、认知、因果、角色自主性和社会结构的世界中参与生成故事。**

---

# 33. 本文件的维护规则

文件名：

```text
DEVELOPMENT_PRINCIPLES.md
```

文件类型：

> **Novel World 项目级协同开发设计原则与架构约束文档**

本文件主要面向：

- 人类开发者
- AI Coding Agent
- 项目新协作者
- 架构审查
- PR Review
- 新世界开发人员

当架构发生重要变化时更新。

如果只是：

```text
新增人物
新增地点
修改 Scene
调整某个角色背景
```

不需要修改本文件。

# 34. 通用路人 NPC 的“概率生成资产”设计

后续项目需要支持：

```text
同一套核心框架
+
不同世界观
+
不同环境
+
不同职业
        ↓
生成具有差异性的普通 NPC
```

因此，路人 NPC 不应全部依赖人工手写。建议逐渐建立一个：

> **Probabilistic NPC Generation Asset / 概率式 NPC 生成资产**

它属于“世界内容生成基础设施”，而不是某一个具体世界的固定人物表。

当前澄源县 Demo 暂时不要立即依赖随机 NPC。主要 NPC、关键角色以及用于测试世界边界的人物继续人工设定。当前最重要的问题仍然是世界状态一致性、Agent 权限、空间与物体可操作性、信息边界和 Resolver 裁决。如果现在同时加入大量随机 NPC，会增加调试噪音。

当前路线：

```text
固定人物跑通小世界
        ↓
稳定 Character / Event / State
        ↓
再加入概率生成的普通 NPC
```

# 35. 概率 NPC 的生成原则

NPC 不应该完全随机生成，也不应该由 LLM 每次自由编一个人。更合理的方式是：

```text
World Prior
+
Environment Prior
+
Occupation Prior
+
Local Social Prior
+
Random Variation
        ↓
Trait / Ability Profile
        ↓
Biography Construction
        ↓
Social Relationship Construction
        ↓
Resources / Knowledge / Role
```

世界、环境和职业改变“出现某类人的概率”，随机性只负责在合理分布内制造个体差异。

例如：

```text
边境环境
→ 警觉 / 武力 / 生存技能概率提高

富裕商镇
→ 商业技能 / 识字 / 社交网络概率提高

猎户
→ perception / physique / tracking 的分布偏高

书生
→ intellect / literacy 的分布偏高

商贩
→ social / negotiation 的分布偏高
```

这里的“偏高”表示概率分布发生偏移，而不是固定加点。

同一职业在不同地方也不应该完全相同。例如“澄源县铁匠”和“京城军器机构中的铁匠”，虽然职业相似，但知识、资源、关系网络、技术水平和社会地位可能明显不同。

# 36. “由属性反推成长经历”应理解为一致性生成

不应采用：

```text
先随机数值
→ 再让 LLM 随意补一个故事
```

更建议：

```text
Structured Sampling
        ↓
Constraint Check
        ↓
Compatible History Candidates
        ↓
Biography Generator
        ↓
Consistency Validator
```

例如 `physique=8, perception=8, social=2` 并不能科学地证明角色“小时候一定做过苦工”。

因此所谓“根据性格、能力反推成长经历”，更准确的工程含义是：

> **根据已经生成的人格、能力、身份和世界约束，构造一组能够合理解释这些特征的兼容成长经历。**

这属于 `generative explanation`，不是 `causal inference`。

推荐顺序：

```text
① 确定世界
② 确定地区
③ 抽取身份 / 职业
④ 条件分布生成基础能力
⑤ 条件分布生成人格倾向
⑥ 生成资源 / 知识
⑦ 生成相容成长经历
⑧ 生成少量必要社会关系
⑨ Validator 检查世界一致性
⑩ 写入 Character Asset 或 Runtime NPC
```

只生成足以支持当前交互的信息，不要一开始为每个路人写完整二十年人生史。

# 37. NPC 资产深度分级

建议区分：

```text
Tier A — Key Character
Tier B — Persistent NPC
Tier C — Background NPC
```

**Tier A**：关键人物，需要 Goal、Belief、Emotion、Memory、Relationship、详细背景和持久 State。

**Tier B**：长期出现的店主、邻居、常客、衙役，只需身份、能力、人格倾向、少量关系和重要 Memory。

**Tier C**：真正路人，例如赶集农夫、过路脚夫、普通香客，初始只需职业、基本能力、少量人格特征、当前位置和当前目的。

如果玩家持续与 Tier C 互动：

```text
Tier C → Tier B → 必要时 Tier A
```

这样可以避免为一次性路人生成完整人生和长期状态。

# 38. 概率 NPC Generator 的资产位置

未来可以采用：

```text
assets/
└── npc_generation/
    ├── base_traits.json
    ├── occupations.json
    ├── environments.json
    ├── distributions.json
    └── generation_rules.json
```

或者：

```text
generators/
└── npc_generator/
```

其中：

```text
概率表 / 先验
→ L2 生成规则资产

生成后的持久 NPC
→ L2 Persistent Character

仅当前场景临时存在的 NPC
→ L3 Runtime Entity
```

不要过早设计几十个人格维度。是否保留某个维度，应由真实 Failure Case 和运行效果决定。

# 39. 概率 NPC 与行为吸引子

概率 NPC 生成可以为行为吸引子提供先验：

```text
Personality Profile
+
Occupation
+
Social Role
+
Current Situation
        ↓
Strategy Attractor Prior
```

但始终保持：

```text
概率倾向 ≠ 强制行为
```

人格概率只改变某类策略出现的倾向，不把人物重新限制成 Choice A/B/C。

# 40. v0.3 API 实测：已经确认的成功点

真实测试已经确认：

```text
DeepSeek API 接入成功 ✅
自由语言 → Intent Agent ✅，明显优于 Mock
Character Agent ✅，已经能产生自然角色回应
L0 / L1 / L2 / L3 分层 ✅
Runtime State 跨进程持久化 ✅
超凡力量硬规则 ✅
Agent 不直接 Commit ✅
```

这说明当前瓶颈已经逐渐从：

```text
LLM 是否理解玩家
```

转向：

```text
World Model 是否能承载 LLM 理解出来的行动
```

# 41. FAIL：不存在物品没有进入明确世界裁决

测试中玩家 `inventory=[]`，但输入“展开行囊中的地图”。当前系统只得到：

```text
freeform → 没有对应 Tool
```

理想链路：

```text
Parse Item Reference
        ↓
地图
        ↓
Inventory Query
        ↓
不存在
        ↓
Action Failed
```

因此未来需要 Entity Reference、Inventory Query 和 Item Tool。

# 42. FAIL：Narrative 与 Runtime State 分离

测试输入：

```text
“进城逛一圈观察一下此城建筑分布”
```

Narrator 描述“你从东门入城”，但 Runtime 仍然是：

```text
location = east_gate
```

这属于：

> **Narrative-State Divergence**

这是当前最高优先级问题之一。

原则：

```text
Narrator 描述的状态变化
必须已经存在于 ResolvedOutcome / Runtime State
```

如果 State 没移动，Narrator 不得写玩家已经移动。

# 43. FAIL：复合行为表达能力不足

例如：

```text
“进城逛一圈，并观察建筑分布”
```

实际上包含 Move + Explore + Inspect，当前可能只识别成 `inspect`。

后续可以逐步支持：

```json
{
  "actions": [
    {"type": "move"},
    {"type": "inspect"}
  ]
}
```

但第一阶段不必构建完整 Planner，只支持少量可验证的 Compound Intent。

# 44. FAIL：当前地点只是列表，还不是空间

当前地点 Asset 有东门、市集、客栈、药铺、铁铺、茶摊、城隍庙、县衙前广场，但缺少：

```text
adjacency
direction
distance
visibility
street
region
```

因此 LLM 可能擅自补出“往西走是县衙”，虽然 Asset 从未规定这个事实。

后续需要最小：

> **Location Graph / 空间拓扑**

暂不需要真实二维坐标。

# 45. FAIL：Description 中的物体不是可交互 Entity

当前东门 description 中出现告示、歇脚石、城墙、城门，但它们只是文本，无法真正执行：

```text
查看告示
阅读告示
撕掉告示
坐到石头上
```

未来需要逐渐引入 Entity / Object Asset，例如：

```json
{
  "id": "east_gate_notice",
  "type": "document",
  "location": "east_gate",
  "readable": true,
  "content": "..."
}
```

# 46. FAIL：Targeted Inspect 尚未建立

当前“观察陆沉”可能退化为 inspect 当前 Scene。

未来应支持：

```text
inspect_character
inspect_object
inspect_location
```

返回内容必须来自 Asset、Runtime State 或合法推断，不能由 Narrator 随意制造长期人物特征。

# 47. FAIL：Narrator 可能补充具有语义影响的玩家行为

测试中 Narrator 自动补充玩家称呼 NPC 为“陆兄”，但玩家并未明确说出这一称呼。

应区分：

```text
Cosmetic Detail
vs
Semantic Action
```

Narrator 可以补充低影响表现层细节，但不应擅自增加承诺、威胁、特殊称呼、交易条件、情感表态和新的事实陈述，因为这些内容可能改变关系和后续事件。

# 48. 当前开发优先级

结合真实测试，当前建议：

```text
P0  Narrative-State Consistency
P1  Entity / Object System
P2  Targeted Inspect
P3  Location Graph
P4  Inventory / Item Interaction
P5  Compound Intent
P6  Information / Evidence / Belief
P7  Memory
P8  Probabilistic Background NPC Generator
```

概率 NPC 是合理且重要的方向，但当前不应抢占小世界基础交互的优先级。

# 49. 概率 NPC Generator 的进入条件

建议至少在以下能力基本成立后，再真正接入随机 NPC：

```text
Location Graph 可用
Entity 可交互
Character State 可持久化
Belief / Knowledge 边界基本稳定
NPC 可以保存并重新加载
```

然后先只生成 Tier C Background NPC，不直接随机生成主线人物。

# 50. 更新后的世界演化路线

```text
固定新手村
        ↓
跑通世界状态与交互
        ↓
完善 Entity / Space / Inventory
        ↓
完善 Belief / Evidence / Memory
        ↓
稳定 Character Agent
        ↓
引入概率生成路人 NPC
        ↓
丰富本地社会关系
        ↓
扩展澄源县
        ↓
抽象更多 World Laws / Assets
        ↓
再扩展到新世界观
```

当前固定人物不是最终形态，而是用于建立稳定的“生成式世界底座”。

概率生成 NPC 则是未来让世界从“人工摆放的小场景”升级为“可以持续长出社会成员的世界”的重要通用资产。
