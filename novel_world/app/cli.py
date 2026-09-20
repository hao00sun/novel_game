from __future__ import annotations

import json

from ..characters.factory import CharacterFactory, STAT_KEYS
from .bootstrap import SAVE_PATH, build_engine


STAT_ZH = {
    "physique": "体魄",
    "agility": "身法",
    "intellect": "心智",
    "perception": "洞察",
    "social": "交涉",
    "will": "意志",
}


def print_character(c):
    stats = " / ".join(
        f"{STAT_ZH[k]}:{v}" for k, v in c["stats"].items()
    )
    print(f"{c['id']:16} {c['name']}｜{c['identity']}｜{stats}")


def choose_character(assets):
    bundle = assets.characters_bundle()
    factory = CharacterFactory(bundle)

    print("\n可选择预设角色：")
    for c in assets.selectable_characters():
        print_character(c)

    print("\n输入角色 id 选择预设角色；输入 custom 创建自建角色。")

    while True:
        choice = input("角色 > ").strip()

        if choice == "custom":
            return create_custom(factory, assets.scene()["entry_location"])

        try:
            asset = assets.get_character(choice)
            return factory.from_preset(asset)
        except (KeyError, ValueError) as e:
            print(e)


def create_custom(factory, entry_location):
    print("\n创建自建角色。总属性预算 30，每项 1~8。")
    name = input("姓名 > ").strip() or "无名"
    identity = input(
        "身份（平民/流民/学徒/行商/读书人/手艺人/猎户/脚夫/江湖客） > "
    ).strip()

    while True:
        stats = {}
        try:
            for key in STAT_KEYS:
                stats[key] = int(input(f"{STAT_ZH[key]} > ").strip())

            return factory.create_custom(
                name=name,
                identity=identity,
                stats=stats,
                location=entry_location,
            )
        except ValueError as e:
            print(f"创建失败：{e}")
            print("请重新输入全部属性。\n")


def main():
    constitution, assets, llm, engine = build_engine()

    print("=" * 70)
    print("Novel World v0.3 API Experience — 澄源县")
    print("=" * 70)
    print(
        f"L0: {constitution.manifest['skill_id']} "
        f"v{constitution.manifest['version']}"
    )
    print(f"LLM Provider: {llm.provider_name}")
    print("配置 Provider：python -m novel_world --configure")

    if not SAVE_PATH.exists():
        player = choose_character(assets)
        state = engine.create_state(player)
        print(f"\n已创建角色：{player['name']}（{player['identity']}）")
    else:
        state = engine.get_state()
        print(
            f"已读取存档：{state['player']['name']}（{state['player']['identity']}）"
        )

    print("\n命令：")
    print("  /where     当前地点")
    print("  /people    当前地点人物")
    print("  /me        玩家状态")
    print("  /state     简要 Runtime State")
    print("  /reset     删除存档")
    print("  quit       退出")
    print()
    print("API 模式下可尝试：")
    print("  去药铺")
    print("  和沈青禾聊聊，问她最近县里有没有反常的事")
    print("  去茶摊打听最近来的外乡人")
    print("  我命令沈青禾立刻把药铺送给我")
    print("  我用轻功跃上屋顶")
    print()

    while True:
        text = input("> ").strip()

        if not text:
            continue

        if text in {"quit", "exit"}:
            break

        state = engine.get_state()

        if text == "/where":
            loc = assets.get_location(state["player"]["location"])
            print(f"{loc['name']}：{loc['description']}")
            continue

        if text == "/people":
            here = state["player"]["location"]
            found = []
            for actor_id, actor in state.get("actors", {}).items():
                if actor.get("location") == here and actor.get("present", True):
                    c = assets.get_character(actor_id)
                    found.append(c)
            if not found:
                print("这里暂时没有明确人物。")
            else:
                for c in found:
                    print(f"- {c['name']}｜{c['identity']}")
            continue

        if text == "/me":
            print(json.dumps(state["player"], ensure_ascii=False, indent=2))
            continue

        if text == "/state":
            summary = {
                "turn": state["turn"],
                "player_location": state["player"]["location"],
                "recent_events": state.get("events", [])[-8:],
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            continue

        if text == "/reset":
            engine.store.delete()
            print("存档已删除。重新运行即可重新创建角色。")
            break

        intent, outcome, new_state, narrative = engine.step(text)

        print()
        print(narrative)
        print()
        print(
            f"[debug] intent={intent.kind} | turn={new_state['turn']} | "
            f"location={new_state['player']['location']}"
        )


if __name__ == "__main__":
    main()
