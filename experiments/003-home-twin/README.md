# Home Twin - A Local Connected Home Simulator

## Overview

Home Twin is a lightweight simulator for testing connected home automations without requiring physical devices. It provides synthetic entities (lights, sensors, presence detectors, etc.) that can be programmatically controlled and observed.

## Features

- **Synthetic Entities**: Create lights, sensors, presence detectors, and custom entity types
- **State Management**: Full state tracking with availability support
- **Deterministic Scenarios**: Replay scripted scenarios for reproducible testing
- **Scenario Persistence**: Export/import scenarios for sharing and regression testing
- **Availability Simulation**: Handle entity unavailability gracefully (network issues, power loss, etc.)
- **Resettable Runs**: Restore all entities to their copied initial state between simulations
- **Dynamic Entities**: Remove entities cleanly, including their references in saved and current scenarios
- **Entity Renaming**: Change an entity ID without losing its type, state, or reset behavior
- **Entity Discovery**: List entity IDs globally or by type in deterministic order, and count current entities
- **Entity Type Metrics**: Get a deterministic, isolated count of entities grouped by type
- **Availability Discovery**: List currently available or unavailable entity IDs in deterministic order, and count them
- **Availability Metrics**: Get current available-entity counts grouped by type
- **Availability Summaries**: Get total, available, and unavailable counts grouped by type

## Installation

```bash
cd experiments/003-home-twin
python -m pytest tests/ -v
```

## Quick Start

```python
from home_twin import HomeTwin

# Create a home
home = HomeTwin()

# Add entities
home.add_entity("living_room_light", "light", {"brightness": 0, "available": True})
home.add_entity("motion_sensor", "sensor", {"motion": False, "available": True})
home.add_entity("presence", "presence", {"home": False, "available": True})

# Simulate events
home.set_state("presence", {"home": True})
home.set_state("motion_sensor", {"motion": True})

# Automation would turn on the light
home.set_state("living_room_light", {"brightness": 100})

# Check state
print(home.get_state())

# Replay a deterministic scenario
scenario = [
    (0, "sensor", {"motion": True}),
    (1, "light", {"brightness": 50}),
    (2, "light", {"brightness": 100}),
    (3, "sensor", {"motion": False}),
    (4, "light", {"brightness": 0}),
]
home.replay_scenario(scenario)

# Export/import scenarios for reproducibility
exported = home.export_scenario("morning_routine")
# ... later or in another process ...
home2 = HomeTwin()
home2.add_entity("light", "light", {"brightness": 0, "available": True})
home2.import_scenario(exported)
home2.replay_scenario(exported["morning_routine"])
# Or replay an imported scenario directly by name
home2.replay_saved_scenario("morning_routine")

# Or save the current replay directly for later listing/replay
home.save_scenario("morning_routine")
```

## API Reference

### `HomeTwin`

Main simulator class.

#### `add_entity(entity_id: str, entity_type: str, initial_state: dict | None = None) -> None`

Add a new entity to the home twin.

- `entity_id`: Unique identifier (e.g., "living_room_light")
- `entity_type`: Type string (e.g., "light", "sensor", "presence")
- `initial_state`: Optional initial state dictionary

#### `set_state(entity_id: str, changes: dict[str, Any]) -> None`

Update an entity's state. If entity is unavailable, changes are ignored.

#### `remove_entity(entity_id: str) -> None`

Remove an entity and its initial-state snapshot. Raises `ValueError` when the entity is unknown.

#### `rename_entity(entity_id: str, new_entity_id: str) -> None`

Rename an entity while preserving its type, current state, and initial-state snapshot. Raises `ValueError` when the source is unknown or the destination already exists.

#### `get_state() -> dict[str, dict[str, Any]]`

Get current state of all entities.

#### `list_entities(entity_type: str | None = None) -> list[str]`

Return entity IDs sorted alphabetically. When `entity_type` is provided, only matching entities are returned.

#### `count_entities(entity_type: str | None = None) -> int`

Return the number of entities currently in the twin. When `entity_type` is provided, only matching entities are counted.

#### `count_entities_by_type() -> dict[str, int]`

Return a new dictionary containing the current number of entities for each entity type, ordered by type.

#### `count_available_entities(entity_type: str | None = None) -> int`

Return the number of currently available entities. When `entity_type` is provided, only matching entities are counted.

#### `count_available_entities_by_type() -> dict[str, int]`

Return current available-entity counts grouped by type, ordered by type.

#### `count_unavailable_entities(entity_type: str | None = None) -> int`

Return the number of currently unavailable entities. When `entity_type` is provided, only matching entities are counted.

#### `count_unavailable_entities_by_type() -> dict[str, int]`

Return current unavailable-entity counts grouped by type, ordered by type.

#### `availability_summary_by_type() -> dict[str, dict[str, int]]`

Return total, available, and unavailable entity counts grouped by type, ordered by type. The returned nested dictionaries are independent from internal state.

#### `availability_summary() -> dict[str, int]`

Return total, available, and unavailable entity counts for the whole home.

#### `list_available_entities(entity_type: str | None = None) -> list[str]`

Return currently available entity IDs sorted alphabetically, optionally limited to one entity type. Entities without an explicit availability state are considered available.

#### `list_unavailable_entities(entity_type: str | None = None) -> list[str]`

Return currently unavailable entity IDs sorted alphabetically, optionally limited to one entity type. Entities without an explicit availability state are considered available.

#### `get_entity_state(entity_id: str) -> dict[str, Any]`

Get an isolated copy of one entity's state. Raises `KeyError` when the entity is unknown.

#### `get_entity_type(entity_id: str) -> str`

Get one entity's type without exposing internal entity storage. Raises `KeyError` when the entity is unknown.

#### `replay_scenario(scenario: list[tuple[int, str, dict[str, Any]]]) -> list[tuple[int, str, dict[str, Any]]]`

Replay a deterministic scenario. Returns list of applied events.

Scenario format: list of `(time_step, entity_id, state_changes)` tuples.

#### `export_scenario(name: str) -> dict[str, list[tuple[int, str, dict[str, Any]]]]`

Export the last replayed scenario by name.

#### `import_scenario(scenario_data: dict[str, list[tuple[int, str, dict[str, Any]]]]) -> None`

Import scenarios from exported data.

#### `save_scenario(name: str) -> dict[str, list[tuple[int, str, dict[str, Any]]]]`

Save the last replayed scenario under `name` and return an isolated export.

#### `list_saved_scenarios() -> list[str]`

Return imported scenario names sorted alphabetically. The returned list is independent from internal storage.

#### `has_saved_scenario(name: str) -> bool`

Return whether a saved scenario exists, without raising an exception for a missing name.

#### `get_saved_scenario(name: str) -> list[tuple[int, str, dict[str, Any]]]`

Return an isolated copy of a saved scenario. Raises `KeyError` when the name is unknown.

#### `remove_saved_scenario(name: str) -> None`

Remove a saved scenario by name. Raises `KeyError` when the name is unknown.

#### `rename_saved_scenario(name: str, new_name: str) -> None`

Rename a saved scenario without overwriting an existing scenario. Raises `KeyError` when the source is unknown or the destination already exists.

#### `replay_saved_scenario(name: str) -> list[tuple[int, str, dict[str, Any]]]`

Replay an imported scenario by name. Raises `KeyError` when the name is unknown.

#### `clear_saved_scenarios() -> list[str]`

Remove every saved scenario without changing entity state or replay history. Returns removed scenario names sorted alphabetically.

## Testing

```bash
python -m pytest tests/ -v
```

All tests pass with 100% coverage of core functionality.

## Status

`validated` - Core functionality complete and tested.