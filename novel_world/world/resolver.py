from __future__ import annotations

from .models import Outcome


class WorldResolver:
    def __init__(self, assets, tools):
        self.assets = assets
        self.tools = tools

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
            dest = intent.destination

            if dest not in scene["allowed_location_ids"]:
                loc = self.assets.find_location_by_name(dest or "")
                if loc:
                    dest = loc["id"]

            if dest not in scene["allowed_location_ids"]:
                return Outcome(
                    ok=False,
                    message="该地点不属于当前新手县城 Scene，v0.3 暂不允许离开县城。"
                )

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
                if (
                    intent.destination
                    and intent.destination in scene["allowed_location_ids"]
                    and runtime_target.get("location") == intent.destination
                ):
                    move_result = self.tools.move(state, intent.destination)
                    changes.extend(move_result["state_changes"])
                    events.extend(move_result["events"])

                    # Validate talk against a temporary state view, not by mutating state.
                    temp_state = {
                        **state,
                        "player": {**state["player"], "location": intent.destination}
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
            return Outcome(
                ok=True,
                message=(
                    f"【{info['location']}】{info['description']}\n"
                    f"当前可见人物：{people}"
                )
            )

        # 5. Free-form:
        # record attempt, but do not fabricate a result.
        return Outcome(
            ok=True,
            message="这个自由行为暂时没有对应 Tool。系统记录了尝试，但没有擅自生成世界结果。",
            events=[f"未结算自由行动：{intent.raw_text}"]
        )
