from __future__ import annotations
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .api import HydrawiseLocalProApi, HydrawiseLocalProAuthError, HydrawiseLocalProError
from .const import CONF_RELAYS, CONF_USERNAME, DEFAULT_USERNAME, DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._pending_data: dict[str, Any] = {}
        self._relay_options: list[dict[str, str]] = []

    async def async_step_zones(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = dict(self._pending_data)
            data[CONF_RELAYS] = user_input[CONF_RELAYS]
            return self.async_create_entry(
                title=f"Hydrawise Local Pro ({data[CONF_HOST]})", data=data
            )

        return self.async_show_form(
            step_id="zones",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RELAYS,
                        default=[option["value"] for option in self._relay_options],
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=self._relay_options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip().replace("http://", "").replace("https://", "").rstrip("/")
            api = HydrawiseLocalProApi(
                async_get_clientsession(self.hass),
                host,
                user_input.get(CONF_USERNAME, DEFAULT_USERNAME),
                user_input[CONF_PASSWORD],
            )
            try:
                payload = await api.async_get_schedule()
                if not payload.get("relays"):
                    errors["base"] = "no_zones"
                else:
                    await self.async_set_unique_id(host)
                    self._abort_if_unique_id_configured()
                    self._pending_data = dict(user_input)
                    self._pending_data[CONF_HOST] = host
                    self._relay_options = [
                        {
                            "value": str(row["relay"]),
                            "label": str(row.get("name") or f"Zone {row['relay']}"),
                        }
                        for row in payload["relays"]
                        if int(row.get("relay", 0)) > 0
                    ]
                    return await self.async_step_zones()
            except HydrawiseLocalProAuthError:
                errors["base"] = "invalid_auth"
            except HydrawiseLocalProError:
                errors["base"] = "cannot_connect"

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        coordinator = self.config_entry.runtime_data.coordinator
        options = [
            {"value": str(relay), "label": zone.name}
            for relay, zone in sorted(coordinator.data.items())
        ]
        selected = self.config_entry.options.get(
            CONF_RELAYS,
            self.config_entry.data.get(
                CONF_RELAYS,
                [option["value"] for option in options],
            ),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RELAYS,
                        default=selected,
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )
