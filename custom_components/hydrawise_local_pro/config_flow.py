from __future__ import annotations
from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import HydrawiseLocalProApi, HydrawiseLocalProAuthError, HydrawiseLocalProError
from .const import CONF_USERNAME, DEFAULT_USERNAME, DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

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
                    data = dict(user_input)
                    data[CONF_HOST] = host
                    return self.async_create_entry(title=f"Hydrawise Local Pro ({host})", data=data)
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
