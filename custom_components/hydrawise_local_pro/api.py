from __future__ import annotations

from typing import Any
import logging
import aiohttp

LOCAL_PERIOD_ID = 998
SCHEDULE_PATH = "get_sched_json.php"
COMMAND_PATH = "set_manual_data.php"
_LOGGER = logging.getLogger(__name__)


class HydrawiseLocalProError(Exception):
    pass


class HydrawiseLocalProAuthError(HydrawiseLocalProError):
    pass


class HydrawiseLocalProApi:
    def __init__(self, session: aiohttp.ClientSession, host: str, username: str, password: str) -> None:
        self._session = session
        self._host = host.strip().replace("http://", "").replace("https://", "").rstrip("/")
        self._auth = aiohttp.BasicAuth(username, password)

    @property
    def host(self) -> str:
        return self._host

    def _url(self, path: str) -> str:
        return f"http://{self._host}/{path}"

    async def async_get_schedule(self) -> dict[str, Any]:
        return await self._request("GET", SCHEDULE_PATH)

    async def async_command_zone(self, action: str, relay: int, duration: int | None = None) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "action": action,
            "relay": relay,
            "period_id": LOCAL_PERIOD_ID,
        }
        if duration is not None:
            params["custom"] = int(duration)
        _LOGGER.warning(
            "Hydrawise command: %s?%s",
            COMMAND_PATH,
            "&".join(f"{key}={value}" for key, value in params.items()),
        )
        response = await self._request("GET", COMMAND_PATH, params=params)
        _LOGGER.warning("Hydrawise command response: %s", response)
        return response

    async def _request(self, method: str, path: str, params: dict[str, str | int] | None = None) -> dict[str, Any]:
        try:
            async with self._session.request(
                method,
                self._url(path),
                params=params,
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 401:
                    raise HydrawiseLocalProAuthError("Falscher Benutzername oder lokales Controller-Passwort")
                if response.status >= 400:
                    raise HydrawiseLocalProError(f"Controller antwortet mit HTTP {response.status}")
                data = await response.json(content_type=None)
        except TimeoutError as err:
            raise HydrawiseLocalProError("Zeitüberschreitung beim Controller") from err
        except aiohttp.ClientError as err:
            raise HydrawiseLocalProError(f"Verbindungsfehler: {err}") from err

        message_type = data.get("message_type") or data.get("messageType")
        if message_type == "error":
            raise HydrawiseLocalProError(str(data.get("message") or "Controller hat den Befehl abgelehnt"))
        return data
