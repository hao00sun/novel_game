"""
WorldResolver 当前整改方向：从“禁止项识别”转向“因果合法性验证”

当前世界裁决不能长期依赖对非法行为进行枚举，例如：

    禁止轻功
    禁止御剑
    禁止瞬移
    禁止读心
    禁止隐身
    ...

这种 Blacklist 方式无法穷举自然语言表达。

例如：

    “身体化作烟雾穿过墙壁”

即使没有出现“法术”“瞬移”等关键词，
本质上仍然试图产生一个当前世界无法解释的状态变化。

因此 Resolver 的长期目标不应是：

    “识别所有不允许发生的事情”

而应转变为：

    “任何准备 Commit 的 World State Change，
     都必须具有合法、可验证、可追溯的因果来源。”


============================================================
核心原则
============================================================

玩家 / CharacterAgent 可以自由提出 Action / Proposal。

但：

    Proposal != World Fact

只有当 Proposal 导致的 State Change
能够通过当前世界允许的因果机制得到解释时，
Resolver 才能生成可提交的 Outcome。


推荐流程：

    Free-form Action / Proposal
            ↓
    Semantic Effect Extraction
            ↓
    Candidate State Change
            ↓
    Causal Mechanism Identification
            ↓
    Hard Constraint Validation
            ↓
        ┌───┴───┐
        │       │
      invalid  valid
        │       │
      reject    ↓
             Soft Resolution
             Program / LLM / Hybrid
                 ↓
               Outcome
                 ↓
             StateManager
                 ↓
              Commit


============================================================
不要依赖“超凡关键词黑名单”
============================================================

关键词检测，例如：

    轻功 / 法术 / 瞬移 / 读心 / 飞行 ...

只能作为：

    semantic warning
    risk flag
    fallback heuristic

不能作为最终安全边界。

即使没有任何关键词命中，
Resolver 仍必须验证实际产生的 State Change。


============================================================
应验证“状态变化来源”，而不是“动作名称”
============================================================

例如：

1. Location Change

    east_gate
        ->
    county_office

Resolver 不应只问：

    “玩家有没有说‘瞬移’？”

而应问：

    “这个位置变化通过什么机制发生？”

可能的合法来源：

    walk
    ride
    vehicle
    known ability
    valid route
    environmental mechanism

如果没有合法路径或能力：

    reject


2. Knowledge Change

如果玩家突然获得某个秘密：

    player.knowledge += secret

必须能够说明信息来源，例如：

    observation
    conversation
    document
    evidence
    information propagation
    inference

如果只是：

    “我感受到他内心真正的想法”

而当前世界没有对应能力或信息渠道：

    reject


3. Inventory Change

如果：

    player.inventory += sword

必须能够追溯：

    pickup
    transfer
    purchase
    crafting
    existing inventory
    valid generation rule

不能：

    source = None
        ->
    凭空产生物品


4. Character Belief Change

角色 Belief 不应因为 LLM 认为“应该改变”
就直接修改。

必须存在合理来源：

    evidence
    observation
    testimony
    inference
    accumulated experience

CharacterAgent 可以提出：

    belief_update_candidate

但 Resolver / Evidence System
应验证其因果基础。


============================================================
未来建议引入 State Change Provenance
============================================================

长期可考虑让重要的 Candidate State Change
携带来源信息，例如：

    {
        "path": "player.location",
        "old": "east_gate",
        "new": "county_office",

        "cause": {
            "type": "movement",
            "mechanism": "walk",
            "source_action": "...",
            "evidence": {...}
        }
    }

或者：

    {
        "path": "player.knowledge.secret_x",
        "new": true,

        "cause": {
            "type": "information_acquisition",
            "mechanism": "read",
            "source": "notice_001"
        }
    }

核心要求：

    No Cause
        ->
    No Commit

    Invalid Cause
        ->
    No Commit


============================================================
程序与 LLM 的职责边界
============================================================

不要试图完全使用程序枚举所有合法行为，
否则会损失自由度。

也不要让 LLM 拥有最终世界裁决权，
否则会产生不稳定和逻辑漏洞。

推荐分工：

Program / State:
    - 当前事实是什么
    - Entity 是否存在
    - Location 是否可达
    - Item 是否存在
    - Character 是否拥有某能力
    - Knowledge 是否有合法来源
    - World Rule 是否允许某机制
    - State Change 是否违反硬约束

LLM:
    - 理解玩家复杂自然语言
    - 提取行为语义
    - 提出 Candidate Action / Effect
    - 在合法空间内进行开放式软判断

Hybrid Resolution:
    - 对“合理但不确定”的灰区进行判断
    - 例如说服、风险动作、复杂社会反应等

因此：

    LLM 负责提出可能性
    Program 负责守住边界
    Resolver 负责组合两者完成裁决


============================================================
关于 extraordinary.enabled
============================================================

extraordinary.enabled == false

不应理解为：

    “匹配并禁止所有超凡词汇”

而应理解为：

    当前世界不存在未定义的超自然因果机制。

因此任何依赖：

    teleportation
    mind reading
    materialization
    supernatural transformation
    undefined supernatural ability

等机制才能成立的 State Change，

如果 World Rules / Character Capability
没有显式提供该机制，

则不得 Commit。


============================================================
长期目标
============================================================

Resolver 不应该发展成：

    数千条动作 if / else

而应该逐渐成为：

    State Transition Validator
            +
    Causal Consistency Resolver

即：

    不需要知道所有“不可能是什么”，

    只需要要求所有准备成为事实的变化，
    都能够证明：

        “它为什么能够在这个世界里发生？”


一句话原则：

    玩家可以自由提出任何行动，
    但任何 World State Change
    都必须具有合法且可追溯的因果来源。
"""


from __future__ import annotations

from .models import Outcome


class WorldResolver:
    def __init__(self, assets, tools, skill_system=None):
        self.assets = assets
        self.tools = tools
        self.skill_system = skill_system

    def _resolve_skill_observations(self, state, location):
        """Expose authored L2 observations according to L4 skill evaluations."""
        if self.skill_system is None:
            return [], []

        observations = []
        checks = []
        for definition in location.get("skill_observations", []):
            evaluation = self.skill_system.evaluate(
                state["player"],
                definition["skill_id"],
                definition["difficulty"],
                definition.get("context_modifiers"),
            )
            checks.append(evaluation.to_dict())
            authored = definition["observations"]
            observations.append(authored.get(evaluation.grade, authored["default"]))
        return observations, checks

    def _resolve_reachable_destination(self, state, scene, destination):
        dest = destination
        if dest not in scene["allowed_location_ids"]:
            loc = self.assets.find_location_by_name(dest or "")
            if loc:
                dest = loc["id"]

        if dest not in scene["allowed_location_ids"]:
            raise ValueError(
                "该地点不属于当前澄源县 Scene；当前城外仅开放山林。"
            )

        if not self.assets.is_location_reachable(state["player"]["location"], dest):
            raise ValueError("当前地点与目标地点之间没有已定义的可达路径。")
        return dest

    def resolve(self, state, intent, npc_proposal=None) -> Outcome:
        world = self.assets.world()
        scene = self.assets.scene()

        # 1. Extraordinary remains hard-disabled in this world.
        if intent.extraordinary or intent.kind == "extraordinary":
            if not world["extraordinary"]["enabled"]:
                return Outcome(
                    ok=False,
                    message="当前世界的超凡力量尚未启用。该尝试不会成为世界事实。",
                    rejected_claims=["超凡能力未在 L1 World Rules 中启用"]
                )

        # 2. Move
        if intent.kind == "move":
            try:
                dest = self._resolve_reachable_destination(
                    state, scene, intent.destination
                )
            except ValueError as e:
                return Outcome(ok=False, message=str(e))

            result = self.tools.move(state, dest)
            return Outcome(
                ok=True,
                message=result["message"],
                state_changes=result["state_changes"],
                events=result["events"]
            )

        # 3. Talk + Character Agent proposal
        if intent.kind == "talk":
            if not intent.target:
                return Outcome(ok=False, message="没有识别到明确交谈对象。")

            changes = []
            events = []

            # Compound action: “去药铺和沈青禾聊聊”
            # The Resolver may accept the movement first if the destination is legal
            # and the NPC is actually there.
            runtime_target = state.get("actors", {}).get(intent.target)
            if runtime_target is None:
                return Outcome(ok=False, message="该目标当前不是可交互 NPC。")

            if runtime_target.get("location") != state["player"]["location"]:
                try:
                    destination = self._resolve_reachable_destination(
                        state, scene, intent.destination
                    )
                except ValueError as e:
                    return Outcome(ok=False, message=str(e))

                if runtime_target.get("location") == destination:
                    move_result = self.tools.move(state, destination)
                    changes.extend(move_result["state_changes"])
                    events.extend(move_result["events"])

                    # Validate talk against a temporary state view, not by mutating state.
                    temp_state = {
                        **state,
                        "player": {**state["player"], "location": destination}
                    }
                    try:
                        result = self.tools.talk(temp_state, intent.target)
                    except (KeyError, ValueError) as e:
                        return Outcome(ok=False, message=str(e))
                else:
                    asset = self.assets.get_character(intent.target)
                    return Outcome(ok=False, message=f"{asset['name']}当前不在这里。")
            else:
                try:
                    result = self.tools.talk(state, intent.target)
                except (KeyError, ValueError) as e:
                    return Outcome(ok=False, message=str(e))

            events.extend(result["events"])
            proposal_dict = npc_proposal.to_dict() if npc_proposal else None

            if npc_proposal:
                # v0.3 allows only soft emotion candidate to be committed,
                # and only as a descriptive runtime state.
                # Belief updates remain uncommitted until a stronger evidence model exists.
                if npc_proposal.emotion_update_candidate:
                    changes.append({
                        "path": f"actors.{intent.target}.emotion.state",
                        "value": npc_proposal.emotion_update_candidate
                    })

                if npc_proposal.belief_update_candidate:
                    events.append(
                        f"{self.assets.get_character(intent.target)['name']}出现信念重新评估候选："
                        f"{npc_proposal.belief_update_candidate}"
                    )

            return Outcome(
                ok=True,
                message=result["message"],
                state_changes=changes,
                events=events,
                npc_proposal=proposal_dict
            )

        # 4. Inspect
        if intent.kind == "inspect":
            info = self.tools.inspect(state)
            people = "、".join(info["people"]) if info["people"] else "暂未发现明确人物"
            location = self.assets.get_location(state["player"]["location"])
            observations, skill_checks = self._resolve_skill_observations(state, location)
            observation_text = ""
            if observations:
                observation_text = "\n" + "\n".join(f"你注意到：{item}" for item in observations)
            return Outcome(
                ok=True,
                message=(
                    f"【{info['location']}】{info['description']}\n"
                    f"当前可见人物：{people}{observation_text}"
                ),
                skill_checks=skill_checks,
            )

        # 5. Free-form:
        # record attempt, but do not fabricate a result.
        return Outcome(
            ok=True,
            message="这个自由行为暂时没有对应 Tool。系统记录了尝试，但没有擅自生成世界结果。",
            events=[f"未结算自由行动：{intent.raw_text}"]
        )
