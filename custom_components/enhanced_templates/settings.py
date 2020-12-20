"""Read and write area and entity settings in storage."""
from typing import Any, List, Optional, Union
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.const import (
    ATTR_AREA_ID,
    ATTR_NAME,
    CONF_ENTITY_ID,
    CONF_ICON,
    CONF_ID,
)
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import Store

from .const import (
    CONF_ACTION,
    CONF_AREA,
    CONF_AREAS,
    CONF_ENTITIES,
    CONF_ENTITY,
    CONF_ENTITY_TYPE,
    CONF_ORIGINAL_AREA_ID,
    CONF_ORIGINAL_ENTITY_TYPE,
    CONF_PERSON,
    CONF_PERSONS,
    CONF_SORT_ORDER,
    CONF_UPDATE,
    CONF_VISIBLE,
    DEFAULT_AREA_ICON,
    DEFAULT_SORT_ORDER,
    DEFAULT_SORT_ORDER_MAX,
    DEFAULT_SORT_ORDER_MIN,
    DOMAIN,
    EVENT_AREA_SETTINGS_CHANGED,
    EVENT_ENTITY_SETTINGS_CHANGED,
    EVENT_PERSON_SETTINGS_CHANGED,
    EVENT_SETTINGS_CHANGED,
    PLATFORM_BINARY_SENSOR,
)
from .model import (
    AreaSettingsRegistry,
    EntitySettingsRegistry,
    PersonSettingsRegistry,
)
from .registry import EnhancedArea, EnhancedEntity, EnhancedPerson
from .share import get_base, get_hass

PLATFORM = PLATFORM_BINARY_SENSOR

CONF_UPDATED = "updated"

SCHEMA_UPDATE_AREA_SERVICE = vol.Schema(
    {
        vol.Required(ATTR_AREA_ID): vol.All(str, vol.Length(min=1)),
        vol.Optional(CONF_ICON): vol.Any(None, "", cv.icon),
        vol.Optional(ATTR_NAME): vol.Any(None, "", vol.All(str, vol.Length(min=1))),
        vol.Optional(CONF_SORT_ORDER): vol.Any(
            None,
            "",
            vol.All(
                vol.Coerce(float),
                vol.Range(min=DEFAULT_SORT_ORDER_MIN, max=DEFAULT_SORT_ORDER_MAX),
            ),
        ),
        vol.Optional(CONF_VISIBLE): vol.Boolean(),
    }
)

SCHEMA_UPDATE_ENTITY_SERVICE = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Optional(ATTR_AREA_ID): vol.Any(None, "", vol.All(str, vol.Length(min=1))),
        vol.Optional(CONF_SORT_ORDER): vol.Any(
            None,
            "",
            vol.All(
                vol.Coerce(float),
                vol.Range(min=DEFAULT_SORT_ORDER_MIN, max=DEFAULT_SORT_ORDER_MAX),
            ),
        ),
        vol.Optional(CONF_ENTITY_TYPE): vol.Any(
            None, "", vol.All(str, vol.Length(min=1))
        ),
        vol.Optional(CONF_VISIBLE): vol.Boolean(),
    }
)

SCHEMA_UPDATE_PERSON_SERVICE = vol.Schema(
    {
        vol.Required(CONF_ID): vol.All(str, vol.Length(min=1)),
        vol.Optional(ATTR_NAME): vol.Any(None, "", vol.All(str, vol.Length(min=1))),
        vol.Optional(CONF_SORT_ORDER): vol.Any(
            None,
            "",
            vol.All(
                vol.Coerce(float),
                vol.Range(min=DEFAULT_SORT_ORDER_MIN, max=DEFAULT_SORT_ORDER_MAX),
            ),
        ),
        vol.Optional(CONF_VISIBLE): vol.Boolean(),
    }
)


@websocket_api.websocket_command(
    {
        vol.Required("type"): "enhanced_templates_area_settings",
        vol.Required("area_id"): cv.string,
    }
)
@websocket_api.async_response
async def websocket_get_area_settings(hass: HomeAssistant, connection: str, msg: dict):
    """Get area settings for an area from a websocket connection."""

    area = EnhancedArea(msg["area_id"])
    if area.area_entry is None:
        connection.send_error(msg["id"], "area_not_found", "Area not found")

    connection.send_result(msg["id"], area.as_dict())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "enhanced_templates_entity_settings",
        vol.Required("entity_id"): cv.entity_id,
    }
)
@websocket_api.async_response
async def websocket_get_entity_settings(
    hass: HomeAssistant, connection: str, msg: dict
):
    """Get entity settings for an entity from a websocket connection."""

    entity = EnhancedEntity(msg["entity_id"])
    if entity.entity_state is None:
        connection.send_error(msg["id"], "entity_not_found", "Entity not found")

    connection.send_result(msg["id"], entity.as_dict())


@websocket_api.websocket_command(
    {
        vol.Required("type"): "enhanced_templates_person_settings",
        vol.Required("person_id"): cv.string,
    }
)
@websocket_api.async_response
async def websocket_get_person_settings(
    hass: HomeAssistant, connection: str, msg: dict
):
    """Get person settings for a person from a websocket connection."""

    person = EnhancedPerson(msg["person_id"])
    if person.person_entry is None:
        connection.send_error(msg["id"], "person_not_found", "Person not found")

    connection.send_result(msg["id"], person.as_dict())


async def setup_settings() -> None:
    """Initialize the settings and websocket api."""

    await update_settings()

    register = get_hass().components.websocket_api.async_register_command
    register(websocket_get_area_settings)
    register(websocket_get_entity_settings)
    register(websocket_get_person_settings)


async def update_settings() -> None:
    """Update the domain settings entries."""

    await update_area_settings()
    await update_entity_settings()
    await update_person_settings()


async def _get_data(store_name: str) -> dict:
    base = get_base()
    store = Store(base.hass, 1, f"{DOMAIN}.{store_name}")
    data: Optional[AreaSettingsRegistry] = await store.async_load()

    if data is None:
        data = {}

    return data


async def update_area_settings() -> None:
    """Update the area domain data entries."""

    get_base().areas = await _get_data(CONF_AREAS)


async def update_entity_settings() -> None:
    """Update the entity domain data entries."""

    get_base().entities = await _get_data(CONF_ENTITIES)


async def update_person_settings() -> None:
    """Update the person domain data entries."""

    get_base().persons = await _get_data(CONF_PERSONS)


async def save_setting(setting_type: str, call: ServiceCall) -> None:
    """Wrapper for all save setting services."""

    updated: bool = False

    if setting_type == CONF_AREA:
        updated = await _update_area(call) or updated

    if setting_type == CONF_ENTITY:
        updated = await _update_entity(call) or updated

    if setting_type == CONF_PERSON:
        updated = await _update_person(call) or updated

    if updated:
        get_base().hass.bus.fire(EVENT_SETTINGS_CHANGED)


async def remove_area_settings(area_id: str) -> None:
    """Remove the settings for an area."""

    hass = get_base().hass
    store = Store(hass, 1, f"{DOMAIN}.{CONF_AREAS}")
    data: Optional[AreaSettingsRegistry] = await store.async_load()

    if area_id in data:
        del data[area_id]

    await store.async_save(data)


async def remove_area_from_entities(area_id: str) -> None:
    """Remove the area_id from all entities."""

    hass = get_base().hass
    store = Store(hass, 1, f"{DOMAIN}.{CONF_ENTITIES}")
    data: Optional[EntitySettingsRegistry] = await store.async_load()

    to_delete = []

    for entity_id in data.keys():
        if data[entity_id].get(ATTR_AREA_ID) == area_id:
            if len(data[entity_id]) == 1:
                to_delete.append(entity_id)
            else:
                del data[entity_id][ATTR_AREA_ID]

    for entity_id in to_delete:
        del data[entity_id]

    await store.async_save(data)


async def remove_entity_settings(entity_id: str) -> None:
    """Remove the settings for an entity."""

    hass = get_base().hass
    store = Store(hass, 1, f"{DOMAIN}.{CONF_ENTITIES}")
    data: Optional[EntitySettingsRegistry] = await store.async_load()

    if entity_id in data:
        del data[entity_id]

    await store.async_save(data)


async def _update_area(call: ServiceCall) -> bool:
    """Update the settings for an area."""

    hass = get_base().hass
    store = Store(hass, 1, f"{DOMAIN}.{CONF_AREAS}")
    data: Optional[AreaSettingsRegistry] = await store.async_load()

    if data is None:
        data = {}
    data[CONF_UPDATED] = False

    area = EnhancedArea(call.data.get(ATTR_AREA_ID))

    await _update_key_value(data, call, area.id, ATTR_NAME, area.original_name)
    await _update_key_value(data, call, area.id, CONF_ICON, DEFAULT_AREA_ICON)
    await _update_key_value(data, call, area.id, CONF_SORT_ORDER, DEFAULT_SORT_ORDER)
    await _update_key_value(data, call, area.id, CONF_VISIBLE, True)

    if await _store_data(store, data, area.id):
        hass.bus.fire(
            EVENT_AREA_SETTINGS_CHANGED,
            {CONF_ACTION: CONF_UPDATE, ATTR_AREA_ID: area.id},
        )
        return True

    return False


async def _update_entity(call: ServiceCall) -> bool:
    """Update the settings for an entity."""

    hass = get_base().hass
    store = Store(hass, 1, f"{DOMAIN}.{CONF_ENTITIES}")
    data: Optional[EntitySettingsRegistry] = await store.async_load()
    if data is None:
        data = {}
    data[CONF_UPDATED] = False

    entity_id: str = call.data.get(CONF_ENTITY_ID)
    entity = EnhancedEntity(entity_id)

    await _update_key_value(
        data, call, entity_id, ATTR_AREA_ID, entity[CONF_ORIGINAL_AREA_ID]
    )
    await _update_key_value(data, call, entity_id, CONF_SORT_ORDER, DEFAULT_SORT_ORDER)
    await _update_key_value(
        data,
        call,
        entity_id,
        CONF_ENTITY_TYPE,
        entity[CONF_ORIGINAL_ENTITY_TYPE],
    )
    await _update_key_value(data, call, entity_id, CONF_VISIBLE, True)

    if await _store_data(store, data, entity_id):
        hass.bus.fire(
            EVENT_ENTITY_SETTINGS_CHANGED,
            {CONF_ACTION: CONF_UPDATE, ATTR_AREA_ID: entity_id},
        )
        return True

    return False


async def _update_person(call: ServiceCall) -> bool:
    """Update the settings for a person."""

    hass = get_base().hass
    store = Store(hass, 1, f"{DOMAIN}.{CONF_PERSONS}")
    data: Optional[PersonSettingsRegistry] = await store.async_load()

    if data is None:
        data = {}
    data[CONF_UPDATED] = False

    person = EnhancedPerson(call.data.get(CONF_ID))

    await _update_key_value(data, call, person.id, ATTR_NAME, person.original_name)
    await _update_key_value(data, call, person.id, CONF_SORT_ORDER, DEFAULT_SORT_ORDER)
    await _update_key_value(data, call, person.id, CONF_VISIBLE, True)

    if await _store_data(store, data, person.id):
        hass.bus.fire(
            EVENT_PERSON_SETTINGS_CHANGED,
            {CONF_ACTION: CONF_UPDATE, CONF_ID: person.id},
        )
        return True

    return False


async def _store_data(store: Store, data: dict, object_key: str) -> bool:
    """Write data to a store."""

    if data[CONF_UPDATED]:
        del data[CONF_UPDATED]
        if len(data[object_key].keys()) == 0:
            del data[object_key]

        await store.async_save(data)
        return True

    return False


async def _update_key_value(
    data: dict,
    call: ServiceCall,
    object_key: str,
    field_key: str,
    default_value: Optional[Union[List[Any], Any]] = None,
    remove_if_default: bool = True,
) -> None:
    """Update a value in data based on object and filed keys."""

    if field_key not in call.data:
        return

    new_value: Any = call.data.get(field_key)
    if new_value == "":
        new_value = None

    # Convert integers from strings
    if field_key in [CONF_SORT_ORDER] and new_value is not None:
        new_value = int(float(new_value))

    field_key_persisted: bool = field_key in data.get(object_key, {})
    new_value_is_default: bool = False

    if isinstance(default_value, list):
        new_value_is_default = new_value is None or new_value in default_value
    else:
        new_value_is_default = new_value is None or new_value == default_value

    if remove_if_default and new_value_is_default:
        if field_key_persisted:
            del data[object_key][field_key]
            data[CONF_UPDATED] = True
        return

    old_value: Any = data.get(object_key, {}).get(field_key)

    if new_value == old_value:
        return

    if object_key not in data:
        data[object_key] = {}

    data[object_key][field_key] = new_value
    data[CONF_UPDATED] = True
