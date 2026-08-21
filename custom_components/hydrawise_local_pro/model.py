from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class Zone:
    relay: int
    relay_id: int
    name: str
    default_run_seconds: int
    is_running: bool
    remaining_seconds: int | None
    last_watered: datetime | None
    next_run: datetime | None
    suspended: bool


def _to_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def parse_schedule(payload: dict[str, Any]) -> dict[int, Zone]:
    controller_epoch = _to_int(payload.get("time"))
    running_rows = payload.get("running") or []
    running_by_relay_id = {}
    running_by_relay = {}
    for row in running_rows:
        rid = _to_int(row.get("relay_id"), -1)
        r = _to_int(row.get("relay"), -1)
        if rid >= 0:
            running_by_relay_id[rid] = row
        if r >= 0:
            running_by_relay[r] = row

    out: dict[int, Zone] = {}
    for row in payload.get("relays") or []:
        relay = _to_int(row.get("relay"))
        relay_id = _to_int(row.get("relay_id"))
        if relay <= 0:
            continue
        running = running_by_relay_id.get(relay_id) or running_by_relay.get(relay)
        normal_runtime_min = _to_int(row.get("normalRuntime"))
        run_seconds = _to_int(row.get("run_seconds") or row.get("run"))
        default_seconds = normal_runtime_min * 60 if normal_runtime_min > 0 else (run_seconds if run_seconds > 0 else 300)

        remaining = None
        if running:
            for key in ("time_left", "remaining", "run_seconds", "time"):
                if key in running:
                    val = _to_int(running.get(key), -1)
                    if val >= 0:
                        remaining = val
                        break

        last_epoch = _to_int(row.get("lastwaterepoch"))
        next_in = _to_int(row.get("time"))
        out[relay] = Zone(
            relay=relay,
            relay_id=relay_id,
            name=str(row.get("name") or f"Zone {relay}"),
            default_run_seconds=default_seconds,
            is_running=bool(running),
            remaining_seconds=remaining,
            last_watered=datetime.fromtimestamp(last_epoch, tz=timezone.utc) if last_epoch > 0 else None,
            next_run=datetime.fromtimestamp(controller_epoch + next_in, tz=timezone.utc)
                     if controller_epoch > 0 and next_in > 0 else None,
            suspended=bool(_to_int(row.get("suspended"))),
        )
    return out
