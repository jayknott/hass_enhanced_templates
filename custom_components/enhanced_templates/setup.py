"""Setup the integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, TITLE
from .registry import setup_registry
from .settings import setup_settings
from .share import get_base, get_configuration, get_log
from .template import setup_template


async def setup_integration(hass: HomeAssistant) -> bool:
    """Main setup procedure for this integration."""

    base = get_base()
    base.hass = hass

    # Check if legacy templates are enabled.
    if hass.config.legacy_templates:
        base.log.error(
            f"Legacy templates are enabled. {TITLE} requires legacy templates to be disabled."
        )
        return False

    create_task = hass.async_create_task
    create_task(setup_registry())
    create_task(setup_settings())
    create_task(setup_template())

    return True


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up this integration using yaml."""

    if DOMAIN not in config:
        return True

    configuration = get_configuration()

    if configuration.config_type == "flow":
        return True

    configuration.config = config[DOMAIN]
    configuration.config_type = "yaml"

    return await setup_integration(hass)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up this integration using the UI."""

    configuration = get_configuration()

    if configuration.config_type == "yaml":
        get_log().warning(
            f"""
                {TITLE} is setup both in config.yaml and integrations.
                The YAML configuration has taken precedence.
            """
        )
        return False

    # TODO: Find out what this means and if it is needed.
    # if config_entry.source == config_entries.SOURCE_IMPORT:
    #     hass.async_create_task(hass.config_entries.async_remove(config_entry.entry_id))
    #     return False

    configuration.config_entry = config_entry
    configuration.config_type = "flow"

    return await setup_integration(hass)
