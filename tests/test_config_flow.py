"""Multi-charger account (issue #2): picker shows only unconfigured chargers."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

DOMAIN = "abb_charger"
CREDS = {"username": "a@b.c", "password": "pw"}
DEVICES = [{"id": i, "deviceNumber": f"TACW-{i}", "model": "CDT_TACW11"} for i in (1, 2, 3)]


@pytest.fixture(autouse=True)
def _enable(enable_custom_integrations):
    yield


async def _start(hass):
    with patch("custom_components.abb_charger.config_flow.AbbChargeDotApi.get_devices",
               AsyncMock(return_value=DEVICES)):
        r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        return await hass.config_entries.flow.async_configure(r["flow_id"], CREDS)


async def test_pick_second_charger(hass):
    MockConfigEntry(domain=DOMAIN, unique_id="1").add_to_hass(hass)
    r = await _start(hass)
    assert r["step_id"] == "device"
    choices = r["data_schema"].schema["device_id"].container
    assert set(choices) == {"2", "3"}
    with patch("custom_components.abb_charger.async_setup_entry", AsyncMock(return_value=True)):
        r = await hass.config_entries.flow.async_configure(r["flow_id"], {"device_id": "2"})
    assert r["type"] is FlowResultType.CREATE_ENTRY
    assert r["data"]["device_number"] == "TACW-2" and r["result"].unique_id == "2"


async def test_all_configured_aborts(hass):
    for i in (1, 2, 3):
        MockConfigEntry(domain=DOMAIN, unique_id=str(i)).add_to_hass(hass)
    r = await _start(hass)
    assert r["type"] is FlowResultType.ABORT and r["reason"] == "already_configured"
