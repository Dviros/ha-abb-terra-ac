from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN


class AbbEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        dev = (self.coordinator.data or {}).get("device") or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_number)},
            name="ABB Terra AC",
            manufacturer="ABB",
            model=dev.get("model"),
            sw_version=dev.get("softVersion"),
            serial_number=self.coordinator.device_number,
        )
