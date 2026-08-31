'''




'''


from __future__ import annotations

from copy import deepcopy


class StateManager:
    """
    L3 唯一写入口。

    v0.2 增加层级保护：
    Runtime State 只能修改 L3 数据，不能借 path 反向修改 L0/L1/L2。
    """

    RESERVED_ROOTS = {
        "constitution",
        "world_rules",
        "assets",
        "asset_definitions",
    }

    def apply(self, state, outcome):
        new_state = deepcopy(state)

        for change in outcome.state_changes:
            self._validate_path(change["path"])
            self._set_path(new_state, change["path"], change["value"])

        if outcome.events:
            new_state.setdefault("events", []).extend(outcome.events)

        new_state["turn"] = new_state.get("turn", 0) + 1
        return new_state

    def _validate_path(self, path):
        root = path.split(".", 1)[0]
        if root in self.RESERVED_ROOTS:
            raise PermissionError(
                f"Runtime State 不允许修改上层定义：{path}"
            )

        if path.startswith("_meta.constitution"):
            raise PermissionError("Runtime 不允许修改 Constitution 引用。")

    def _set_path(self, obj, path, value):
        parts = path.split(".")
        cursor = obj
        for key in parts[:-1]:
            cursor = cursor.setdefault(key, {})
        cursor[parts[-1]] = value
