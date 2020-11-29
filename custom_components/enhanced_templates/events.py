"""Event listeners and handlers used in this integration."""
from homeassistant.core import Event
from homeassistant.helpers.area_registry import EVENT_AREA_REGISTRY_UPDATED

# from homeassistant.helpers.entity_registry import EVENT_ENTITY_REGISTRY_UPDATED

from .registry import _areas_registry_data, update_registry

from .const import EVENT_AREAS_CHANGED
from .share import get_hass


async def setup_events() -> None:
    """Setup event listeners and handlers."""

    listen = get_hass().bus.async_listen

    # listen(EVENT_AUTOMATION_RELOADED, handle_automation_reloaded)
    listen(EVENT_AREA_REGISTRY_UPDATED, handle_area_registry_updated)
    # listen(EVENT_AREA_SETTINGS_CHANGED, handle_area_registry_updated)
    # listen(EVENT_ENTITY_REGISTRY_UPDATED, handle_entity_registry_updated)
    # listen(EVENT_ENTITY_SETTINGS_CHANGED, handle_entity_registry_updated)


# async def handle_automation_reloaded(_event: Event):
#     await update_automations(True)


async def handle_area_registry_updated(event: Event) -> None:
    """Handle when an area is updated."""

    await update_registry()
    get_hass().bus.fire(EVENT_AREAS_CHANGED)


# async def handle_entity_registry_updated(event: Event) -> None:
#     """Handle when an entity is updated."""

#     base = get_base()
#     create_task = base.hass.async_create_task

#     action: str = event.data.get(CONF_ACTION)

#     if action in [CONF_CREATE]:
#         await add_entity_to_registry(event.data.get(CONF_ENTITY_ID))

#     if action in [CONF_REMOVE]:
#         await remove_entity_from_registry(event.data.get(CONF_ENTITY_ID))

#     if action in [CONF_UPDATE]:
#         await update_entity_from_registry(event.data.get(CONF_ENTITY_ID))

#     await update_template_entities_global()

#     built_in = base.built_in_entities
#     create_task(built_in[BUILT_IN_AUTOMATION_POPULATE_ENTITY_SELECT].async_trigger({}))
#     create_task(built_in[BUILT_IN_AUTOMATION_ENTITY_CHANGED].async_trigger({}))
