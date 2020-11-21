"""Read and write area and entity settings in storage."""
from typing import Any, List, Optional, Union
import voluptuous as vol

from homeassistant.const import (
    ATTR_AREA_ID,
    ATTR_NAME,
    CONF_ENTITY_ID,
    CONF_ICON,
    CONF_ID,
    CONF_TYPE,
)
from homeassistant.core import ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import Store

from .const import (
    # ALL_ENTITY_TYPES,
    CONF_ACTION,
    CONF_AREA,
    CONF_AREA_NAME,
    CONF_AREAS,
    CONF_ENTITIES,
    CONF_ENTITY,
    CONF_ORIGINAL_AREA_ID,
    CONF_ORIGINAL_NAME,
    CONF_ORIGINAL_TYPE,
    CONF_SORT_ORDER,
    CONF_UPDATE,
    CONF_VISIBLE,
    DEFAULT_AREA_ICON,
    DEFAULT_SORT_ORDER,
    DOMAIN,
    EVENT_AREA_SETTINGS_CHANGED,
    EVENT_ENTITY_SETTINGS_CHANGED,
    EVENT_SETTINGS_CHANGED,
    PLATFORM_BINARY_SENSOR,
)
from .model import (
    AreaSettings,
    AreaSettingsRegistry,
    EntitySettings,
    EntitySettingsRegistry,
)
from .share import get_base

PLATFORM = PLATFORM_BINARY_SENSOR

CONF_UPDATED = "updated"

SCHEMA_UPDATE_AREA_SERVICE = vol.Schema(
    {
        vol.Required(CONF_AREA_NAME): vol.All(str, vol.Length(min=1)),
        vol.Optional(CONF_ICON): cv.icon,
        vol.Optional(ATTR_NAME): vol.All(str, vol.Length(min=1)),
        vol.Optional(CONF_SORT_ORDER): vol.All(str, vol.Length(min=1, max=8)),
        vol.Optional(CONF_VISIBLE): cv.boolean,
    }
)

SCHEMA_UPDATE_ENTITY_SERVICE = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
        vol.Optional(CONF_AREA_NAME): vol.All(str, vol.Length(min=0)),
        vol.Optional(CONF_SORT_ORDER): vol.All(str, vol.Length(min=1, max=8)),
        vol.Optional(CONF_TYPE): cv.string,
        vol.Optional(CONF_VISIBLE): cv.boolean,
    }
)


async def setup_settings() -> None:
    """Initialize the area and entity domain data entries."""

    await update_settings()


async def update_settings() -> None:
    """Update the area and entity domain data entries."""

    await update_area_settings()
    await update_entity_settings()


async def _get_data(store_name: str) -> dict:
    base = get_base()
    store = Store(base.hass, 1, f"{DOMAIN}.{store_name}")
    data: Optional[AreaSettingsRegistry] = await store.async_load()

    if data is None:
        data = {}

    return data


async def update_area_settings() -> None:
    """Update the area domain data entries."""

    get_base().areas = _get_data(CONF_AREAS)


async def update_entity_settings() -> None:
    """Update the entity domain data entries."""

    # get_base().entities = await hass_entities()
    get_base().entities = _get_data(CONF_ENTITIES)


async def save_setting(setting_type: str, call: ServiceCall) -> None:
    """Wrapper for all save setting services."""

    updated: bool = False

    # Have to do this because it comes from the template as a string
    if CONF_SORT_ORDER in call.data:
        try:
            int(float(call.data[CONF_SORT_ORDER]))
        except:
            raise vol.error.SchemaError("Expected an integer for sort_order.")

    if setting_type == CONF_AREA:
        updated = await _update_area(call) or updated

    if setting_type == CONF_ENTITY:
        updated = await _update_entity(call) or updated

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

    area_name: str = call.data.get(CONF_AREA_NAME)
    area_id = await _get_area_id_by_name(area_name)

    await _update_key_value(data, call, area_id, ATTR_NAME, area_name)
    await _update_key_value(data, call, area_id, CONF_ICON, DEFAULT_AREA_ICON)
    await _update_key_value(data, call, area_id, CONF_SORT_ORDER, DEFAULT_SORT_ORDER)
    await _update_key_value(data, call, area_id, CONF_VISIBLE, True)

    if await _store_data(store, data, area_id):
        hass.bus.fire(
            EVENT_AREA_SETTINGS_CHANGED,
            {CONF_ACTION: CONF_UPDATE, ATTR_AREA_ID: area_id},
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
    entity = _get_entity_by_id(entity_id)

    await _update_key_value(
        data, call, entity_id, CONF_AREA_NAME, entity[CONF_ORIGINAL_AREA_ID]
    )
    await _update_key_value(data, call, entity_id, CONF_SORT_ORDER, DEFAULT_SORT_ORDER)
    await _update_key_value(
        data, call, entity_id, CONF_TYPE, [entity[CONF_ORIGINAL_TYPE], None]
    )
    await _update_key_value(data, call, entity_id, CONF_VISIBLE, True)

    if await _store_data(store, data, entity_id):
        hass.bus.fire(
            EVENT_ENTITY_SETTINGS_CHANGED,
            {CONF_ACTION: CONF_UPDATE, ATTR_AREA_ID: entity_id},
        )
        return True

    return False


async def _get_area_id_by_name(area_name: Optional[str]) -> Optional[str]:
    """Get an area's ID by its name."""

    base = get_base()
    area: Optional[AreaSettings] = None

    if area_name is not None and area_name != "":
        area = next(
            (
                area_obj
                for area_obj in base.areas
                if area_obj[CONF_ORIGINAL_NAME] == area_name
            ),
            None,
        )
    else:
        return None

    if area is None:
        raise vol.error.SchemaError(
            f"Cannot update area because an area with name '{area_name}' doesn't exist"
        )

    return area[CONF_ID]


def _get_entity_by_id(entity_id: Optional[str]) -> Optional[EntitySettings]:
    """Get an EntitySettings object by its name."""

    base = get_base()
    entity: Optional[EntitySettings] = None

    if entity_id is not None and entity_id != "":
        entity = next(
            (
                entity_obj
                for entity_obj in base.entities
                if entity_obj[CONF_ENTITY_ID] == entity_id
            ),
            None,
        )
    else:
        return None

    if entity is None:
        raise vol.error.SchemaError(
            f"Cannot update entity because an entity with id '{entity_id}' doesn't exist"
        )

    return entity


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

    if object_key not in data:
        data[object_key] = {}

    new_value: Any = call.data.get(field_key)
    if new_value == "":
        new_value = None

    if field_key == CONF_AREA_NAME:
        field_key = ATTR_AREA_ID
        area_id = await _get_area_id_by_name(new_value)
        new_value = area_id

    old_value: Any = data[object_key].get(field_key)

    # Convert integers from strings
    if field_key in [CONF_SORT_ORDER]:
        new_value = int(float(new_value))

    field_key_persisted: bool = field_key in data[object_key]
    new_value_is_default: bool = False

    if isinstance(default_value, list):
        new_value_is_default = new_value in default_value
    else:
        new_value_is_default = new_value == default_value

    if remove_if_default and new_value_is_default:
        if field_key_persisted:
            del data[object_key][field_key]
            data[CONF_UPDATED] = True
        return

    if new_value == old_value:
        return

    data[object_key][field_key] = new_value
    data[CONF_UPDATED] = True
