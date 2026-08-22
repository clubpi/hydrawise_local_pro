from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "hydrawise_local_pro" / "model.py"
)
SPEC = importlib.util.spec_from_file_location("hydrawise_local_pro_model", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODEL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODEL
SPEC.loader.exec_module(MODEL)


class ParseScheduleTests(unittest.TestCase):
    def test_next_run_uses_reasonable_offset(self) -> None:
        epoch = 1_800_000_000
        zones = MODEL.parse_schedule(
            {
                "time": epoch,
                "relays": [{"relay": 1, "relay_id": 10, "name": "Front", "time": 3600}],
            }
        )

        self.assertEqual(
            zones[1].next_run,
            datetime.fromtimestamp(epoch + 3600, tz=timezone.utc),
        )

    def test_next_run_ignores_firmware_sentinel(self) -> None:
        zones = MODEL.parse_schedule(
            {
                "time": 1_800_000_000,
                "relays": [
                    {
                        "relay": 1,
                        "relay_id": 10,
                        "name": "Front",
                        "time": 1_576_800_000,
                    }
                ],
            }
        )

        self.assertIsNone(zones[1].next_run)


if __name__ == "__main__":
    unittest.main()
