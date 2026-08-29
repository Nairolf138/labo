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

#### `get_state() -> dict[str, dict[str, Any]]`

Get current state of all entities.

#### `get_entity_state(entity_id: str) -> dict[str, Any]`

Get an isolated copy of one entity's state. Raises `KeyError` when the entity is unknown.

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

#### `replay_saved_scenario(name: str) -> list[tuple[int, str, dict[str, Any]]]`

Replay an imported scenario by name. Raises `KeyError` when the name is unknown.

## Testing

```bash
python -m pytest tests/ -v
```

All tests pass with 100% coverage of core functionality.

## Status

`validated` - Core functionality complete and tested.