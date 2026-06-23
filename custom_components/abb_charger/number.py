from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.exceptions import HomeAssistantError

from .const import MIN_CHARGE_CURRENT
from .entity import AbbEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AbbChargingCurrent(entry.runtime_data)])


class AbbChargingCurrent(AbbEntity, NumberEntity):
    """Charging current limit (load balancing) — read from REST adjustCurrent, set over WS (0xC0)."""

    _attr_name = "Charging current limit"
    _attr_icon = "mdi:current-ac"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_native_min_value = MIN_CHARGE_CURRENT
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_number}_charge_current"

    @property
    def native_max_value(self):
        dev = (self.coordinator.data or {}).get("device") or {}
        try:
            return float(dev.get("ratedCurrent") or 16)
        except (TypeError, ValueError):
            return 16.0

    @property
    def native_value(self):
        port = (self.coordinator.data or {}).get("port") or {}
        v = port.get("adjustCurrent")
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value):
        r = await self.coordinator.api.set_output_current(self.coordinator.device_number, int(value))
        if not r.get("ok"):
            raise HomeAssistantError(f"set current failed: {r.get('result') or r.get('error')}")
        await self.coordinator.async_request_refresh()
