"""Adds config flow for this integration."""
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, TITLE


class CustomDashboardFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for this integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if self.hass.data.get(DOMAIN):
            return self.async_abort(reason="single_instance_allowed")

        user_input_update = user_input if user_input is not None else {}
        return self.async_create_entry(title={TITLE}, data=user_input_update)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        return CustomDashboardOptionsFlowHandler(config_entry)


class CustomDashboardOptionsFlowHandler(config_entries.OptionsFlow):
    """Custom Dashboard config flow options handler."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize Custom Dashboard options flow."""
        # Overwriting this method allows for passing of the config_entry
        self.config_entry = config_entry

    async def async_step_init(self, user_input: ConfigType = None):
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input: ConfigType = None):
        return self.async_create_entry(title="Custom Dashboard", data=user_input)