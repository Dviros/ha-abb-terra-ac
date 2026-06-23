from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass

from .entity import AbbEntity

# Connector status codes that mean "nothing plugged in / available".
IDLE_CONNECTOR_CODES = {2}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _is_charging(port: dict) -> bool:
    if _num(port.get("power")) > 0:
        return True
    finished = port.get("finishedAt") or ""
    if finished:
        return False
    return bool(port.get("orderNumber") or port.get("startedAt"))


def _is_connected(port: dict) -> bool:
    if _is_charging(port):
        return True
    if _num(port.get("occupyUserId")) > 0:
        return True
    status = port.get("connectorStatus")
    return status is not None and int(status) not in IDLE_CONNECTOR_CODES


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([AbbOnline(c), AbbCharging(c), AbbConnected(c)])


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


class AbbCharging(AbbEntity, BinarySensorEntity):
    _attr_name = "Charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_number}_charging"

    @property
    def is_on(self):
        return _is_charging((self.coordinator.data or {}).get("port") or {})


class AbbConnected(AbbEntity, BinarySensorEntity):
    """Best-effort 'cable connected at the station'. Confirmed true while charging;
    connected-but-idle relies on connector status, verified on next real plug-in."""

    _attr_name = "Connected"
    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_number}_connected"

    @property
    def is_on(self):
        return _is_connected((self.coordinator.data or {}).get("port") or {})

    @property
    def extra_state_attributes(self):
        p = (self.coordinator.data or {}).get("port") or {}
        return {"connector_status": p.get("connectorStatus"), "occupy_user_id": p.get("occupyUserId")}
