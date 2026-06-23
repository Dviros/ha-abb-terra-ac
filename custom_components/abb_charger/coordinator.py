from datetime import timedelta
import json
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL_SECONDS
from .api import AbbChargeDotApi

_LOGGER = logging.getLogger(__name__)


class AbbCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: AbbChargeDotApi, device_id: int, device_number: str):
        super().__init__(hass, _LOGGER, name=DOMAIN,
                         update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS))
        self.api = api
        self.device_id = device_id
        self.device_number = device_number

    async def _async_update_data(self):
        try:
            device = await self.api.get_device(self.device_id)
            last = await self.api.get_last_session(self.device_id)
            price = await self.api.get_price(self.device_id)
            upgrade = None
            if isinstance(device, dict) and device.get("softVersion") and device.get("hardwareVersion"):
                upgrade = await self.api.get_upgrade(
                    self.device_number, device["softVersion"], device["hardwareVersion"])
            return {"device": device, "last_session": last, "price": price,
                    "upgrade": upgrade, "port": _parse_port(device)}
        except Exception as err:  # noqa
            raise UpdateFailed(str(err)) from err


def _parse_port(device) -> dict:
    """Flatten ports[0] + its live `detail` JSON string into one dict."""
    if not isinstance(device, dict):
        return {}
    ports = device.get("ports")
    if not (isinstance(ports, list) and ports and isinstance(ports[0], dict)):
        return {}
    p0 = ports[0]
    port = {k: v for k, v in p0.items() if k != "detail"}
    detail = p0.get("detail")
    if isinstance(detail, str) and detail:
        try:
            port.update(json.loads(detail))
        except ValueError:
            pass
    port["connectorStatus"] = p0.get("status")  # connector status (not device.status)
    return port
