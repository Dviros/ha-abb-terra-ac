from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass

from .entity import AbbEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AbbOnline(entry.runtime_data)])


class AbbOnline(AbbEntity, BinarySensorEntity):
    _attr_name = "Online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_number}_online"

    @property
    def is_on(self):
        dev = (self.coordinator.data or {}).get("device") or {}
        return dev.get("online") == 1
