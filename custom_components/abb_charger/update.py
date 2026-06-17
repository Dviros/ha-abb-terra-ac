from homeassistant.components.update import UpdateEntity

from .entity import AbbEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AbbFirmwareUpdate(entry.runtime_data)])


class AbbFirmwareUpdate(AbbEntity, UpdateEntity):
    _attr_name = "Firmware"

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_number}_firmware"

    @property
    def installed_version(self):
        return ((self.coordinator.data or {}).get("device") or {}).get("softVersion")

    @property
    def latest_version(self):
        up = (self.coordinator.data or {}).get("upgrade") or {}
        rule = up.get("rule") if isinstance(up, dict) else None
        if isinstance(rule, dict) and rule.get("version"):
            return rule["version"]
        return self.installed_version
