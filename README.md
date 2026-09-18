# Novel World 📖🎮

> Turn stories into living, interactive worlds.
> 将故事变成一个可以进入、探索、行动并持续演化的世界。

---

## 中文

**Novel World** 是一个开源的 AI 交互叙事 / 虚拟世界项目。

项目的目标不只是“让 AI 续写小说”，而是尝试构建一个具有：

* 世界规则
* 世界状态
* 人物状态
* 自然语言行动
* 行为裁决
* 因果事件
* 角色认知与记忆
* 时间演化

的可运行叙事世界。

玩家不再只是阅读已经写好的剧情，而是作为世界中的一个角色进入其中：

* 扮演已有角色或创建自己的角色
* 使用自然语言自由行动
* 与 NPC 进行持续互动
* 探索地点、人物和事件
* 改变原本可能发生的剧情
* 让世界根据玩家与 NPC 的行为继续演化

---

# 当前阶段

项目目前处于 **v0.3 原型阶段**。

当前重点不是大规模生成剧情，而是先建立一个稳定、可解释、可扩展的 **World Runtime（世界运行时）**。

当前 Demo 使用一个架空古代县城 **「澄源县」** 作为最小实验世界。

设计目标是：

> 即使没有预设“主线任务”，人物、地点、行为和世界状态也能够依据统一规则产生新的事件。

---

# 核心设计思想

Novel World 将：

> **“角色想做什么”**

和：

> **“世界最终发生什么”**

严格分离。

AI / Agent 可以提出行为，但不能直接修改世界事实。

基本流程：

```text
Player Input
玩家自然语言输入
        ↓
Intent / Action Proposal
理解玩家想做什么
        ↓
Tool
标准化原子行为
        ↓
Resolver
检查世界规则、状态、条件与行为后果
        ↓
Outcome
产生合法结果
        ↓
State Manager
提交世界状态变化
        ↓
Event / Memory / Perception
事件、记忆与认知变化
        ↓
Narrator
将已经发生的事实描述给玩家
```

核心原则：

```text
Agent proposes.
Resolver decides.
State Manager commits.
Narrator describes.
```

即：

> **Agent 提议，Resolver 裁决，State Manager 提交，Narrator 描述。**

---

# 世界分层

Novel World 将世界信息划分为不同层级。

## L0 — World Constitution

世界最高规则。

例如：

* AI 不能凭空修改世界事实
* Character Belief（角色相信的事情）不等于 World Truth（世界事实）
* Agent 不能拥有世界最终解释权
* 所有重要状态变化必须拥有合法因果来源

---

## L1 — Static Assets

相对稳定的世界资产，例如：

* 人物
* 地点
* 身份
* 初始关系
* 世界背景
* 固定物品
* 初始剧情信息

当前 Demo 世界资产位于：

```text
assets/beginner_world/
```

---

## L2 / L3 — Runtime World State

运行过程中不断变化的世界状态，例如：

```text
人物当前位置
人物关系
玩家状态
发生过的事件
角色记忆
世界时间
物品状态
局势变化
```

这些信息由 Runtime 系统维护，而不是直接写回原始资产。

---

# 当前架构

当前核心结构大致如下：

```text
                    World Constitution
                           │
                           ▼

Player Input
     │
     ▼
Intent Agent
     │
     ▼
Action / Tool
     │
     ▼
World Resolver
     │
     ├────────── Character / World State
     │
     ▼
Outcome
     │
     ▼
State Manager
     │
     ▼
Runtime World State
     │
     ▼
Narrator
     │
     ▼
Player
```

随着项目继续开发，将逐步加入：

```text
Action System
Character Skill System
Entity System
Probability System
Time System
Event System
Knowledge / Belief / Memory
NPC Autonomous Behavior
Rumor / Social Simulation
```

---

# Tool 与 Skill

Novel World 尝试避免为每一种剧情行为单独编写逻辑。

Instead，复杂行为将由较小的基础能力组合产生。

## Tool

Tool 表示：

> **角色正在尝试做什么。**

例如：

```text
move
look
inspect
listen
take
place
speak
throw
strike
open
use
```

Tool 不直接决定行为是否成功。

例如：

```text
throw(dart, magistrate)
```

只表示：

> 玩家尝试把飞镖投向县令。

是否命中、是否被阻挡、造成什么后果，应由 Resolver 判断。

---

## Character Skill

Skill 表示：

> **角色有多擅长完成某类事情。**

例如：

```text
tracking
herbalism
medicine
archery
literacy
metalworking
social_insight
negotiation
```

基本关系：

```text
Tool
= 做什么

Skill
= 有多擅长

Knowledge
= 知道什么

Profession
= 通常学习过什么

Outcome
= 世界最终发生什么
```

Skill 本身同样没有修改世界事实的权限。

---

# 当前 Demo 世界

当前 Demo 发生在一个架空古代县城：

## 澄源县

这是一个仍然维持基本秩序、但已经开始受到外部局势影响的小型县城。

世界中正在逐渐出现：

* 粮价变化
* 商路异常
* 流民增加
* 地方治安压力
* 官府与地方势力之间的关系变化

当前主要场景包括：

```text
城门
集市
客栈
药铺
铁匠铺
县衙
居民区
城外官道
山林
```

它们不是传统 RPG 的线性“关卡”。

而是构成一个可以自由移动的 **Scene Graph（场景图）**。

玩家可以自行决定：

```text
去哪里
和谁交流
调查什么
做什么事情
```

世界再根据这些行为产生后果。

---

# 当前角色

Demo 中已经存在若干具有不同身份、性格和能力的角色，例如：

* 陆沉 —— 猎户
* 沈青禾 —— 药铺学徒
* 周砚 —— 寒门书生
* 赵实 —— 铁匠
* 柳三娘 —— 市井人物
* 徐知县 —— 澄源县官员

人物并不只是用于生成对话。

长期目标是让角色拥有：

```text
Identity
Attributes
Skills
Knowledge
Beliefs
Memory
Relationships
Goals
Schedule
```

从而能够在没有玩家直接互动时继续行动。

---

# 当前已实现

目前已经具备或正在形成的基础能力包括：

* [x] 基础世界资产加载
* [x] 世界 Constitution（宪法 / 规则层）
* [x] Character 数据模型
* [x] Runtime World State
* [x] Intent Agent
* [x] Character Agent 基础结构
* [x] Tool Registry
* [x] 基础 `move / talk / inspect`
* [x] World Resolver
* [x] State Manager
* [x] Narrator
* [x] CLI Demo
* [x] LLM Provider 抽象
* [x] Mock Provider
* [x] 基础测试体系

---

## Development / 开发环境

Windows PowerShell：

```powershell
py -V:3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

不依赖 pytest 的测试方式：

```powershell
python -m unittest discover -s tests -v
```

如果 PowerShell 阻止 `Activate.ps1`，可执行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

也可以不激活虚拟环境，直接运行：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

---

# 正在建设

当前重点正在从：

```text
能理解玩家输入
```

向：

```text
能可靠地裁决自由行为
```

推进。

近期核心模块包括：

* [ ] Action System
* [ ] Character Skill System
* [ ] Entity / Item System
* [ ] Probability / Uncertainty System
* [ ] Structured Event System
* [ ] World Time System
* [ ] Character Knowledge / Belief
* [ ] Long-term Memory
* [ ] NPC Autonomous Behavior
* [ ] Rumor System
* [ ] Relationship / Social Simulation

---

# 长期目标

在 World Runtime 稳定以后，Novel World 将继续扩展到：

* [ ] TXT / EPUB / PDF 小说导入
* [ ] 人物自动提取
* [ ] 地点自动提取
* [ ] 事件自动提取
* [ ] 世界观 / Lore Extraction
* [ ] Knowledge Base / RAG
* [ ] 原著剧情时间线
* [ ] Canon / Alternative Timeline
* [ ] 世界自动初始化
* [ ] Web 游戏界面
* [ ] AI 场景图片
* [ ] Character TTS
* [ ] 多世界 / 多小说支持

最终希望形成：

```text
Novel / Story
      ↓
World Extraction
      ↓
Characters · Locations · Events · Lore
      ↓
Knowledge Base
      ↓
World Initialization
      ↓
────────────────────────────────
        Novel World Runtime
────────────────────────────────
      ↓
Player + NPC Actions
      ↓
Resolver
      ↓
Events + State Changes
      ↓
Living Story World
```

也就是说：

> **小说最终只是世界的一种“初始条件”。**

真正运行以后，故事将来自：

```text
World Rules
+
Character Decisions
+
Player Actions
+
Time
+
Causality
```

---

# 项目理念

Novel World 不希望变成一个单纯的：

> “让 LLM 自由续写剧情”

的系统。

项目更关注：

### 可解释

为什么发生这件事？

```text
Action
↓
Rule
↓
Resolver
↓
Outcome
```

应该能够被追踪。

### 可复现

相同世界状态、规则和输入，应尽量得到可以分析和复现的结果。

### 可扩展

增加新的：

```text
人物
地点
技能
Tool
世界
```

不应该要求重写整个引擎。

### AI 与程序边界清晰

适合 AI 的部分交给 Agent：

```text
理解
推理
人物表达
行为提议
叙事
```

需要稳定性的部分交给程序：

```text
状态
权限
规则
因果
数据结构
最终裁决
```

---

# English

## Novel World

**Novel World** is an open-source AI interactive storytelling and world-simulation project.

The goal is not simply to let an LLM continue writing a novel.

Instead, Novel World aims to build a persistent world containing:

* world rules
* runtime state
* characters
* natural-language actions
* action resolution
* causal events
* character knowledge and memory
* autonomous world evolution

Players enter the story as part of the world rather than simply reading it.

They can:

* Play as an existing character or create a new one
* Interact with characters through natural language
* Explore locations and events
* Perform free-form actions
* Change events that would otherwise happen
* Create alternative storylines through interaction

---

## Core Principle

Novel World separates:

```text
what a character wants to do
```

from:

```text
what actually happens in the world
```

The basic runtime pipeline is:

```text
Player Input
      ↓
Intent / Action Proposal
      ↓
Tool
      ↓
Resolver
      ↓
Outcome
      ↓
State Manager
      ↓
World State / Events
      ↓
Narrator
```

The central rule is:

> **Agents propose.
> Resolvers decide.
> State Managers commit.
> Narrators describe.**

Agents are not allowed to directly rewrite world truth.

---

## Current Stage

Novel World is currently in an early **v0.3 prototype stage**.

The current demo uses a fictional historical county called **Chengyuan County** as a small experimental world.

The current focus is building a stable and explainable **World Runtime**, including:

* World Constitution
* Character models
* Runtime state
* Intent understanding
* Tools
* Resolver
* State transitions
* Narration

The next major systems include:

* Action System
* Character Skill System
* Entity / Item System
* Probability System
* Time System
* Structured Events
* Character Knowledge / Belief / Memory
* Autonomous NPC behavior
* Social simulation

---

## Long-Term Pipeline

```text
Novel / Story
      ↓
Characters · Locations · Events · Lore
      ↓
Knowledge Base / RAG
      ↓
World Initialization
      ↓
Novel World Runtime
      ↓
Player + NPC Actions
      ↓
Resolver
      ↓
Events + State Changes
      ↓
Living Interactive World
```

In the long term, a novel becomes the **initial condition of a simulated story world**, rather than a fixed sequence of events.

---

## Roadmap

### Runtime Foundation

* [x] World asset loading
* [x] World Constitution
* [x] Character models
* [x] Runtime world state
* [x] Intent Agent
* [x] Basic Character Agent
* [x] Tool Registry
* [x] Basic movement / conversation / inspection
* [x] Resolver
* [x] State Manager
* [x] Narrator
* [x] CLI prototype
* [x] LLM provider abstraction
* [x] Basic tests

### World Simulation

* [ ] General Action System
* [ ] Character Skill System
* [ ] Entity / Item System
* [ ] Probability / Uncertainty
* [ ] Structured Event System
* [ ] World Time
* [ ] Character Knowledge / Belief
* [ ] Long-Term Memory
* [ ] Autonomous NPC Behavior
* [ ] Rumor System
* [ ] Relationship / Social Simulation

### Novel → World

* [ ] TXT / EPUB / PDF import
* [ ] Character extraction
* [ ] Location extraction
* [ ] Event extraction
* [ ] Lore extraction
* [ ] Knowledge Base / RAG
* [ ] Canon timeline
* [ ] Alternative timeline generation
* [ ] Automatic world initialization

### Experience Layer

* [ ] Web game interface
* [ ] AI-generated scene images
* [ ] Character TTS
* [ ] Multi-world support

---

## Philosophy

Novel World is built around four ideas:

**Explainable**

World changes should have traceable causes.

**Reproducible**

Important behavior should be inspectable and testable rather than hidden entirely inside an LLM.

**Composable**

New characters, locations, tools and skills should be added without rewriting the entire engine.

**Clear AI / System Boundaries**

LLMs are good at:

```text
language
interpretation
character reasoning
proposal generation
narration
```

Deterministic systems should own:

```text
state
permissions
rules
causality
validation
final world transitions
```

---

## Status

Novel World is currently an experimental early-stage project.

The architecture, APIs and data formats may change substantially as the world runtime evolves.

Contributions, experiments and discussion are welcome.

---

## License

To be determined.
