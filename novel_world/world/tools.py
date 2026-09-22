"""Deterministic candidate-action tools.

Tools validate the immediately knowable preconditions and return candidate
changes or resolution requests. They never mutate L3 state themselves and
never invent the outcome of an uncertain action.
"""

from __future__ import annotations

from copy import deepcopy
from numbers import Real


class ToolRegistry:
    """The program-side boundary for basic embodied actions."""

    POSTURES = {
        "standing": "standing", "站": "standing", "站立": "standing",
        "sitting": "sitting", "坐": "sitting", "坐下": "sitting",
        "crouching": "crouching", "蹲": "crouching", "蹲下": "crouching",
        "kneeling": "kneeling", "跪": "kneeling", "跪下": "kneeling",
        "lying": "lying", "躺": "lying", "躺下": "lying",
    }

    def __init__(self, assets):
        self.assets = assets

    @staticmethod
    def _result(message, *, state_changes=None, events=None, **requests):
        return {
            "message": message,
            "state_changes": state_changes or [],
            "events": events or [],
            **requests,
        }

    @staticmethod
    def _change(path, value, mechanism):
        return {"path": path, "value": value, "cause": {"mechanism": mechanism}}

    @staticmethod
    def _player(state):
        return state["player"]

    def _entity(self, state, entity_id):
        entity = state.get("entities", {}).get(entity_id)
        if entity is None:
            raise ValueError(f"{entity_id}不是当前 Runtime 中存在的物品或可操作对象。")
        return entity

    def _present_actor(self, state, actor_id):
        actor = state.get("actors", {}).get(actor_id)
        if actor is None or not actor.get("present", True):
            raise ValueError(f"{actor_id}当前不是可交互角色。")
        if actor.get("location") != self._player(state)["location"]:
            raise ValueError(f"{actor_id}当前不在这里。")
        return actor

    def _visible_entity(self, state, entity_id):
        entity = self._entity(state, entity_id)
        player = self._player(state)
        if entity.get("holder") == player.get("id"):
            return entity
        container_id = entity.get("contained_in")
        if container_id:
            container = self._entity(state, container_id)
            if container.get("location") != player["location"]:
                raise ValueError(f"{entity.get('name', entity_id)}当前不在可见或可触及范围内。")
            if container.get("openable") and not container.get("is_open", False):
                raise ValueError(f"{entity.get('name', entity_id)}被收在未打开的容器中。")
            return entity
        if entity.get("location") == player["location"] and not entity.get("holder"):
            return entity
        raise ValueError(f"{entity.get('name', entity_id)}当前不在可见或可触及范围内。")

    def _held_entity(self, state, entity_id):
        entity = self._entity(state, entity_id)
        player = self._player(state)
        if entity.get("holder") != player["id"] or entity_id not in player["held_items"]:
            raise ValueError(f"你当前没有正拿着{entity.get('name', entity_id)}。")
        return entity

    @staticmethod
    def _with_item(items, item_id):
        return [*items, item_id] if item_id not in items else list(items)

    @staticmethod
    def _without_item(items, item_id):
        return [item for item in items if item != item_id]

    def _player_item_changes(self, state, *, held=None, equipped=None):
        changes = []
        if held is not None:
            changes.append(self._change("player.held_items", held, "item_handling"))
        if equipped is not None:
            changes.append(self._change("player.equipped_items", equipped, "item_handling"))
        return changes

    # Perception ---------------------------------------------------------
    def look(self, state, target=None):
        return self._result("你尝试观察。", perception_requests=[{"kind": "look", "target": target}])

    def listen(self, state, target=None):
        return self._result("你尝试倾听。", perception_requests=[{"kind": "listen", "target": target}])

    def inspect(self, state, target=None):
        """Keep the old no-target scene inspection API for the existing Resolver."""
        if target is not None:
            self._visible_entity(state, target)
            return self._result("你开始仔细观察目标。", perception_requests=[{"kind": "inspect", "target": target}])

        loc = self.assets.get_location(self._player(state)["location"])
        people = []
        for actor_id, actor in state.get("actors", {}).items():
            if actor.get("location") == loc["id"] and actor.get("present", True):
                people.append(self.assets.get_character(actor_id)["name"])
        return {"location": loc["name"], "description": loc["description"], "people": people}

    def search(self, state, area, target=None):
        if area not in {self._player(state)["location"], "当前地点", "这里"}:
            self._visible_entity(state, area)
        if target:
            self._visible_entity(state, target)
        return self._result("你开始搜索。", perception_requests=[{"kind": "search", "area": area, "target": target}])

    # Movement -----------------------------------------------------------
    def move(self, state, destination_id, manner="walk"):
        loc = self.assets.get_location(destination_id)
        if not isinstance(manner, str) or not manner.strip():
            raise ValueError("移动方式必须是非空文本。")
        return self._result(
            f"你向{loc['name']}移动。",
            state_changes=[self._change("player.location", destination_id, "movement")],
            events=[f"玩家以{manner}方式前往{loc['name']}"],
        )

    def turn(self, state, direction_or_target):
        if not isinstance(direction_or_target, str) or not direction_or_target.strip():
            raise ValueError("朝向必须明确。")
        return self._result("你调整了朝向。", state_changes=[self._change("player.facing", direction_or_target, "turn")])

    def change_posture(self, state, posture):
        normalized = self.POSTURES.get(posture)
        if normalized is None:
            raise ValueError("姿态仅支持站、坐、蹲、跪、躺。")
        return self._result("你改变了姿态。", state_changes=[self._change("player.posture", normalized, "posture_change")])

    def wait(self, state, duration):
        if not isinstance(duration, Real) or isinstance(duration, bool) or duration <= 0:
            raise ValueError("等待时长必须是大于 0 的分钟数。")
        elapsed = state.get("world_time", {}).get("elapsed_minutes", 0)
        return self._result(
            f"你等待了{duration}分钟。",
            state_changes=[self._change("world_time.elapsed_minutes", elapsed + duration, "wait")],
            action_requests=[{"kind": "world_tick", "duration_minutes": duration}],
        )

    # Object operations --------------------------------------------------
    def take(self, state, object_id):
        entity = self._visible_entity(state, object_id)
        if not entity.get("portable", False):
            raise ValueError(f"{entity.get('name', object_id)}不能被拿起。")
        player = self._player(state)
        changes = [
            self._change(f"entities.{object_id}.holder", player["id"], "take"),
            self._change(f"entities.{object_id}.location", None, "take"),
            self._change(f"entities.{object_id}.contained_in", None, "take"),
            self._change("player.inventory", self._with_item(player["inventory"], object_id), "take"),
            *self._player_item_changes(state, held=self._with_item(player["held_items"], object_id)),
        ]
        if entity.get("contained_in"):
            container_id = entity["contained_in"]
            container = self._entity(state, container_id)
            changes.append(self._change(
                f"entities.{container_id}.contents",
                self._without_item(container.get("contents", []), object_id),
                "take",
            ))
        return self._result(
            f"你拿起了{entity.get('name', object_id)}。",
            state_changes=changes,
        )

    def release(self, state, object_id):
        entity = self._held_entity(state, object_id)
        player = self._player(state)
        return self._result(
            f"你放开了{entity.get('name', object_id)}。",
            state_changes=[
                self._change(f"entities.{object_id}.holder", None, "release"),
                self._change(f"entities.{object_id}.location", player["location"], "release"),
                self._change("player.inventory", self._without_item(player["inventory"], object_id), "release"),
                *self._player_item_changes(
                    state,
                    held=self._without_item(player["held_items"], object_id),
                    equipped=self._without_item(player["equipped_items"], object_id),
                ),
            ],
        )

    def place(self, state, object_id, destination):
        entity = self._held_entity(state, object_id)
        player = self._player(state)
        changes = [
            self._change(f"entities.{object_id}.holder", None, "place"),
            self._change(f"entities.{object_id}.location", player["location"], "place"),
            self._change(f"entities.{object_id}.contained_in", None, "place"),
            self._change("player.inventory", self._without_item(player["inventory"], object_id), "place"),
            *self._player_item_changes(
                state,
                held=self._without_item(player["held_items"], object_id),
                equipped=self._without_item(player["equipped_items"], object_id),
            ),
        ]
        if destination not in {"ground", "地上", "地面"}:
            surface = self._visible_entity(state, destination)
            if not (surface.get("container") or surface.get("surface")):
                raise ValueError(f"{surface.get('name', destination)}不能放置物品。")
            if surface.get("openable") and not surface.get("is_open", False):
                raise ValueError(f"{surface.get('name', destination)}尚未打开。")
            changes.extend([
                self._change(f"entities.{object_id}.contained_in", destination, "place"),
                self._change(f"entities.{destination}.contents", self._with_item(surface.get("contents", []), object_id), "place"),
            ])
        return self._result(f"你放下了{entity.get('name', object_id)}。", state_changes=changes)

    def transfer(self, state, object_id, target_id):
        entity = self._held_entity(state, object_id)
        actor = self._present_actor(state, target_id)
        player = self._player(state)
        return self._result(
            f"你将{entity.get('name', object_id)}交给了{target_id}。",
            state_changes=[
                self._change(f"entities.{object_id}.holder", target_id, "transfer"),
                self._change(f"entities.{object_id}.location", None, "transfer"),
                self._change("player.inventory", self._without_item(player["inventory"], object_id), "transfer"),
                self._change(f"actors.{target_id}.inventory", self._with_item(actor["inventory"], object_id), "transfer"),
                *self._player_item_changes(state, held=self._without_item(player["held_items"], object_id)),
            ],
        )

    def open(self, state, target_id):
        entity = self._visible_entity(state, target_id)
        if not entity.get("openable", False):
            raise ValueError(f"{entity.get('name', target_id)}不能打开。")
        if entity.get("is_open", False):
            raise ValueError(f"{entity.get('name', target_id)}已经打开。")
        return self._result(f"你打开了{entity.get('name', target_id)}。", state_changes=[self._change(f"entities.{target_id}.is_open", True, "open")])

    def close(self, state, target_id):
        entity = self._visible_entity(state, target_id)
        if not entity.get("openable", False):
            raise ValueError(f"{entity.get('name', target_id)}不能关闭。")
        if not entity.get("is_open", False):
            raise ValueError(f"{entity.get('name', target_id)}已经关闭。")
        return self._result(f"你关闭了{entity.get('name', target_id)}。", state_changes=[self._change(f"entities.{target_id}.is_open", False, "close")])

    def use(self, state, object_id, target=None):
        entity = self._visible_entity(state, object_id)
        affordances = entity.get("affordances", [])
        if not affordances:
            raise ValueError(f"{entity.get('name', object_id)}没有已定义的正常用途。")
        return self._result(
            f"你尝试使用{entity.get('name', object_id)}。",
            action_requests=[{"kind": "use", "object": object_id, "target": target, "affordances": deepcopy(affordances)}],
        )

    def equip(self, state, object_id):
        entity = self._entity(state, object_id)
        player = self._player(state)
        if object_id not in player["inventory"] or entity.get("holder") != player["id"]:
            raise ValueError(f"你当前没有持有{entity.get('name', object_id)}。")
        if not entity.get("equippable", False):
            raise ValueError(f"{entity.get('name', object_id)}不能装备。")
        return self._result(
            f"你装备了{entity.get('name', object_id)}。",
            state_changes=self._player_item_changes(state, equipped=self._with_item(player["equipped_items"], object_id)),
        )

    def store(self, state, object_id, container_id):
        entity = self._held_entity(state, object_id)
        container = self._visible_entity(state, container_id)
        if not container.get("container", False):
            raise ValueError(f"{container.get('name', container_id)}不是容器。")
        if container.get("openable") and not container.get("is_open", False):
            raise ValueError(f"{container.get('name', container_id)}尚未打开。")
        player = self._player(state)
        return self._result(
            f"你将{entity.get('name', object_id)}收进{container.get('name', container_id)}。",
            state_changes=[
                self._change(f"entities.{object_id}.holder", None, "store"),
                self._change(f"entities.{object_id}.location", player["location"], "store"),
                self._change(f"entities.{object_id}.contained_in", container_id, "store"),
                self._change(f"entities.{container_id}.contents", self._with_item(container.get("contents", []), object_id), "store"),
                self._change("player.inventory", self._without_item(player["inventory"], object_id), "store"),
                *self._player_item_changes(
                    state,
                    held=self._without_item(player["held_items"], object_id),
                    equipped=self._without_item(player["equipped_items"], object_id),
                ),
            ],
        )

    # Mechanics and defense ---------------------------------------------
    def _physical_request(self, state, kind, target, **details):
        if target in state.get("entities", {}):
            self._visible_entity(state, target)
        elif target in state.get("actors", {}):
            self._present_actor(state, target)
        return self._result("动作已提交给后续裁决。", action_requests=[{"kind": kind, "target": target, **details}])

    def push(self, state, target, force):
        return self._physical_request(state, "push", target, force=force)

    def pull(self, state, target, force):
        return self._physical_request(state, "pull", target, force=force)

    def grab(self, state, target):
        result = self._physical_request(state, "grab", target)
        result["state_changes"] = [self._change("player.grabbed_target", target, "grab")]
        return result

    def throw(self, state, object_id, target_or_direction):
        entity = self._held_entity(state, object_id)
        return self._result(
            f"你尝试投出{entity.get('name', object_id)}。",
            action_requests=[{"kind": "throw", "object": object_id, "target_or_direction": target_or_direction}],
        )

    def strike(self, state, target, instrument=None, manner=None):
        if instrument is not None:
            self._held_entity(state, instrument)
        return self._physical_request(state, "strike", target, instrument=instrument, manner=manner)

    def block(self, state, source):
        return self._result("你尝试格挡。", action_requests=[{"kind": "block", "source": source}])

    def dodge(self, state, source_or_direction):
        return self._result("你尝试闪避。", action_requests=[{"kind": "dodge", "source_or_direction": source_or_direction}])

    # Communication and information -------------------------------------
    def speak(self, state, content, target=None):
        if target is not None:
            self._present_actor(state, target)
        if not isinstance(content, str) or not content.strip():
            raise ValueError("说话内容不能为空。")
        return self._result("你开口说话。", action_requests=[{"kind": "speak", "content": content, "target": target}])

    def gesture(self, state, gesture_type, target=None):
        if target is not None:
            self._present_actor(state, target)
        return self._result("你做出了示意动作。", action_requests=[{"kind": "gesture", "type": gesture_type, "target": target}])

    def write(self, state, content, medium_id):
        medium = self._visible_entity(state, medium_id)
        if not medium.get("writable", False):
            raise ValueError(f"{medium.get('name', medium_id)}不能书写。")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("书写内容不能为空。")
        return self._result("你留下了文字。", state_changes=[self._change(f"entities.{medium_id}.content", content, "write")])

    def read(self, state, target_id):
        target = self._visible_entity(state, target_id)
        if not target.get("readable", False):
            raise ValueError(f"{target.get('name', target_id)}没有可阅读的文字。")
        return self._result("你开始阅读。", perception_requests=[{"kind": "read", "target": target_id}])

    # Backward-compatible name used by the current talk Resolver branch.
    def talk(self, state, target_id):
        asset = self.assets.get_character(target_id)
        self._present_actor(state, target_id)
        return self._result(f"你与{asset['name']}开始交谈。", events=[f"玩家与{asset['name']}发生交谈"])
