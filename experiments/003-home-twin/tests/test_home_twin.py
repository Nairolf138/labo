"""Behavior tests for the Home Twin experiment."""

from pathlib import Path
import sys
import unittest

SRC = Path(__file__).parents[1] / "src"
sys.path.insert(0, str(SRC))

import home_twin  # noqa: E402


class HomeTwinTest(unittest.TestCase):
    """Tests for the Home Twin experiment."""

    def test_simulates_presence_light_and_availability(self) -> None:
        """Simulate presence, brightness and availability, then replay a deterministic scenario."""
        # Create a home with synthetic entities
        home = home_twin.HomeTwin()

        # Add entities
        home.add_entity("living_room_light", "light", {"brightness": 0, "available": True})
        home.add_entity("motion_sensor", "sensor", {"motion": False, "available": True})
        home.add_entity("presence_simulator", "presence", {"home": False, "available": True})

        # Initial state
        state = home.get_state()
        self.assertEqual(state["living_room_light"]["brightness"], 0)
        self.assertFalse(state["motion_sensor"]["motion"])
        self.assertFalse(state["presence_simulator"]["home"])

        # Simulate presence arriving
        home.set_state("presence_simulator", {"home": True})
        state = home.get_state()
        self.assertTrue(state["presence_simulator"]["home"])

        # Simulate motion detected
        home.set_state("motion_sensor", {"motion": True})
        state = home.get_state()
        self.assertTrue(state["motion_sensor"]["motion"])

        # Simulate light turning on (automation would do this)
        home.set_state("living_room_light", {"brightness": 100})
        state = home.get_state()
        self.assertEqual(state["living_room_light"]["brightness"], 100)

        # Simulate presence leaving
        home.set_state("presence_simulator", {"home": False})
        state = home.get_state()
        self.assertFalse(state["presence_simulator"]["home"])

        # Simulate motion stopping
        home.set_state("motion_sensor", {"motion": False})
        state = home.get_state()
        self.assertFalse(state["motion_sensor"]["motion"])

        # Light turns off
        home.set_state("living_room_light", {"brightness": 0})
        state = home.get_state()
        self.assertEqual(state["living_room_light"]["brightness"], 0)

    def test_replay_deterministic_scenario(self) -> None:
        """Replay a deterministic scenario from a script."""
        home = home_twin.HomeTwin()

        home.add_entity("light", "light", {"brightness": 0, "available": True})
        home.add_entity("sensor", "sensor", {"motion": False, "available": True})

        # Define a scenario as a list of (time, entity, state_changes)
        scenario = [
            (0, "sensor", {"motion": True}),
            (1, "light", {"brightness": 50}),
            (2, "light", {"brightness": 100}),
            (3, "sensor", {"motion": False}),
            (4, "light", {"brightness": 0}),
        ]

        # Replay the scenario
        events = home.replay_scenario(scenario)

        # Verify the final state
        state = home.get_state()
        self.assertEqual(state["light"]["brightness"], 0)
        self.assertFalse(state["sensor"]["motion"])

        # Verify events were recorded
        self.assertEqual(len(events), 5)
        self.assertEqual(events[0], (0, "sensor", {"motion": True}))
        self.assertEqual(events[-1], (4, "light", {"brightness": 0}))

    def test_add_entity_isolates_initial_state(self) -> None:
        """External mutations must not alter the twin's stored state."""
        initial_state = {"brightness": 25}
        home = home_twin.HomeTwin()

        home.add_entity("light", "light", initial_state)
        initial_state["brightness"] = 100
        initial_state["external"] = True

        self.assertEqual(home.get_state()["light"]["brightness"], 25)
        self.assertNotIn("external", home.get_state()["light"])

    def test_exported_scenario_is_isolated(self) -> None:
        """Exported scenarios must not share mutable event data with the twin."""
        home = home_twin.HomeTwin()
        home.add_entity("light", "light", {"brightness": 0})
        source_changes = {"brightness": 100, "metadata": {"source": "test"}}
        home.replay_scenario([(0, "light", source_changes)])

        exported = home.export_scenario("test_scenario")
        exported["test_scenario"][0][2]["metadata"]["source"] = "external"

        self.assertEqual(home.export_scenario("test_scenario")["test_scenario"][0][2]["metadata"]["source"], "test")

    def test_entity_unavailability(self) -> None:
        """Handle entity unavailability gracefully."""
        home = home_twin.HomeTwin()

        home.add_entity("unreliable_light", "light", {"brightness": 0, "available": True})

        # Mark as unavailable
        home.set_state("unreliable_light", {"available": False})

        state = home.get_state()
        self.assertFalse(state["unreliable_light"]["available"])

        # Attempting to change state of unavailable entity should be tracked
        home.set_state("unreliable_light", {"brightness": 100})

        # State should not change when unavailable
        state = home.get_state()
        self.assertEqual(state["unreliable_light"]["brightness"], 0)

    def test_scenario_persistence(self) -> None:
        """Save and load scenarios for reproducibility."""
        home = home_twin.HomeTwin()

        home.add_entity("light", "light", {"brightness": 0, "available": True})

        scenario = [
            (0, "light", {"brightness": 100}),
            (1, "light", {"brightness": 0}),
        ]

        home.replay_scenario(scenario)

        # Export scenario
        exported = home.export_scenario("test_scenario")
        self.assertIn("test_scenario", exported)
        self.assertEqual(len(exported["test_scenario"]), 2)

        # Create new home and import
        home2 = home_twin.HomeTwin()
        home2.add_entity("light", "light", {"brightness": 0, "available": True})
        home2.import_scenario(exported)

        events = home2.replay_scenario(exported["test_scenario"])
        self.assertEqual(len(events), 2)

        state = home2.get_state()
        self.assertEqual(state["light"]["brightness"], 0)


if __name__ == "__main__":
    unittest.main()