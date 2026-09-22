"""
============================================================
长期权限原则
============================================================

无论 IntentAgent 后续变得多复杂，都应保持：

1. IntentAgent 负责理解玩家表达。
2. IntentAgent 可以拆动作，但不能判定动作成功。
3. IntentAgent 可以识别 DesiredOutcome，但不能把它当成事实。
4. IntentAgent 不能修改 World State。
5. IntentAgent 不应获得超出玩家知识边界的信息。
6. LLM 输出必须经过结构校验和实体引用校验。
7. 复杂语义解析与世界裁决必须继续分离。

一句话：

    IntentAgent 的目标不是“替玩家行动”，
    而是尽可能无损地表达“玩家到底尝试了什么”。
IntentAgent 当前定位与已知架构限制

当前 IntentAgent 是面向 v0.x Demo 的玩家输入语义解释器。

核心职责：

Player Free Text
    ->
Intent Interpretation
    ->
Structured Intent
    ->
Resolver

它负责回答：

    “玩家正在尝试做什么？”

而不是回答：

    “玩家是否成功？”
    “世界最终发生了什么？”

IntentAgent 没有修改 World State 的权限。
Intent / DesiredOutcome 都只是玩家意图的结构化表达，
最终结果必须交由 Resolver 裁决，并由 StateManager Commit。


============================================================
当前已知问题
============================================================

1. 无法完整拆解复杂玩家输入
------------------------------------------------------------

当前 Intent 以单一 kind 为核心：

    kind = move | talk | inspect | extraordinary | freeform

因此更接近“主意图分类”，而不是完整的语义拆解。

例如：

    “走到告示前，读完告示，把它撕下来藏进怀里，
     然后去找沈青禾问她认不认识上面的名字。”

实际包含：

    move
    -> read
    -> take/remove
    -> store
    -> move
    -> talk/query

当前结构只能选择一个主要 kind，
其他动作容易被忽略、压缩或落入 raw_text。


2. 缺少多动作 / 动作序列结构
------------------------------------------------------------

当前：

    Intent.kind: str

无法自然表达：

    先 A 再 B
    A 后立即 B
    一边 A 一边 B
    如果 A 则 B
    尝试 A，失败则 B

未来更合理的结构可能是：

    IntentBundle
        actions[]
        desired_outcomes[]
        references[]
        speech_acts[]
        conditions[]
        ambiguities[]

其中 actions[] 应保持动作顺序。

注意：

IntentAgent 可以拆解玩家声明的动作序列，
但不应自行替玩家规划未声明的行动。

即：

    Semantic Decomposition != Autonomous Planning


3. 动作语义维度不足
------------------------------------------------------------

当前结构主要包含：

    kind
    target
    destination
    speech
    desired_outcome
    extraordinary

但自然语言中的行动还可能包含：

    actor
    action
    target
    destination
    source
    instrument
    manner
    quantity
    condition
    timing
    sequence
    negation
    speech content
    information request
    desired outcome

例如：

    “悄悄用袖子遮住那张纸”

至少包含：

    action      = cover
    target      = paper
    instrument  = sleeve
    manner      = secretly

当前 Intent 无法完整保存这些语义。


4. Entity 类型支持不足
------------------------------------------------------------

当前 IntentAgent 主要识别：

    Character
    Location

但玩家实际可能操作：

    Item
    Entity
    Document
    Door
    Container
    Weapon
    Building
    Faction
    Event
    Corpse
    Notice
    Vehicle
    Animal
    Resource

例如：

    “看看告示上写了什么”

当前系统可能只识别为：

    inspect

而无法形成：

    action = read
    target = notice_001

因此后续 Entity System 建立后，
IntentAgent 需要能够解析统一 Entity Reference。


5. 指代解析能力不足
------------------------------------------------------------

玩家不会一直使用完整名称。

常见表达包括：

    “他”
    “她”
    “那里”
    “刚才那个人”
    “那张告示”
    “把它拿起来”
    “继续问他”
    “回刚才那个地方”

这些表达需要结合：

    当前场景
    最近交互对象
    最近动作
    最近对话
    Player Knowledge

进行 Reference Resolution。

当前 interpret() 主要只接收当前 State 中有限信息，
尚未形成正式的指代消解机制。


6. 缺少真正的上下文连续理解
------------------------------------------------------------

当前 IntentAgent 主要看到：

    player_text
    current_location
    locations
    characters
    extraordinary setting

但玩家输入通常依赖前文：

    Turn 1:
        “我问沈青禾最近有没有失踪的人。”

    Turn 2:
        “继续问她最后一次在哪里见到他的。”

第二句话脱离上一回合很难完整理解。

未来需要引入经过控制的：

    recent interaction context
    referenced entities
    current conversation target
    recent actions

但不应把全部 History 无限制塞给 IntentAgent。


7. known_locations / known_characters 的知识边界不准确
------------------------------------------------------------

当前代码实际上使用：

    self.assets.locations()
    self.assets.characters()

因此传给 LLM 的“known_*”更接近：

    World Asset 中存在的所有地点 / 人物

而不一定是：

    玩家真正知道的地点 / 人物

未来如果存在：

    隐藏地点
    密室
    未见过的人物
    秘密组织

直接暴露全部 Asset 会破坏：

    World Truth != Player Knowledge

后续应逐渐改为：

    player_known_locations
    player_known_characters
    visible_entities
    referencable_entities


8. Speech 提取较粗糙
------------------------------------------------------------

fallback 模式下经常直接：

    speech = raw_text

例如：

    “我走过去笑着问沈青禾：最近城外是不是不太平？”

真正 speech 应更接近：

    “最近城外是不是不太平？”

而：

    “走过去”
    “笑着”

属于其他动作或 manner。

未来应进一步区分：

    physical action
    speech act
    utterance content
    social intent


9. DesiredOutcome 虽然已经存在，但仍可能与 Action 混淆
------------------------------------------------------------

当前 Prompt 已要求区分：

    Action
    DesiredOutcome

这是正确方向。

但仅依赖 LLM Prompt 仍可能出现：

    玩家：
        “我说服沈青禾相信我。”

被解析为：

        action = make_shen_believe

而正确语义应是：

        action = persuade / speak
        desired_outcome = shen_believes_player

因此未来最好增加程序化 Intent Validation，
不能只依赖 Prompt 保证权限边界。


10. LLM 输出缺少严格结构校验
------------------------------------------------------------

当前主要通过 data.get(...) 构造 Intent。

理论上 LLM 可能输出：

    kind = "attack_and_run"
    target = 不存在的 ID
    destination = 不存在的位置
    extraordinary = 错误类型

目前缺少完整的：

    schema validation
    enum validation
    entity reference validation
    normalization
    ambiguity detection

未来应形成：

    LLM Output
        ->
    Intent Schema Validation
        ->
    Reference Resolution
        ->
    Normalized Intent
        ->
    Resolver


11. 缺少“不确定 / 歧义”表达
------------------------------------------------------------

当前 IntentAgent 基本必须输出一个答案。

但真实玩家输入可能是：

    “去找那个卖药的。”

如果有两个相关 NPC，
正确结果可能不是强行猜一个。

未来应允许：

    confidence
    ambiguity
    candidate_targets
    unresolved_reference

例如：

    target = null
    candidate_targets = [...]
    ambiguity = true

必要时由界面要求玩家澄清，
而不是让 LLM 随机选择。


12. fallback 规则扩展性有限
------------------------------------------------------------

当前 fallback 依赖关键词：

    去 / 前往 / 走到
    说 / 问 / 聊
    看看 / 查看 / 观察
    ...

这种方式适合 Demo 和 API 故障降级，
但不适合作为长期通用语言理解方案。

随着动作种类增加，如果继续增加：

    if "拿" ...
    if "偷" ...
    if "开" ...
    if "攻击" ...

最终会形成脆弱的大型规则树。

fallback 更适合保持：

    少量高频基础动作
    +
    API 故障时的最低可运行能力

而不是承担完整语义解析。


13. extraordinary 检测较粗糙
------------------------------------------------------------

当前通过固定关键词：

    轻功
    法术
    飞行
    瞬移
    ...

判断 extraordinary。

可能出现：

    “他说自己会轻功”
    “我问这里有没有法术传说”

文本虽然包含超凡词，
但玩家并没有尝试执行超凡动作。

因此未来应区分：

    mention extraordinary
    ask about extraordinary
    attempt extraordinary action

而不是只做关键词命中。


14. API 异常被统一吞掉
------------------------------------------------------------

当前：

    except Exception:
        return fallback(...)

能够保证游戏继续运行，这是优点。

但也可能隐藏：

    API timeout
    JSON parsing error
    Prompt regression
    code bug
    invalid schema
    KeyError

未来应：

    log error
        +
    fallback

而不是静默吞掉所有异常。


15. 缺少 Intent Trace / Provenance
------------------------------------------------------------

当前难以回答：

    这个 Intent 是 LLM 解析的还是 fallback？
    为什么选择这个 target？
    哪些引用被成功解析？
    哪些语义被丢弃？
    是否存在歧义？
    原始 LLM 输出是什么？

未来为了 Debug / Failure Dataset，
建议逐步增加：

    parser_source
    normalized_actions
    resolved_references
    unresolved_references
    ambiguities
    warnings

这些属于解析 Trace，
不属于 World Fact。


============================================================
推荐演进方向
============================================================

当前 IntentAgent 可以继续承担 Demo 阶段的 Intent Parser，
不需要立即升级成复杂 Planner。

优先演进方向应是：

Player Text
    ->
Semantic Decomposition
    ->
Action Atom(s)
    ->
Reference Resolution
    ->
Intent Validation
    ->
Normalized Intent / IntentBundle
    ->
Resolver

未来目标应更接近：

    玩家一句自然语言
        ↓
    尽可能完整拆成“玩家明确尝试的原子动作”
        ↓
    保留动作顺序、目标、条件、说话内容和期望结果
        ↓
    Resolver 再判断哪些动作能够实际发生

而不是：

    玩家一句自然语言
        ↓
    强行压缩成一个 kind



"""

from __future__ import annotations

import json

from ..infrastructure.llm import MockProvider
from ..world.models import ActionAtom, ActionBundle, Intent
from .prompts import ACTION_SYSTEM, INTENT_SYSTEM


EXTRAORDINARY_WORDS = [
    "轻功", "御剑", "法术", "内力", "真气", "飞行",
    "瞬移", "读心", "隐身", "妖术", "神通", "灵力"
]


class IntentAgent:
    def __init__(
        self,
        assets,
        llm,
        constitution=None,
        action_schema=None,
        action_validator=None,
    ):
        self.assets = assets
        self.llm = llm
        self.constitution = constitution
        self.action_schema = action_schema
        self.action_validator = action_validator

    def interpret_actions(self, text: str, state: dict) -> ActionBundle:
        """Parse and validate L4 candidate actions without touching the legacy Intent path."""
        if any(word in text for word in EXTRAORDINARY_WORDS):
            return ActionBundle(
                raw_text=text,
                actions=[],
                ambiguities=["超凡尝试保留给 Legacy Resolver 的世界规则检查。"],
            )
        if self.action_schema is None or self.action_validator is None:
            return ActionBundle(
                raw_text=text,
                actions=[],
                ambiguities=["Action parsing is not configured."],
            )
        if isinstance(self.llm, MockProvider):
            return ActionBundle(
                raw_text=text,
                actions=[],
                ambiguities=["Action parsing requires an LLM provider."],
            )

        reference_context, reference_ids = self._build_action_reference_context(state)
        payload = {
            "player_text": text,
            "tool_schema": self.action_schema.to_prompt_data(),
            "reference_context": reference_context,
        }
        try:
            data = self.llm.json(
                system=ACTION_SYSTEM,
                user=json.dumps(payload, ensure_ascii=False, indent=2),
                temperature=0.1,
            )
        except Exception as error:
            return ActionBundle(
                raw_text=text,
                actions=[],
                ambiguities=[f"Action parsing failed: {type(error).__name__}."],
            )

        return self._validated_action_bundle(text, data, reference_ids)

    def _build_action_reference_context(self, state: dict):
        current_location = state["player"]["location"]
        player_id = state["player"].get("id")
        locations = [
            {"id": location["id"], "name": location["name"], "type": "location"}
            for location in self.assets.locations()
        ]
        characters = []
        for character_id, actor in state.get("actors", {}).items():
            if actor.get("present", True) and actor.get("location") == current_location:
                asset = self.assets.get_character(character_id)
                characters.append({"id": character_id, "name": asset["name"], "type": "character"})
        entities = []
        for entity_id, entity in state.get("entities", {}).items():
            if entity.get("holder") == player_id:
                entities.append({
                    "id": entity_id,
                    "name": entity.get("name", entity_id),
                    "type": "entity",
                    "relation": "inventory",
                })
            elif (
                entity.get("location") == current_location
                and not entity.get("holder")
                and not entity.get("contained_in")
            ):
                entities.append({
                    "id": entity_id,
                    "name": entity.get("name", entity_id),
                    "type": "entity",
                    "relation": "scene",
                })
        context = {"locations": locations, "characters": characters, "entities": entities}
        reference_ids = {item["id"] for group in context.values() for item in group}
        return context, reference_ids

    def _validated_action_bundle(self, text, data, reference_ids) -> ActionBundle:
        if not isinstance(data, dict) or not isinstance(data.get("actions", []), list):
            return ActionBundle(text, [], ["Action parser returned malformed actions."])

        ambiguities = [item for item in data.get("ambiguities", []) if isinstance(item, str)]
        actions = []
        for index, raw_action in enumerate(data["actions"]):
            if not isinstance(raw_action, dict) or not isinstance(raw_action.get("tool"), str):
                ambiguities.append(f"Action {index + 1} is malformed.")
                continue
            action = ActionAtom(
                tool=raw_action["tool"],
                args=raw_action.get("args", {}),
                desired_outcome=raw_action.get("desired_outcome"),
                raw_text=raw_action.get("raw_text"),
            )
            validation = self.action_validator.validate(action)
            if not validation.ok:
                ambiguities.extend(validation.errors)
                continue
            reference_errors = self._validate_action_references(action, reference_ids)
            if reference_errors:
                ambiguities.extend(reference_errors)
                continue
            actions.append(action)
        return ActionBundle(raw_text=text, actions=actions, ambiguities=ambiguities)

    @staticmethod
    def _validate_action_references(action: ActionAtom, reference_ids: set[str]):
        """Check only explicit *_id references; Tool preconditions remain elsewhere."""
        errors = []
        for argument_name, value in action.args.items():
            if argument_name.endswith("_id") and (
                not isinstance(value, str) or value not in reference_ids
            ):
                errors.append(
                    f"Unknown reference for {argument_name}: {value!r}."
                )
        return errors

    def interpret(self, text: str, state: dict) -> Intent:
        if any(word in text for word in EXTRAORDINARY_WORDS):
            return self._fallback(text)
        if isinstance(self.llm, MockProvider):
            return self._fallback(text)

        locations = [
            {"id": x["id"], "name": x["name"], "aliases": x.get("aliases", [])}
            for x in self.assets.locations()
        ]
        characters = [
            {"id": x["id"], "name": x["name"], "identity": x["identity"]}
            for x in self.assets.characters()
        ]

        payload = {
            "player_text": text,
            "current_location": state["player"]["location"],
            "known_locations": locations,
            "known_characters": characters,
            "extraordinary_enabled": self.assets.world()["extraordinary"]["enabled"],
        }

        try:
            data = self.llm.json(
                system=INTENT_SYSTEM + ("\n\nL0 WORLD CONSTITUTION:\n" + self.constitution.llm_guardrails if self.constitution else ""),
                user=json.dumps(payload, ensure_ascii=False, indent=2),
                temperature=0.1,
            )
            return Intent(
                kind=str(data.get("kind", "freeform")),
                raw_text=text,
                target=data.get("target"),
                destination=data.get("destination"),
                speech=data.get("speech"),
                desired_outcome=data.get("desired_outcome"),
                extraordinary=bool(data.get("extraordinary", False)),
            )
        except Exception:
            # API 格式失败时，降级到规则解释，世界仍可运行。
            return self._fallback(text)

    def _fallback(self, text: str) -> Intent:
        t = text.strip()
        extraordinary = any(word in t for word in EXTRAORDINARY_WORDS)

        loc = self.assets.find_location_by_name(t)
        char = self.assets.find_character_by_name(t)

        if extraordinary:
            return Intent(
                kind="extraordinary",
                raw_text=t,
                extraordinary=True,
                target=char["id"] if char else None,
            )

        if char and loc and any(k in t for k in ["说", "问", "聊", "交谈", "打听", "告诉"]):
            return Intent(
                kind="talk",
                raw_text=t,
                target=char["id"],
                destination=loc["id"],
                speech=t,
            )

        if loc and any(k in t for k in ["去", "前往", "走到", "来到"]):
            return Intent(
                kind="move",
                raw_text=t,
                destination=loc["id"],
            )

        if char and any(k in t for k in ["说", "问", "聊", "交谈", "打听", "告诉"]):
            return Intent(
                kind="talk",
                raw_text=t,
                target=char["id"],
                speech=t,
            )

        if any(k in t for k in ["看看", "查看", "观察", "四周", "这里"]):
            return Intent(kind="inspect", raw_text=t)

        return Intent(kind="freeform", raw_text=t)
