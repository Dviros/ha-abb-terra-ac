import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .entity import AbbEntity
from .binary_sensor import _is_charging  # single source of truth for "is it charging"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AbbChargeSwitch(entry.runtime_data)])


class AbbChargeSwitch(AbbEntity, SwitchEntity):
    _attr_name = "Charging"
    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_number}_charge_control"

    @property
    def is_on(self):
        # Reflect the charger's real state (power/active session), so it never
        # gets stuck "on" after a charge ends on its own.
        return _is_charging((self.coordinator.data or {}).get("port") or {})

    async def async_turn_on(self, **kwargs):
        await self._do("start")

    async def async_turn_off(self, **kwargs):
        await self._do("stop")

    async def _do(self, action):
        r = await self.coordinator.api.command(self.coordinator.device_number, action)
        if not r.get("ok"):
            raise HomeAssistantError(f"{action} failed: {r.get('result') or r.get('error')}")
        await self.coordinator.async_request_refresh()
