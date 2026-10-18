from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import (UnitOfEnergy, UnitOfTime, UnitOfPower,
                                 UnitOfElectricCurrent, UnitOfElectricPotential)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

from .binary_sensor import _is_charging
from .entity import AbbEntity

# key, section, field, name, unit, device_class, state_class, kind, diagnostic
# kind: None raw | 'ts' timestamp | 'num' float | 'live' float, 0 when not charging
#       'amps'/'volts' per-phase value from the raw sum-of-phases x100 (issue #1)
DESCRIPTIONS = [
    ("energy", "last_session", "energy", "Last session energy", UnitOfEnergy.WATT_HOUR,
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
    # --- live charger telemetry (ports[0].detail, refreshed each poll) ---
    ("power", "port", "power", "Power", UnitOfPower.WATT,
     SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT, "live", False),
    ("current", "port", "current", "Current", UnitOfElectricCurrent.AMPERE,
     SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, "amps", False),
    ("voltage", "port", "voltage", "Voltage", UnitOfElectricPotential.VOLT,
     SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, "volts", True),
    ("session_energy_live", "port", "elecQuantity", "Session energy (live)", UnitOfEnergy.WATT_HOUR,
     None, SensorStateClass.MEASUREMENT, "num", False),
    ("session_duration_live", "port", "duration", "Session duration (live)", UnitOfTime.SECONDS,
     SensorDeviceClass.DURATION, None, "num", True),
    ("connector_status", "port", "connectorStatus", "Connector status", None, None, None, None, True),
    ("fault", "port", "faultType", "Fault", None, None, None, None, True),
]


def _phases(device: dict) -> int:
    """1 or 3, from the rated specs (7.4 kW/32 A -> 1; 11 kW/16 A, 22 kW/32 A -> 3)."""
    try:
        watts = float(device.get("elecPower"))
        amps = float(device.get("ratedCurrent"))
    except (TypeError, ValueError):
        return 1
    if watts < 100:  # reported in kW
        watts *= 1000
    return 3 if amps > 0 and watts / (230 * amps) > 1.5 else 1


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
        if self._kind is None:
            return v
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if self._kind in ("live", "amps") and not _is_charging(sec):
            return 0.0  # cloud freezes the last live values until unplug
        if self._kind in ("amps", "volts"):
            return round(v / 100 / _phases(self.coordinator.data.get("device") or {}), 1)
        return v
