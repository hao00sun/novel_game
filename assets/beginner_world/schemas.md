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

地点资产。

---

## characters.json — L2

人物模板资产。

不是 Runtime State。

---

## Runtime State — L3

后续存：

```text
location
inventory
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
