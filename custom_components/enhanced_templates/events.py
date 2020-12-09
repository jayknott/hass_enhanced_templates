"""Event listeners and handlers used in this integration."""
from homeassistant.core import Event
from homeassistant.helpers.area_registry import EVENT_AREA_REGISTRY_UPDATED

from .registry import update_area_registry

from .const import (
    EVENT_AREAS_CHANGED,
    EVENT_AREA_SETTINGS_CHANGED,
    EVENT_ENTITY_SETTINGS_CHANGED,
)
from .settings import update_area_settings, update_entity_settings
from .share import get_hass


async def setup_events() -> None:
    """Setup event listeners and handlers."""

    listen = get_hass().bus.async_listen

    listen(EVENT_AREA_REGISTRY_UPDATED, handle_area_registry_updated)
    listen(EVENT_AREA_SETTINGS_CHANGED, handle_area_settings_changed)
    listen(EVENT_ENTITY_SETTINGS_CHANGED, handle_entity_settings_changed)


async def handle_area_registry_updated(event: Event) -> None:
    """Handle when an area is updated in the registry."""

    update_area_registry()
    get_hass().bus.fire(EVENT_AREAS_CHANGED)


async def handle_area_settings_changed(event: Event) -> None:
    """Handle when area settings have been updated."""

    await update_area_settings()


async def handle_entity_settings_changed(event: Event) -> None:
    """Handle when entity settings have been updated."""

    await update_entity_settings()
