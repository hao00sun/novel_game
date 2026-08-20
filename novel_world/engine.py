from __future__ import annotations

from copy import deepcopy


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

        self.constitution.assert_world_compatible(self.assets.world())

    def _initial_actors(self, player_id):
        actors = {}
        for c in self.assets.characters():
            if c["id"] == player_id:
                continue

            profile = c.get("agent_profile", {})
            actors[c["id"]] = {
                "location": c["location"],
                "present": True,
                "goals": deepcopy(profile.get("goals", [])),
                "beliefs": deepcopy(profile.get("beliefs", [])),
                "emotion": deepcopy(profile.get("emotion", {"state": "平静"})),
                "relationship_context": deepcopy(
                    profile.get("relationship_context", [])
                ),
                "memory": [],
            }
        return actors

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

        # L4
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
