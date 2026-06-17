from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE_ID, CONF_DEVICE_NUMBER
from .api import AbbChargeDotApi
from .coordinator import AbbCoordinator

PLATFORMS = [Platform.SWITCH, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.UPDATE]


async def async_setup_entry(hass, entry):
    session = async_get_clientsession(hass)
    api = AbbChargeDotApi(session, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    coordinator = AbbCoordinator(hass, api, entry.data[CONF_DEVICE_ID], entry.data[CONF_DEVICE_NUMBER])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
