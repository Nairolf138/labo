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

    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity and its initial-state snapshot from the twin."""
        if entity_id not in self.entities:
            raise ValueError(f"Entity {entity_id} not found")
        del self.entities[entity_id]
        del self._initial_states[entity_id]
        self._last_replayed_scenario = [
            event
            for event in self._last_replayed_scenario
            if event[1] != entity_id
        ]
        self.scenarios = {
            name: [event for event in events if event[1] != entity_id]
            for name, events in self.scenarios.items()
        }

    def rename_entity(self, entity_id: str, new_entity_id: str) -> None:
        """Rename an entity without losing its type, state, or reset snapshot."""
        if entity_id not in self.entities:
            raise ValueError(f"Entity {entity_id} not found")
        if entity_id == new_entity_id:
            return
        if new_entity_id in self.entities:
            raise ValueError(f"Entity {new_entity_id} already exists")

        entity = self.entities.pop(entity_id)
        entity.entity_id = new_entity_id
        self.entities[new_entity_id] = entity
        self._initial_states[new_entity_id] = self._initial_states.pop(entity_id)
        self._last_replayed_scenario = [
            (time_step, new_entity_id if event_entity_id == entity_id else event_entity_id, changes)
            for time_step, event_entity_id, changes in self._last_replayed_scenario
        ]
        self.scenarios = {
            name: [
                (
                    time_step,
                    new_entity_id if event_entity_id == entity_id else event_entity_id,
                    changes,
                )
                for time_step, event_entity_id, changes in events
            ]
            for name, events in self.scenarios.items()
        }

    def set_state(self, entity_id: str, changes: dict[str, Any]) -> None:
        """Set state for an entity."""
        if entity_id not in self.entities:
            raise ValueError(f"Entity {entity_id} not found")
        self.entities[entity_id].update_state(changes)

    def get_state(self) -> dict[str, dict[str, Any]]:
        """Get state of all entities."""
        return {eid: entity.get_state() for eid, entity in self.entities.items()}

    def list_entities(self, entity_type: str | None = None) -> list[str]:
        """Return entity IDs, optionally filtered by type, in sorted order."""
        entity_ids = (
            entity.entity_id
            for entity in self.entities.values()
            if entity_type is None or entity.entity_type == entity_type
        )
        return sorted(entity_ids)

    def list_entity_types(self) -> list[str]:
        """Return the distinct entity types currently present, in sorted order."""
        return sorted({entity.entity_type for entity in self.entities.values()})

    def list_available_entities(self, entity_type: str | None = None) -> list[str]:
        """Return available entity IDs, optionally filtered by type, sorted."""
        return sorted(
            entity.entity_id
            for entity in self.entities.values()
            if entity.state.get("available", True)
            and (entity_type is None or entity.entity_type == entity_type)
        )

    def list_unavailable_entities(self, entity_type: str | None = None) -> list[str]:
        """Return unavailable entity IDs, optionally filtered by type, sorted."""
        return sorted(
            entity.entity_id
            for entity in self.entities.values()
            if not entity.state.get("available", True)
            and (entity_type is None or entity.entity_type == entity_type)
        )

    def count_entities(self, entity_type: str | None = None) -> int:
        """Return the number of entities, optionally filtered by type."""
        if entity_type is None:
            return len(self.entities)
        return sum(entity.entity_type == entity_type for entity in self.entities.values())

    def count_available_entities(self, entity_type: str | None = None) -> int:
        """Return the number of available entities, optionally filtered by type."""
        return len(self.list_available_entities(entity_type=entity_type))

    def has_entity(self, entity_id: str) -> bool:
        """Return whether an entity currently exists in the home twin."""
        return entity_id in self.entities

    def get_entity_state(self, entity_id: str) -> dict[str, Any]:
        """Get an isolated copy of one entity's state."""
        if entity_id not in self.entities:
            raise KeyError(f"Entity {entity_id!r} not found")
        return self.entities[entity_id].get_state()

    def get_entity_type(self, entity_id: str) -> str:
        """Get the type of one entity without exposing the entity object."""
        if entity_id not in self.entities:
            raise KeyError(f"Entity {entity_id!r} not found")
        return self.entities[entity_id].entity_type

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

    def has_saved_scenario(self, name: str) -> bool:
        """Return whether a saved scenario currently exists."""
        return name in self.scenarios

    def get_saved_scenario(self, name: str) -> list[tuple[int, str, dict[str, Any]]]:
        """Return an isolated copy of a saved scenario by name."""
        if name not in self.scenarios:
            raise KeyError(f"Scenario {name!r} not found")
        return copy.deepcopy(self.scenarios[name])

    def remove_saved_scenario(self, name: str) -> None:
        """Remove a saved scenario by name."""
        if name not in self.scenarios:
            raise KeyError(f"Scenario {name!r} not found")
        del self.scenarios[name]

    def clear_saved_scenarios(self) -> list[str]:
        """Remove every saved scenario and return removed names in sorted order."""
        removed = sorted(self.scenarios)
        self.scenarios.clear()
        return removed

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