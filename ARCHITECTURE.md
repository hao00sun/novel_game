# ARCHITECTURE.md

> **文件类型：Novel World 技术架构说明**

## v0.3 数据流

```text
L0 World Constitution
        │
        ├───────────────┬─────────────────┐
        ↓               ↓                 ↓
Intent Agent      Character Agent      Narrator
        │               │                 │
        └────── L4 Proposal / Intent ─────┘
                        ↓
                  World Resolver
                        ↓
                  State Manager
                        ↓
                 L3 Runtime State
```

## 为什么 L0 也要进入 Prompt

`skills/world_core/SKILL.md` 不只是文档。

v0.3 中：

```text
manifest.json.llm_guardrails
        ↓
Intent Agent system prompt
Character Agent system prompt
Narrator system prompt
```

因此最外层世界规则同时有两种约束：

```text
生成约束：LLM Prompt Guardrails
执行约束：Resolver / State Manager
```

Prompt 约束不能替代程序校验；二者必须同时存在。

## Provider

```text
LLMProvider
├── MockProvider
└── OpenAICompatibleProvider
```

核心 Agent 不依赖具体厂商。

## 当前 API 使用点

```text
Intent Agent
Character Agent
Narrator
```

不交给 API 的内容：

```text
世界宪法修改
Scene 边界
超凡开关
地点存在性
State Commit
JSON 持久化
```

## Character Runtime

L2 Character Asset 保存初始人物定义。

创建游戏时形成 L3：

```text
actors[id]
├── location
├── goals
├── beliefs
├── emotion
├── relationship_context
└── memory
```

后续 v0.4 会重点加强：

```text
World Truth
≠ Character Belief
≠ Character Memory
```

## Compound Action

v0.3 支持最基础的连续意图：

```text
“去药铺和沈青禾聊聊”
```

Resolver 可以：

```text
验证地点
→ 候选移动
→ 验证 NPC 在目标地点
→ 建立交谈
→ 一次 Commit
```

仍然不会让 Agent 直接修改位置。

---

## 当前代码目录职责

核心 Python 包按“职责 / 权限”分类：

```text
novel_world/
├── __main__.py              # `python -m novel_world` 入口
├── engine.py                # 单回合流程编排，不负责直接裁决事实
├── app/
│   ├── bootstrap.py         # 依赖组装：Constitution / Assets / LLM / Agents / World
│   └── cli.py               # 命令行交互
├── agents/
│   ├── intent.py            # 玩家自由文本 → Intent
│   ├── character.py         # NPC 上下文 → CharacterProposal
│   ├── narrator.py          # 已确认 Outcome → 叙事文本
│   └── prompts.py           # Agent system prompts
├── world/
│   ├── models.py            # Intent / CharacterProposal / Outcome 数据结构
│   ├── constitution.py      # L0 规则加载与兼容性检查
│   ├── resolver.py          # 世界裁决
│   ├── tools.py             # 产生可验证的候选 state_changes
│   └── state_manager.py     # L3 Runtime State 唯一 Commit 入口
├── assets/
│   └── loader.py            # L1/L2 世界资产只读入口
├── characters/
│   └── factory.py           # 预设 / 自建玩家角色构造
└── infrastructure/
    ├── llm.py               # LLM Provider 适配
    ├── storage.py           # Runtime State 持久化
    └── config.py            # .env 配置读取
```

依赖方向应保持为：

```text
app → engine → agents / world
             ↘ assets / characters
             ↘ infrastructure

agents → world.models
agents → infrastructure.llm
world → assets（通过注入的 AssetLoader 使用）
```

原则：`agents/` 只能产生解释、Proposal 或叙事，不直接修改 Runtime State；`world/state_manager.py` 仍是 L3 的唯一事实写入口。
