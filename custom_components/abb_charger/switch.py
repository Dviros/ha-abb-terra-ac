import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError

from .entity import AbbEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AbbChargeSwitch(entry.runtime_data)])


class AbbChargeSwitch(AbbEntity, SwitchEntity):
    _attr_name = "Charging"
    _attr_icon = "mdi:ev-station"
    _attr_assumed_state = True   # no reliable live read over cloud yet; control is one-shot

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_number}_charge_control"
        self._is_on = False

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        await self._do("start", True)

    async def async_turn_off(self, **kwargs):
        await self._do("stop", False)

    async def _do(self, action, new_state):
        r = await self.coordinator.api.command(self.coordinator.device_number, action)
        if not r.get("ok"):
            raise HomeAssistantError(f"{action} failed: {r.get('result') or r.get('error')}")
        self._is_on = new_state
        self.async_write_ha_state()
