from __future__ import annotations
import asyncio
from datetime import timedelta, datetime, timezone
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HydrawiseLocalProApi, HydrawiseLocalProError
from .model import Zone, parse_schedule

_LOGGER = logging.getLogger(__name__)


class HydrawiseLocalProCoordinator(DataUpdateCoordinator[dict[int, Zone]]):
    def __init__(self, hass: HomeAssistant, api: HydrawiseLocalProApi) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Hydrawise Local Pro",
            update_interval=timedelta(seconds=5),
        )
        self.api = api
        self.duration_seconds: dict[int, int] = {}
        self.command_ends: dict[int, datetime] = {}
        self.pending_relays: list[int] = []
        self._queue_task: asyncio.Task[None] | None = None
        self._keepalive_tasks: dict[int, asyncio.Task[None]] = {}
        self.automatic_enabled = True

    async def _async_update_data(self) -> dict[int, Zone]:
        previous_running = {
            relay for relay, zone in (self.data or {}).items() if zone.is_running
        }
        try:
            payload = await self.api.async_get_schedule()
            zones = parse_schedule(payload)
        except HydrawiseLocalProError as err:
            raise UpdateFailed(str(err)) from err

        now = datetime.now(timezone.utc)
        current_running = {relay for relay, zone in zones.items() if zone.is_running}
        if previous_running - current_running and self.pending_relays and self._queue_task is None:
            self._queue_task = asyncio.create_task(self._start_next_after_pause())

        for relay, zone in zones.items():
            if relay not in self.duration_seconds:
                self.duration_seconds[relay] = zone.default_run_seconds
            # Firmware 1.x often omits time_left. Use our commanded end time as a reliable fallback.
            if zone.is_running and relay in self.command_ends:
                zone.remaining_seconds = max(0, int((self.command_ends[relay] - now).total_seconds()))
            if not zone.is_running:
                self.command_ends.pop(relay, None)
        return zones

    async def _start_next_after_pause(self) -> None:
        try:
            await asyncio.sleep(30)
            while self.data and any(zone.is_running for zone in self.data.values()):
                await asyncio.sleep(5)
            if self.pending_relays:
                await self.async_start(self.pending_relays.pop(0))
        finally:
            self._queue_task = None

    def _relay_is_active(self, relay: int) -> bool:
        zone = self.data.get(relay) if self.data else None
        if zone and zone.is_running:
            return True
        end_time = self.command_ends.get(relay)
        return end_time is not None and end_time > datetime.now(timezone.utc)

    def get_duration(self, relay: int) -> int:
        return int(self.duration_seconds.get(relay, 300))

    async def _maintain_local_run(self, relay: int, end_time: datetime) -> None:
        try:
            while True:
                remaining = (end_time - datetime.now(timezone.utc)).total_seconds()
                if remaining <= 0:
                    break
                await asyncio.sleep(min(45, max(1, remaining - 10)))
                if (end_time - datetime.now(timezone.utc)).total_seconds() <= 0:
                    break
                await self.api.async_command_zone("run", relay, duration=60)
            await self.api.async_command_zone("stop", relay)
            self.command_ends.pop(relay, None)
            await self.async_request_refresh()
        except asyncio.CancelledError:
            raise
        except HydrawiseLocalProError:
            _LOGGER.exception("Fehler beim Verlängern von Hydrawise-Zone %s", relay)
        finally:
            self._keepalive_tasks.pop(relay, None)

    async def async_set_duration(self, relay: int, seconds: int) -> None:
        self.duration_seconds[relay] = max(60, min(10800, int(seconds)))
        self.async_update_listeners()

    async def async_start(self, relay: int) -> None:
        if not self.automatic_enabled:
            return
        if any(
            other_relay != relay and self._relay_is_active(other_relay)
            for other_relay in self.duration_seconds
        ):
            if relay not in self.pending_relays:
                self.pending_relays.append(relay)
            await self.async_request_refresh()
            return

        if relay in self.pending_relays:
            self.pending_relays.remove(relay)

        duration = self.get_duration(relay)
        await self.api.async_command_zone("run", relay, duration=duration)
        end_time = datetime.now(timezone.utc) + timedelta(seconds=duration)
        self.command_ends[relay] = end_time
        old_task = self._keepalive_tasks.pop(relay, None)
        if old_task is not None:
            old_task.cancel()
        self._keepalive_tasks[relay] = asyncio.create_task(
            self._maintain_local_run(relay, end_time)
        )
        await self.async_request_refresh()

    async def async_set_automatic(self, enabled: bool) -> None:
        self.automatic_enabled = enabled
        if not enabled:
            self.pending_relays.clear()
            for relay, zone in list(self.data.items()):
                if zone.is_running:
                    await self.async_stop(relay)
        await self.async_request_refresh()

    async def async_stop(self, relay: int) -> None:
        keepalive_task = self._keepalive_tasks.pop(relay, None)
        if keepalive_task is not None:
            keepalive_task.cancel()
        if relay in self.pending_relays:
            self.pending_relays.remove(relay)
            return
        await self.api.async_command_zone("stop", relay)
        self.command_ends.pop(relay, None)
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        if self._queue_task is not None:
            self._queue_task.cancel()
            self._queue_task = None
        for task in self._keepalive_tasks.values():
            task.cancel()
        self._keepalive_tasks.clear()
