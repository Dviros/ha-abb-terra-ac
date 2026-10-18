import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (DOMAIN, CONF_USERNAME, CONF_PASSWORD, CONF_DEVICE_ID, CONF_DEVICE_NUMBER,
                    CONF_MAX_CURRENT, MIN_CHARGE_CURRENT)
from .api import AbbChargeDotApi, AuthError


class AbbConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """One config entry per charger. Accounts with several chargers add the
    integration once per charger; the picker hides chargers already set up."""

    VERSION = 1

    def __init__(self):
        self._creds = {}
        self._devices = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AbbOptionsFlow()

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
                    configured = self._async_current_ids()
                    self._devices = {str(d["id"]): d for d in devices if str(d["id"]) not in configured}
                    if not self._devices:
                        return self.async_abort(reason="already_configured")
                    self._creds = user_input
                    if len(self._devices) == 1:
                        return await self._create(next(iter(self._devices.values())))
                    return await self.async_step_device()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    async def async_step_device(self, user_input=None):
        if user_input is not None:
            return await self._create(self._devices[user_input[CONF_DEVICE_ID]])
        choices = {k: f"{d.get('deviceNumber', k)} ({d.get('model') or 'ABB Terra AC'})"
                   for k, d in self._devices.items()}
        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE_ID): vol.In(choices)}),
        )

    async def _create(self, d):
        await self.async_set_unique_id(str(d["id"]))
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=d.get("deviceNumber", "ABB Terra AC"),
            data={
                CONF_USERNAME: self._creds[CONF_USERNAME],
                CONF_PASSWORD: self._creds[CONF_PASSWORD],
                CONF_DEVICE_ID: d["id"],
                CONF_DEVICE_NUMBER: d["deviceNumber"],
            },
        )


class AbbOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        coordinator = getattr(self.config_entry, "runtime_data", None)
        rated = coordinator.rated_current if coordinator else 80
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_MAX_CURRENT, rated)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_MAX_CURRENT, default=min(current, rated)):
                    vol.All(vol.Coerce(int), vol.Range(min=MIN_CHARGE_CURRENT, max=rated)),
            }),
            description_placeholders={"rated": str(rated)},
        )
