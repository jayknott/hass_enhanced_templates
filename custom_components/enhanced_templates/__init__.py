"""
Use areas and custom globals in Jinja templates and YAML files.

For more details about this integration, please refer to the documentation at
https://github.com/jayknott/hass_enhanced_templates
"""
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .setup import (
    async_setup as yaml_setup,
    async_setup_entry as ui_setup,
)

CONFIG_SCHEMA = vol.Schema({DOMAIN: {}}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up this integration using yaml."""

    return await yaml_setup(hass, config)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigType) -> bool:
    """Set up this integration using the UI."""

    return await ui_setup(hass, config_entry)
