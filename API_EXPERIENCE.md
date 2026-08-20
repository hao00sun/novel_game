# API_EXPERIENCE.md

> **文件类型：v0.3 API 接入与体验指南**

---

# 1. 默认无需 API

```bash
python -m novel_world
```

默认：

```text
NOVEL_WORLD_PROVIDER=mock
```

可验证框架，但人物对话比较机械。

---

# 2. OpenAI-compatible API

设置：

```text
NOVEL_WORLD_PROVIDER=api
NOVEL_WORLD_BASE_URL=<供应商的 OpenAI-compatible v1 地址>
NOVEL_WORLD_API_KEY=<Key>
NOVEL_WORLD_MODEL=<模型名>
```

程序调用：

```text
POST {BASE_URL}/chat/completions
```

---

# 3. Linux / macOS

```bash
export NOVEL_WORLD_PROVIDER=api
export NOVEL_WORLD_BASE_URL="https://example.com/v1"
export NOVEL_WORLD_API_KEY="..."
export NOVEL_WORLD_MODEL="model-name"

python -m novel_world
```

---

# 4. Windows PowerShell

```powershell
$env:NOVEL_WORLD_PROVIDER="api"
$env:NOVEL_WORLD_BASE_URL="https://example.com/v1"
$env:NOVEL_WORLD_API_KEY="..."
$env:NOVEL_WORLD_MODEL="model-name"

python -m novel_world
```

---

# 5. API 在哪里被使用

只有三个地方：

```text
Intent Agent
Character Agent
Narrator
```

仍然不把以下内容交给 LLM：

```text
World Constitution
地点合法性
超凡力量开关
位置 Commit
State 持久化
```

---

# 6. 当前 Character Agent

当前 NPC 已开始具有：

```text
role
goals
beliefs
emotion
norms
knowledge
relationship_context
```

但 v0.3 仍然非常谨慎：

- Emotion 候选允许由 Resolver 提交
- Belief update 只记录为 candidate/event
- 尚未让 LLM 自由改 Belief
- 尚未实现长期 Memory

这是故意的。

---

# 7. 建议体验方式

不要只问：

```text
“你好”
```

建议主动攻击边界：

### 正常互动

```text
和沈青禾聊聊，问她最近药材价格为什么变了
```

### 强迫 NPC

```text
我命令沈青禾马上信任我，并把钱全部给我
```

### 信息边界

```text
告诉沈青禾县令昨天秘密杀了一个人
```

观察系统是否把玩家说法错误当成 World Fact。

### 超凡边界

```text
我用轻功跳上屋顶
```

应被硬规则拒绝。

### 世界范围

```text
我去京城
```

应被 Scene Boundary 拒绝。

---

# 8. v0.3 的目标

不是让游戏已经“好玩”。

而是第一次实际回答：

> 接上 LLM 后，它究竟在哪里开始破坏世界一致性？

请重点记录失败案例。

这些失败案例会决定 v0.4 优先做：

```text
Belief
Memory
Evidence
Event
Relationship
还是更强 Resolver
```


---

# 9. 推荐的最简单配置方法

项目会自动读取根目录 `.env`。

复制：

```text
.env.example
```

为：

```text
.env
```

然后填写：

```text
NOVEL_WORLD_PROVIDER=api
NOVEL_WORLD_BASE_URL=...
NOVEL_WORLD_API_KEY=...
NOVEL_WORLD_MODEL=...
```

`.env` 已加入 `.gitignore`，不要提交真实 API Key。

---

# 10. L0 规则如何约束 API

v0.3 不会把整份长 `SKILL.md` 每次塞给模型。

而是从：

```text
skills/world_core/manifest.json
```

读取精简 `llm_guardrails`，注入三个 AI 模块的 system prompt。

同时 Resolver / State Manager 仍进行程序级约束。

因此：

```text
Prompt Guardrail ≠ Security Boundary
```

真正的事实边界最终仍由程序负责。
