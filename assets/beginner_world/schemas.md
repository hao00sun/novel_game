# Asset Schemas — v0.2

## 五层结构

```text
L0 skills/world_core/
L1 world.json
L2 scene / locations / characters
L3 runtime state
L4 current-turn proposal
```

---

## world.json — L1

描述：

```text
这是哪一种世界
是否存在超凡
时代技术
全局配置
```

它不能覆盖 L0。

---

## scene.json — L2

描述当前可运行区域的 Persistent Definition。

---

## locations.json — L2

地点资产。当前支持：

```text
description
tags
aliases
connections      # Location Graph 中可达的相邻地点
scene_rules      # 静态场景边界
skill_observations # 已写死的地点观察事实
```

---

## characters.json — L2

人物模板资产。

不是 Runtime State。

人物技能以 `skills: {skill_id: 0~5}` 保存；具体知识仍留在
`agent_profile.knowledge`，不得用技能等级替代。

---

## skills.json — L2

可组合的人物技能定义。包含 `related_stats`、`applicable_tools`、
`trained_only` 与未来知识/效果元数据；技能评估是 L4，不直接写 Runtime。

---

## objects.json — L2

静态物品与可操作对象模板。`GameEngine.create_state()` 会复制为 L3
`entities`；Tool 只对 L3 Entity 产生候选变化。

```text
id / name / location
portable / equippable / affordances
openable / is_open / container / surface / contained_in
readable / writable / content
```

---

## 预留世界资产 — L2

```text
world_lore.md        # 完整背景和未来 RAG 来源
factions.json        # 利益网络及静态资源与约束
event_templates.json # 事件定义、因果链和初始条件模板
rumors.json          # 传闻模板，不等于 Runtime 已传播传闻
```

这些文件当前不由 Runtime 自动结算；对应系统实现后才接入。

---

## Runtime State — L3

后续存：

```text
location
inventory
entities
world_time
goal
belief
emotion
memory
relationship
events
```

---

## Proposal — L4

例如：

```text
Intent
Character Proposal
Event Candidate
Narrative Draft
```

没有经过 Resolver + StateManager 就不能成为事实。
