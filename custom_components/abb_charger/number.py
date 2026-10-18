from homeassistant.components.number import NumberMode, RestoreNumber
from homeassistant.const import UnitOfElectricCurrent
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_MAX_CURRENT, MIN_CHARGE_CURRENT
from .entity import AbbEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AbbChargingCurrent(entry.runtime_data, entry)])


class AbbChargingCurrent(AbbEntity, RestoreNumber):
    """Charging current limit (load balancing), set over WS (0xC0).

    The cloud's REST `adjustCurrent` does not track the WS-set limit (issue #1), so the
    state is the last value successfully sent, restored across restarts.
    """

    _attr_name = "Charging current limit"
    _attr_icon = "mdi:current-ac"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_native_min_value = MIN_CHARGE_CURRENT
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{coordinator.device_number}_charge_current"
        self._attr_native_value = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) is not None:
            self._attr_native_value = last.native_value

    @property
    def native_max_value(self):
        rated = self.coordinator.rated_current
        return float(min(rated, self._entry.options.get(CONF_MAX_CURRENT, rated)))

    @property
    def extra_state_attributes(self):
        port = (self.coordinator.data or {}).get("port") or {}
        return {"cloud_adjust_current": port.get("adjustCurrent")}

    async def async_set_native_value(self, value):
        amps = int(value)
        if amps > self.native_max_value:  # HA range-checks too; guard direct calls
            raise HomeAssistantError(f"{amps} A exceeds the configured maximum {self.native_max_value:g} A")
        r = await self.coordinator.api.set_output_current(self.coordinator.device_number, amps)
        if not r.get("ok"):
            raise HomeAssistantError(f"set current failed: {r.get('result') or r.get('error')}")
        self._attr_native_value = float(amps)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
