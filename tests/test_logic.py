"""Smallest checks for issue #1 logic. Run: uv run --with homeassistant --with pytest pytest tests"""
from types import SimpleNamespace

from custom_components.abb_charger.binary_sensor import _is_charging, _is_connected
from custom_components.abb_charger.sensor import AbbSensor, DESCRIPTIONS, _phases

DEV_11KW = {"elecPower": 11000, "ratedCurrent": 16}
# frozen live values from issue #1 (6,830 W, sum-of-phases x100)
LIVE = {"power": 6830, "current": 2975, "voltage": 69400}


def _value(key, port, device=DEV_11KW):
    d = next(d for d in DESCRIPTIONS if d[0] == key)
    s = AbbSensor.__new__(AbbSensor)
    s.coordinator = SimpleNamespace(data={"port": port, "device": device})
    s._section, s._field, s._kind = d[1], d[2], d[7]
    return s.native_value


def test_charging_follows_connector_status():
    assert _is_charging({**LIVE, "connectorStatus": 6})
    for code in (2, 3, 4, 8, "8"):
        assert not _is_charging({**LIVE, "connectorStatus": code})
    assert _is_charging({**LIVE, "connectorStatus": ""})  # fallback: old power logic
    assert _is_connected({"connectorStatus": 8}) and not _is_connected({"connectorStatus": 2})
    assert not _is_connected({"connectorStatus": ""})  # used to raise ValueError


def test_phases():
    assert _phases(DEV_11KW) == 3
    assert _phases({"elecPower": 22, "ratedCurrent": 32}) == 3  # kW
    assert _phases({"elecPower": 7400, "ratedCurrent": 32}) == 1
    assert _phases({}) == 1


def test_live_sensors():
    charging = {**LIVE, "connectorStatus": 6}
    assert _value("current", charging) == 9.9
    assert _value("voltage", charging) == 231.3
    assert _value("power", charging) == 6830
    ended = {**LIVE, "connectorStatus": 8}
    assert _value("power", ended) == 0 and _value("current", ended) == 0
    assert _value("voltage", ended) == 231.3
