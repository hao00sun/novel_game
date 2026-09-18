# Character Skill System

第一版人物技能系统是一个确定性的 L4 能力评估器，不是 RPG 升级系统，也不拥有世界最终解释权。

```text
Tool        = 角色尝试做什么
Skill       = 角色在某类行为上有多擅长
Knowledge   = 角色具体知道什么
Profession  = 通常学过什么，不是继承层级
Attribute   = 基础天赋条件
Outcome     = Resolver 裁决后实际发生什么
```

技能定义位于 `assets/<world>/skills.json`（L2）；角色以
`skills: {skill_id: 0~5}` 持有等级。`CharacterSkillSystem.evaluate()` 使用：

```text
0.7 × skill level + 0.3 × normalized related stats + context modifiers
```

生成 `SkillEvaluation`：包含有效分数、难度、差值、等级与修正项。它不修改
角色、Runtime State 或资产，也不会创造信息。Resolver 只可用它来决定玩家能从
地点/物品等已写入 L2 的事实中看见哪一层信息，并将该检查记录进 Outcome。

当前只接入 `inspect`：`locations.json.skill_observations` 是资产事实，技能只能
控制默认、`competent`、`strong` 等观察文本的暴露层级。概率、经验升级、知识系统、
战斗、交易与完整 Action System 均未实现。
