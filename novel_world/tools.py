from __future__ import annotations


class ToolRegistry:
    """
    Tool 只产生可验证候选 state_changes，不直接修改 State。
    """

    def __init__(self, assets):
        self.assets = assets

    def inspect(self, state):
        loc = self.assets.get_location(state["player"]["location"])

        people = []
        for actor_id, actor in state.get("actors", {}).items():
            if actor.get("location") == loc["id"] and actor.get("present", True):
                asset = self.assets.get_character(actor_id)
                people.append(asset["name"])

        return {
            "location": loc["name"],
            "description": loc["description"],
            "people": people,
        }

    def move(self, state, destination_id):
        loc = self.assets.get_location(destination_id)
        return {
            "message": f"你前往了{loc['name']}。",
            "state_changes": [
                {"path": "player.location", "value": destination_id}
            ],
            "events": [f"玩家抵达{loc['name']}"]
        }

    def talk(self, state, target_id):
        asset = self.assets.get_character(target_id)
        actor = state.get("actors", {}).get(target_id)

        if actor is None:
            raise ValueError(f"{asset['name']}当前不是可交互 NPC。")

        if actor.get("location") != state["player"]["location"]:
            raise ValueError(f"{asset['name']}当前不在这里。")

        return {
            "message": f"你与{asset['name']}开始交谈。",
            "state_changes": [],
            "events": [f"玩家与{asset['name']}发生交谈"]
        }
