from __future__ import annotations
from homeassistant.components.valve import ValveDeviceClass, ValveEntity, ValveEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HydrawiseLocalProConfigEntry
from .api import HydrawiseLocalProError
from .entity import ZoneEntity


async def async_setup_entry(hass: HomeAssistant, entry: HydrawiseLocalProConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data.coordinator
    async_add_entities(IrrigationValve(c, relay) for relay in c.data)


class IrrigationValve(ZoneEntity, ValveEntity):
    _attr_name = None
    _attr_device_class = ValveDeviceClass.WATER
    _attr_reports_position = False
    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

    def __init__(self, coordinator, relay):
        super().__init__(coordinator, relay)
        self._attr_unique_id = f"{coordinator.api.host}_{relay}_valve"

    @property
    def is_closed(self) -> bool | None:
        z = self.zone
        return None if z is None else not z.is_running

    @property
    def is_opening(self) -> bool:
        return self.relay in self.coordinator.pending_relays

    async def async_open_valve(self, **kwargs) -> None:
        try:
            await self.coordinator.async_start(self.relay)
        except (HydrawiseLocalProError, RuntimeError) as err:
            raise HomeAssistantError(str(err)) from err

    async def async_close_valve(self, **kwargs) -> None:
        try:
            await self.coordinator.async_stop(self.relay)
        except HydrawiseLocalProError as err:
            raise HomeAssistantError(str(err)) from err
