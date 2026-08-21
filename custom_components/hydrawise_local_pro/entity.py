from __future__ import annotations
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HydrawiseLocalProCoordinator


class ZoneEntity(CoordinatorEntity[HydrawiseLocalProCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HydrawiseLocalProCoordinator, relay: int) -> None:
        super().__init__(coordinator)
        self.relay = relay

    @property
    def zone(self):
        return self.coordinator.data.get(self.relay)

    @property
    def device_info(self) -> DeviceInfo:
        z = self.zone
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.api.host}-{self.relay}")},
            name=f"{z.name} (Local Pro)" if z else f"Zone {self.relay} (Local Pro)",
            manufacturer="Hunter",
            model="Hydrawise HC local zone",
            via_device=(DOMAIN, self.coordinator.api.host),
        )
