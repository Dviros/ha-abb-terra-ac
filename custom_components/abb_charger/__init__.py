from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE_ID, CONF_DEVICE_NUMBER
from .api import AbbChargeDotApi
from .coordinator import AbbCoordinator

PLATFORMS = [Platform.SWITCH, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER, Platform.UPDATE]


async def async_setup_entry(hass, entry):
    # One client per account: ChargeDot allows one active session per account, so
    # several chargers on the same account must share a login instead of evicting each other.
    key = (entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    apis = hass.data.setdefault(DOMAIN, {})
    if key not in apis:
        apis[key] = AbbChargeDotApi(async_get_clientsession(hass), *key)
    api = apis[key]
    coordinator = AbbCoordinator(hass, api, entry.data[CONF_DEVICE_ID], entry.data[CONF_DEVICE_NUMBER])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
