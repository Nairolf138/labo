"""Home Twin - A local connected home simulator for testing automations."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    """A synthetic entity in the home twin."""

    entity_id: str
    entity_type: str  # light, sensor, presence, etc.
    state: dict[str, Any] = field(default_factory=dict)

    def update_state(self, changes: dict[str, Any]) -> None:
        """Update entity state with new values."""
        if not self.state.get("available", True) and changes.get("available") is not True:
            return
        self.state.update(copy.deepcopy(changes))

    def get_state(self) -> dict[str, Any]:
        """Get a copy of the current state."""
        return copy.deepcopy(self.state)


class HomeTwin:
    """Simulator for a connected home with synthetic entities."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.scenarios: dict[str, list[tuple[int, str, dict[str, Any]]]] = {}
        self._initial_states: dict[str, dict[str, Any]] = {}
        self._last_replayed_scenario: list[tuple[int, str, dict[str, Any]]] = []

    def add_entity(
        self, entity_id: str, entity_type: str, initial_state: dict[str, Any] | None = None
    ) -> None:
        """Add a new entity to the home twin."""
        if entity_id in self.entities:
            raise ValueError(f"Entity {entity_id} already exists")
        state = copy.deepcopy(initial_state) if initial_state is not None else {}
        state.setdefault("available", True)
        self.entities[entity_id] = Entity(entity_id=entity_id, entity_type=entity_type, state=state)
        self._initial_states[entity_id] = copy.deepcopy(state)

    def reset(self) -> None:
        """Restore all entities and clear the current replay history."""
        for entity_id, entity in self.entities.items():
            entity.state = copy.deepcopy(self._initial_states[entity_id])
        self._last_replayed_scenario = []

    def set_state(self, entity_id: str, changes: dict[str, Any]) -> None:
        """Set state for an entity."""
        if entity_id not in self.entities:
            raise ValueError(f"Entity {entity_id} not found")
        self.entities[entity_id].update_state(changes)

    def get_state(self) -> dict[str, dict[str, Any]]:
        """Get state of all entities."""
        return {eid: entity.get_state() for eid, entity in self.entities.items()}

    def get_entity_state(self, entity_id: str) -> dict[str, Any]:
        """Get an isolated copy of one entity's state."""
        if entity_id not in self.entities:
            raise KeyError(f"Entity {entity_id!r} not found")
        return self.entities[entity_id].get_state()

    def replay_scenario(
        self, scenario: list[tuple[int, str, dict[str, Any]]]
    ) -> list[tuple[int, str, dict[str, Any]]]:
        """Replay a deterministic scenario and return the events applied."""
        events = []
        for time_step, entity_id, changes in scenario:
            if entity_id in self.entities:
                self.entities[entity_id].update_state(changes)
            events.append((time_step, entity_id, changes))
        self._last_replayed_scenario = copy.deepcopy(events)
        return copy.deepcopy(events)

    def export_scenario(self, name: str) -> dict[str, list[tuple[int, str, dict[str, Any]]]]:
        """Export the last replayed scenario by name."""
        return {name: copy.deepcopy(self._last_replayed_scenario)}

    def save_scenario(self, name: str) -> dict[str, list[tuple[int, str, dict[str, Any]]]]:
        """Save and return the last replayed scenario under ``name``."""
        exported = self.export_scenario(name)
        self.import_scenario(exported)
        return exported

    def import_scenario(self, scenario_data: dict[str, list[tuple[int, str, dict[str, Any]]]]) -> None:
        """Import scenarios from exported data."""
        self.scenarios.update(copy.deepcopy(scenario_data))

    def list_saved_scenarios(self) -> list[str]:
        """Return saved scenario names in deterministic order."""
        return sorted(self.scenarios)

    def replay_saved_scenario(
        self, name: str
    ) -> list[tuple[int, str, dict[str, Any]]]:
        """Replay an imported scenario by name."""
        if name not in self.scenarios:
            raise KeyError(f"Scenario {name!r} not found")
        return self.replay_scenario(self.scenarios[name])


if __name__ == "__main__":
    # Simple demo
    home = HomeTwin()
    home.add_entity("light", "light", {"brightness": 0, "available": True})
    home.add_entity("sensor", "sensor", {"motion": False, "available": True})

    print("Initial state:", home.get_state())

    home.set_state("sensor", {"motion": True})
    print("After motion:", home.get_state())

    home.set_state("light", {"brightness": 100})
    print("After light on:", home.get_state())