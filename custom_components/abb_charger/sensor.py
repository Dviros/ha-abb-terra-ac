from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfTime
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

from .entity import AbbEntity

# key, section, field, name, unit, device_class, state_class, kind(None|'ts'|'num'), diagnostic
DESCRIPTIONS = [
    ("energy", "last_session", "energy", "Last session energy", UnitOfEnergy.KILO_WATT_HOUR,
     None, SensorStateClass.MEASUREMENT, "num", False),
    ("cost", "last_session", "cost", "Last session cost", None, None, SensorStateClass.MEASUREMENT, "num", False),
    ("duration", "last_session", "duration", "Last session duration", UnitOfTime.SECONDS,
     SensorDeviceClass.DURATION, None, "num", False),
    ("end", "last_session", "stopTime", "Last session end", None, SensorDeviceClass.TIMESTAMP, None, "ts", False),
    ("avg_price", "price", "averagePrice", "Tariff average price", None, None, None, "num", False),
    ("status", "device", "status", "Status code", None, None, None, None, True),
    ("rated_current", "device", "ratedCurrent", "Rated current", "A", None, None, "num", True),
    ("max_power", "device", "elecPower", "Rated power", "W", None, None, "num", True),
    ("firmware", "device", "softVersion", "Firmware", None, None, None, None, True),
    ("open_flag", "price", "open", "Public charging flag", None, None, None, "num", True),
]


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([AbbSensor(c, *d) for d in DESCRIPTIONS])


class AbbSensor(AbbEntity, SensorEntity):
    def __init__(self, coordinator, key, section, field, name, unit, dc, sc, kind, diag):
        super().__init__(coordinator)
        self._section = section
        self._field = field
        self._kind = kind
        self._attr_unique_id = f"{coordinator.device_number}_{key}"
        self._attr_name = name
        if unit:
            self._attr_native_unit_of_measurement = unit
        if dc:
            self._attr_device_class = dc
        if sc:
            self._attr_state_class = sc
        if diag:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self):
        sec = (self.coordinator.data or {}).get(self._section) or {}
        if not isinstance(sec, dict):
            return None
        v = sec.get(self._field)
        if v is None or v == "":
            return None
        if self._kind == "ts":
            dt = dt_util.parse_datetime(str(v).replace(" ", "T"))
            if dt and dt.tzinfo is None:
                dt = dt.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
            return dt
        if self._kind == "num":
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
        return v
