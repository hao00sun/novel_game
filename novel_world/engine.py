from __future__ import annotations

"""
Engine 负责“流程”，不负责“世界细节”。

Engine 当前定位与已知架构限制

当前 GameEngine 是面向 v0.x Demo 的最小闭环回合编排器，主要职责是：

Player Input
    -> IntentAgent
    -> CharacterAgent（当前主要处理显式 talk target）
    -> WorldResolver
    -> StateManager
    -> Storage
    -> Narrator

它的核心价值是保持清晰的权限边界：
- Agent 负责理解、认知和提出 Proposal，不直接修改世界事实。
- Resolver 负责裁决“实际允许发生什么”。
- StateManager 是 Runtime State 的唯一正式 Commit 入口。
- Narrator 只描述已确认 Outcome，不应创造新的世界事实。

当前实现有以下已知限制：

1. 可扩展性有限
   step() 当前是硬编码的线性 Pipeline。
   随着 Time、Event、Memory、Belief、Entity、Relationship、
   NPC Autonomy、Economy 等系统加入，继续直接堆入 step()
   会使 Engine 逐渐膨胀为“上帝模块”。

2. 世界联动能力较弱
   当前主要是“一个玩家 Action -> 一个直接 Outcome”，
   对旁观 NPC、实体、阵营、关系、信息传播及次级影响的处理不足。

3. 缺少影响范围发现机制
   当前较依赖 Intent 中显式 target。
   尚未形成统一的 Affected Entities / Characters / Systems
   发现机制，因此难以支持自然的群体反应和环境连锁效应。

4. 世界自主推进能力不足
   当前世界主要由玩家输入驱动。
   尚缺少统一 World Tick，用于推进时间、计划事件、
   NPC 自主行动、World Pressure、信息传播等。

5. 历史与记忆机制较浅
   当前 history 仅保留最近 30 回合，主要记录：
   player_text / intent / outcome。
   尚未区分 Recent History、长期世界历史、Character Memory、
   Event Log、Knowledge History 和长期摘要。

6. Event 目前更接近日志，而非真正的事件系统
   尚未形成统一的 Event 对象、事件传播、订阅和跨系统联动机制。
   后续复杂世界更适合采用：
   Action -> Event -> 多系统响应 -> Secondary Effects。

7. 缺少复杂回合下的事务与容错能力
   当前流程较简单，因此问题不明显。
   当一次回合包含多个 Agent、World Tick 和跨系统更新后，
   需要考虑阶段失败、Retry、幂等、部分 Commit 和恢复机制。

8. Debug / Trace 能力仍有限
   当前能够记录 Intent 和 Outcome，但未来需要更完整的 TurnTrace，
   包括 Proposal、Affected Set、Resolver Decision、
   State Changes、Events、Rejected Claims、World Tick 和异常信息。

演进原则：
- 当前阶段不为了未来可能出现的复杂度而提前重写 Engine。
- 优先通过真实的新手村运行暴露问题，再逐步抽象。
- 当多个系统开始共享回合阶段时，再考虑 Phased Turn Pipeline。
- 当多个系统需要响应同一世界变化时，再考虑 Event-driven World Simulation。

预期演进方向：

Linear Turn Pipeline
    ->
Phased Turn Pipeline
    +
Event-driven World Simulation

当前 Engine 应继续保持“薄编排层”：
负责规定一次玩家行动按什么顺序经过各权限层，
而不是把具体世界规则、角色心理、事件逻辑和基础设施细节
重新塞回 Engine 本身。
"""

"""
------------------------------------------------------------------------------------------------
未来演进方向：从“离散回合”升级为“时间驱动世界”
一句话原则：

    玩家行动决定自己如何使用时间，
    时间流逝决定整个世界如何继续发展。

并且：

    世界不是随着“回合数”前进，
    而是随着“世界时间”前进。
当前 GameEngine 主要采用：

    Player Input
        ->
    Resolve
        ->
    turn += 1
        ->
    Next Input

的离散回合模式。

长期目标不是让“每次玩家输入”等价于固定一个回合，
而是引入显式 World Time：

    Player Action
        ->
    Action Semantic Parsing
        ->
    Action Resolution
        ->
    Time Cost / Duration Resolution
        ->
    World Time Advance (Δt)
        ->
    World Evolution / World Tick
        ->
    New World State
        ->
    Narration


============================================================
核心目标
============================================================

游戏世界中的时间应持续具有因果意义。

不同玩家行为消耗不同时间，例如：

    看一眼四周
        -> 数秒

    与 NPC 简短交谈
        -> 数十秒 / 数分钟

    仔细搜索房间
        -> 数分钟

    从城东走到城西
        -> 根据距离、路线、速度决定

    睡觉
        -> 数小时

    长途旅行
        -> 数小时 / 数天

因此未来不应继续使用：

    one player input = one fixed turn

而应使用：

    one resolved action = variable Δt


============================================================
时间本身属于 World State
============================================================

World Time 应成为正式的 L3 Runtime State，例如：

    world_time
    date
    time_of_day

或统一时间戳。

时间变化必须像 Location / Inventory 一样，
由正式世界流程 Commit，

不能由 Narrator 或 LLM 任意宣布：

    “几个小时过去了”

除非 World State 中真的已经推进了相应时间。


============================================================
行动时间需要“解析 + 裁决”
============================================================

玩家自然语言本身可能包含时间信息：

    “我快速扫一眼房间”
    “我仔细搜索整个屋子”
    “我等到天黑”
    “我休息半个时辰”
    “我慢慢跟着他走”

Intent / Semantic Parser 应负责提取：

    action
    manner
    explicit duration
    timing intent
    speed intent

但最终实际耗时不能完全由 LLM 决定。

推荐：

    Player Text
        ↓
    Semantic Time Hint
        ↓
    Resolver / Time System
        ↓
    根据世界事实校正

影响实际耗时的因素可能包括：

    action type
    distance
    route
    movement speed
    character capability
    tool
    environment
    interruption
    action complexity
    explicit player intent

因此：

    LLM 可以理解“玩家打算花多久 / 快慢如何”

但：

    Program / Resolver 决定
    “在当前世界中实际过去了多久”。


============================================================
世界必须随着时间自主变化
============================================================

时间推进后，不能只修改：

    world_time += Δt

还需要让世界在这段时间内自行演化。

例如：

    NPC 按自己的计划移动
    商铺开门 / 关门
    天色变化
    守卫换班
    NPC 吃饭 / 睡觉 / 工作
    伤势恢复或恶化
    信息传播
    阵营行动
    Scheduled Event 到期
    World Pressure 升级
    天气 / 环境发生变化
    已开始的事件继续发展

因此长期流程应接近：

    Commit Player Action
            ↓
        Advance Time
            ↓
        World Tick
            ↓
    NPC / Event / Environment Systems
            ↓
        Secondary Events
            ↓
        Commit World Evolution


============================================================
世界发展不能依赖玩家“按下一回合”
============================================================

当前世界主要是：

    玩家做事
        ->
    世界才变化

长期目标应是：

    玩家行为只是世界时间线中的一类事件。

即使玩家：

    等待
    睡觉
    赶路
    藏起来观察

世界中的其他角色和事件仍然会继续运行。

因此：

    Player Activity != World Activity

玩家不行动，
不意味着世界停止。


============================================================
长时间行动必须考虑中途事件
============================================================

如果玩家执行：

    “睡到第二天早上”

耗时可能为：

    Δt = 8 hours

不能简单执行：

    time += 8h

然后一次性计算结果。

因为这八小时内可能发生：

    23:30 盗贼进入客栈
    01:00 城门发生冲突
    03:00 NPC 离开
    05:30 天亮
    06:00 玩家被敲门叫醒

因此未来 Time System 应能够处理：

    start_time
        ↓
    next scheduled event
        ↓
    process event
        ↓
    continue time advance
        ↓
    until target_time

必要时：

    世界事件可以中断玩家原本的长时间行动。


============================================================
时间应成为事件系统的重要基础
============================================================

未来 Event 不应只记录：

    “发生了某件事”

还应具有：

    timestamp
    start_time
    duration
    scheduled_time
    expiry
    causes
    participants

例如：

    Event:
        market_closes
        scheduled_time = 18:00

    Event:
        guard_shift_change
        scheduled_time = 20:00

    Event:
        rumor_propagation
        start_time = ...
        propagation_delay = ...

这样世界事件才能真正沿时间轴运行。


============================================================
失败行为也可能消耗时间
============================================================

Action Failure 不应自动等于：

    Δt = 0

例如：

    尝试撬锁失败
    搜索房间但没找到东西
    与 NPC 交谈但没有获得信息
    走到半路发现道路封闭

即使最终 DesiredOutcome 没有实现，

世界中仍然可能已经过去：

    数秒
    数分钟
    数小时

因此：

    Action Success
    与
    Time Consumption

必须分开建模。


============================================================
时间系统与其他模块的权限边界
============================================================

IntentAgent:
    理解玩家表达中的时间语义，
    例如等待、速度、持续时间、先后顺序。

Resolver:
    判断动作是否成立，并确定合法的实际行动结果。

Time System:
    根据已确认动作计算 / 校正实际 Δt，
    推进 World Clock。

World Tick / Event System:
    处理 Δt 内世界自主发生的变化。

StateManager:
    Commit 已确认的时间和世界状态变化。

Narrator:
    只描述已经确认的时间流逝和世界变化，
    不能自行决定“过了多久”。


============================================================
长期目标
============================================================

GameEngine 最终不应被理解成：

    “处理玩家的一句话”

而应逐渐成为：

    “处理玩家的一次行动，
     并推进由这次行动所跨越的一段世界时间。”

最终形成：

    Player Action
        ↓
    Resolve Action
        ↓
    Resolve Duration
        ↓
    Advance World Clock
        ↓
    Process Events in Chronological Order
        ↓
    World Autonomous Evolution
        ↓
    Commit New World State
        ↓
    Narrate What Actually Happened



"""

from copy import deepcopy

from .world.models import Intent


class GameEngine:
    def __init__(
        self,
        constitution,
        assets,
        intent_agent,
        character_agent,
        resolver,
        state_manager,
        narrator,
        store
    ):
        self.constitution = constitution
        self.assets = assets
        self.intent_agent = intent_agent
        self.character_agent = character_agent
        self.resolver = resolver
        self.state_manager = state_manager
        self.narrator = narrator
        self.store = store

        self.constitution.assert_world_compatible(self.assets.world())#检查世界资产是否符合世界宪法要求

    def _initial_actors(self, player_id):
        actors = {}
        for c in self.assets.characters():
            if c["id"] == player_id:
                continue

            profile = c.get("agent_profile", {})
            actors[c["id"]] = {
                "id": c["id"],
                "location": c["location"],
                "present": True,
                "stats": deepcopy(c["stats"]),
                "skills": deepcopy(c.get("skills", {})),
                "goals": deepcopy(profile.get("goals", [])),
                "beliefs": deepcopy(profile.get("beliefs", [])),
                "emotion": deepcopy(profile.get("emotion", {"state": "平静"})),
                "relationship_context": deepcopy(
                    profile.get("relationship_context", [])
                ),
                "memory": [],
            }
        return actors

    def _initial_entities(self):
        """Copy L2 object definitions into independent mutable L3 entities."""
        entities = {}
        for definition in self.assets.objects():
            entity = deepcopy(definition)
            entity.setdefault("holder", None)
            entity.setdefault("contained_in", None)
            entity.setdefault("contents", [])
            entities[entity["id"]] = entity
        return entities

    def create_state(self, player_character):
        scene = self.assets.scene()
        player = deepcopy(player_character)

        if not player.get("location"):
            player["location"] = scene["entry_location"]

        state = {
            "_meta": {
                "layer": "L3",
                "mutability": "mutable_state",
                "constitution_skill_id": self.constitution.manifest["skill_id"],
                "world_asset_id": self.assets.world()["world_id"]
            },
            "world_id": self.assets.world()["world_id"],
            "scene_id": scene["scene_id"],
            "turn": 0,
            "player": player,
            "actors": self._initial_actors(player["id"]),
            "entities": self._initial_entities(),
            "world_time": {"elapsed_minutes": 0},
            "events": [
                f"{player['name']}进入{scene['name']}"
            ],
            "history": [],
        }
        self.store.save(state)
        return state

    def get_state(self):
        return self.store.load()

    def step(self, text):
        state = self.get_state()

        bundle = self.intent_agent.interpret_actions(text, state)
        uses_action_path = bool(bundle.actions) and not any(
            action.tool == "talk" for action in bundle.actions
        )
        if uses_action_path:
            intent = Intent(kind="action_bundle", raw_text=text)
            outcome = self.resolver.resolve_actions(state, bundle)
        else:
            intent = self.intent_agent.interpret(text, state)
            npc_proposal = None
            if intent.kind == "talk" and intent.target:
                npc_proposal = self.character_agent.react(
                    intent.target,
                    state,
                    intent
                )
            outcome = self.resolver.resolve(
                state,
                intent,
                npc_proposal=npc_proposal,
            )

        new_state = self.state_manager.apply(state, outcome)

        new_state.setdefault("history", []).append({
            "turn": new_state["turn"],
            "player_text": text,
            "intent": intent.to_dict(),
            "action_bundle": bundle.to_dict() if uses_action_path else None,
            "outcome": outcome.to_dict(),
        })
        new_state["history"] = new_state["history"][-30:]

        self.store.save(new_state)

        narrative = self.narrator.render(
            old_state=state,
            intent=intent,
            outcome=outcome,
            new_state=new_state,
        )

        return intent, outcome, new_state, narrative
