import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE_ID, CONF_DEVICE_NUMBER
from .api import AbbChargeDotApi, AuthError


class AbbConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = AbbChargeDotApi(session, user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
            try:
                devices = await api.get_devices()
            except AuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa
                errors["base"] = "cannot_connect"
            else:
                if not devices:
                    errors["base"] = "no_devices"
                else:
                    d = devices[0]
                    await self.async_set_unique_id(str(d["id"]))
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=d.get("deviceNumber", "ABB Terra AC"),
                        data={
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_DEVICE_ID: d["id"],
                            CONF_DEVICE_NUMBER: d["deviceNumber"],
                        },
                    )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )
