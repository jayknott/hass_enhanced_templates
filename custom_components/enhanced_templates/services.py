"""Services available for this integration."""
from homeassistant.core import ServiceCall

from .settings import (
    save_setting,
    SCHEMA_UPDATE_AREA_SERVICE,
    SCHEMA_UPDATE_ENTITY_SERVICE,
)
from .const import (
    CONF_AREA,
    CONF_ENTITY,
    DOMAIN,
    SERVICE_SET_AREA,
    SERVICE_SET_ENTITY,
)
from .share import get_hass


async def setup_services() -> None:
    """Setup services."""

    hass = get_hass()
    register = hass.services.async_register

    async def service_save_area_setting(call: ServiceCall) -> None:
        await save_setting(CONF_AREA, call)

    async def service_save_entity_setting(call: ServiceCall) -> None:
        await save_setting(CONF_ENTITY, call)

    # Set area settings service
    register(
        DOMAIN, SERVICE_SET_AREA, service_save_area_setting, SCHEMA_UPDATE_AREA_SERVICE
    )

    # Set entity settings service
    register(
        DOMAIN,
        SERVICE_SET_ENTITY,
        service_save_entity_setting,
        SCHEMA_UPDATE_ENTITY_SERVICE,
    )
