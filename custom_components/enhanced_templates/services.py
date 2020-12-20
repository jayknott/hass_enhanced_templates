"""Services available for this integration."""
from homeassistant.core import ServiceCall

from .settings import (
    SCHEMA_UPDATE_PERSON_SERVICE,
    save_setting,
    SCHEMA_UPDATE_AREA_SERVICE,
    SCHEMA_UPDATE_ENTITY_SERVICE,
)
from .const import (
    CONF_AREA,
    CONF_ENTITY,
    CONF_PERSON,
    DOMAIN,
    SERVICE_SET_AREA,
    SERVICE_SET_ENTITY,
    SERVICE_SET_PERSON,
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

    async def service_save_person_setting(call: ServiceCall) -> None:
        await save_setting(CONF_PERSON, call)

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

    # Set person settings service
    register(
        DOMAIN,
        SERVICE_SET_PERSON,
        service_save_person_setting,
        SCHEMA_UPDATE_PERSON_SERVICE,
    )
