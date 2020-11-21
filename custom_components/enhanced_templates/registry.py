"""Setup and manage area or entity registries."""
import re
from typing import Callable, Dict, Iterable, List, Optional, TypedDict, Union
import attr

from homeassistant.const import ATTR_AREA_ID, CONF_ICON, CONF_NAME
from homeassistant.core import State

from homeassistant.helpers.area_registry import AreaEntry, AreaRegistry
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry

from .const import (
    CONF_ENTITY_TYPE,
    CONF_SORT_ORDER,
    CONF_VISIBLE,
    DEFAULT_AREA_ICON,
    DEFAULT_SORT_ORDER,
    PLATFORM_BINARY_SENSOR,
)
from .share import get_base, get_hass

PLATFORM = PLATFORM_BINARY_SENSOR


async def setup_registry() -> None:
    """Setup registry."""

    get_base().area_registry = _areas_registry_data()


class AreaSettingsEntry(TypedDict, total=False):
    """Model for area settings stored in the store."""

    name: str
    icon: str
    original_name: str
    sort_order: int
    visible: bool


AreaSettingsRegistry = Dict[str, AreaSettingsEntry]


@attr.s(auto_attribs=True)
class EnhancedArea:
    """Model for an Area."""

    id: str = None
    area_settings: Optional[AreaSettingsEntry] = None
    area_entry: Optional[AreaEntry] = None

    @area_settings.default
    def _default_entity_settings(self) -> AreaSettingsEntry:
        """If the settings are None find the settings and provide an empty dictionary if None."""

        settings = self.area_settings
        if settings is None:
            settings = get_base().areas.get(self.id)

        return settings if settings is not None else {}

    @area_entry.default
    def _default_area_entry(self) -> Optional[AreaEntry]:
        """If the entry is None, find the entry if it exists."""

        entry = self.area_entry
        if entry is None:
            registry: AreaRegistry = get_hass().data["area_registry"]
            entry = registry.async_get_area(self.id)

        return entry

    @property
    def id(self) -> str:
        """Area ID from the HA area registry"""

        return self.area_entry.id

    @property
    def name(self) -> str:
        """Name of the area, from settings first and then the HA area registry."""

        return self.area_settings.get(CONF_NAME, self.area_entry.name)

    @property
    def original_name(self) -> str:
        """Name of the area from th HA area registry."""

        return self.area_entry.name

    @property
    def icon(self) -> str:
        """Icon from settings or the default icon."""

        return self.area_settings.get(CONF_ICON, DEFAULT_AREA_ICON)

    @property
    def sort_order(self) -> int:
        """Sort order from settings or the default."""

        return self.area_settings.get(CONF_SORT_ORDER, DEFAULT_SORT_ORDER)

    @property
    def visible(self) -> bool:
        """Visible from settings or the default (True)."""

        return self.area_settings.get(CONF_VISIBLE, True)


class EntitySettingsEntry(TypedDict, total=False):
    """Model for entity settings stored in the store."""

    area_id: str
    original_area_id: str
    name: str
    entity_type: str
    original_entity_type: str
    sort_order: int
    visible: bool


EntitySettingsRegistry = Dict[str, EntitySettingsEntry]


@attr.s(auto_attribs=True)
class EnhancedEntity:
    """Model for entity settings stored in IntegrationBase."""

    entity_id: str = None
    entity_settings: Optional[EntitySettingsEntry] = None
    entity_state: Optional[State] = None
    entity_entry: Optional[RegistryEntry] = None

    @entity_settings.default
    def _default_entity_settings(self) -> EntitySettingsEntry:
        """If the settings are None find the settings and provide an empty dictionary if None."""

        settings = self.entity_settings
        if settings is None:
            settings = get_base().entities.get(self.entity_id)

        return settings if settings is not None else {}

    @entity_state.default
    def _default_entity_state(self) -> State:
        """If the state is None, find the state."""

        state = self.entity_state
        if state is None:
            state = get_hass().states.get(self.entity_id)

        return state

    @entity_entry.default
    def _default_entity_entry(self) -> Optional[RegistryEntry]:
        """If the entry is None, find the entry if it exists."""

        entry = self.entity_entry
        if entry is None:
            registry: EntityRegistry = get_hass().data["entity_registry"]
            entry = registry.async_get(self.entity_id)

        return entry

    @property
    def area_id(self) -> Optional[str]:
        """Area ID from settings first, then the entry, then inferred from the entity ID."""

        id: Optional[str] = self.entity_settings.get(ATTR_AREA_ID)

        if id is None and self.entity_entry is not None:
            id = self.entity_entry.area_id

        if id is None:
            id = self._match_area_with_entity_id()

        return id

    @property
    def original_area_id(self) -> Optional[str]:
        """Area ID from the entry."""

        return self.entity_entry.area_id if self.entity_entry is not None else None

    @property
    def name(self) -> str:
        """Friendly name for entity from the state or inferred from the entity ID."""

        entity_name = self.entity_state.name if self.entity_state is not None else None

        if entity_name is None:
            entity_name = self.entity_id.split(".")[-1].replace("_", " ").title()

        return entity_name

    @property
    def domain(self) -> str:
        """Domain of the entity."""

        return self.entity_id.split(".")[0]

    @property
    def original_entity_type(self) -> str:
        """Original entity type inferred from domain."""

        return self._original_entity_type()

    @property
    def entity_type(self) -> str:
        """Entity type from settings or original entity type."""

        self.entity_settings.get(CONF_ENTITY_TYPE, self.original_entity_type)

    @property
    def sort_order(self) -> int:
        """Sort order from settings or the default."""

        return self.entity_settings.get(CONF_SORT_ORDER, DEFAULT_SORT_ORDER)

    @property
    def visible(self) -> bool:
        """Visible from settings or the default (True)."""

        return self.entity_settings.get(CONF_VISIBLE, True)

    @property
    def disabled(self) -> bool:
        """Disabled from the entry of the default (False)."""

        return self.entity_entry.disabled if self.entity_entry is not None else False

    def _match_area_with_entity_id(self) -> Optional[str]:
        """
        Match and area with an entity by checking if the area name is at the
        beginning of the entity ID.
        """

        areas = get_base().area_registry

        if areas is None:
            return None

        for area in areas:
            name = area.name.lower().replace(" ", "_")
            quote = "'"
            regex = f"(all_)?({name.replace(quote, '')}|{name.replace(quote, '_')})_"
            if re.match(regex, self.entity_id.split(".")[-1]):
                return area.id

        return None

    def _original_entity_type(self) -> str:
        """Entity type from defined maps in const.py or the entity domain."""

        domain = self.domain

        # def binary_sensors() -> str:
        #     return BINARY_SENSOR_CLASS_MAP.get(
        #         entity.attributes.get("device_class"),
        #         BINARY_SENSOR_CLASS_MAP.get(CONF_DEFAULT, domain),
        #     )

        # def covers() -> str:
        #     return COVER_CLASS_MAP.get(
        #         entity.attributes.get("device_class"),
        #         COVER_CLASS_MAP.get(CONF_DEFAULT, domain),
        #     )

        # def sensors() -> str:
        #     return SENSOR_CLASS_MAP.get(
        #         entity.attributes.get("device_class"),
        #         SENSOR_CLASS_MAP.get(CONF_DEFAULT, domain),
        #     )

        def other() -> str:
            # return PLATFORM_MAP.get(domain, PLATFORM_MAP.get(CONF_DEFAULT, domain))
            return domain

        switcher: Dict[str, Callable[[], str]] = {
            # "binary_sensor": binary_sensors,
            # "cover": covers,
            # "sensor": sensors,
        }

        # if entity is None:
        #     return other()

        return switcher.get(domain, other)()


def _areas_registry_data() -> Iterable[AreaEntry]:
    area_registry: AreaRegistry = get_base().hass.data["area_registry"]
    return sorted(area_registry.async_list_areas(), key=lambda entry: entry.name)


# def get_area(area_id: str, area_entry: Optional[AreaEntry] = None) -> EnhancedArea:
#     base = get_base()
#     if area_entry is None:
#         registry: AreaRegistry = base.hass.data["area_registry"]
#         area_entry = registry.async_get_area(area_id)

#     area_settings = base.areas.get(area_id)

#     return EnhancedArea(area_entry=area_entry, area_settings=area_settings)


def get_areas(
    area_id: str = None, include_hidden: bool = False
) -> Union[EnhancedArea, List[EnhancedArea]]:
    if area_id is not None:
        return EnhancedArea(area_id)

    areas = []
    for area in get_base().area_registry:
        enhanced_area = EnhancedArea(area.id, area_entry=area)
        if include_hidden or enhanced_area.visible:
            areas.append(enhanced_area)

    return areas


# def get_entity(
#     entity_id: str,
#     entity_entry: Optional[RegistryEntry] = None,
# ) -> EnhancedEntity:
#     base = get_base()
#     if entity_entry is None:
#         registry: EntityRegistry = base.hass.data["entity_registry"]
#         entity_entry = registry.async_get(entity_id)

#     entity_settings = base.entities.get(entity_id, {})
#     entity_state = base.hass.states.get(entity_id)
#     entity_name = entity_state.name if entity_state is not None else None
#     entity_type = original_entity_type(entity_id)
#     if entity_name is None:
#         entity_name = (
#             entity_entry.name
#             if entity_entry is not None and entity_entry.name is not None
#             else entity_id.split(".")[-1].replace("_", " ").title()
#         )

#     if areas is None:
#         areas = _areas_registry_data()

#     area_id = entity_settings.get(ATTR_AREA_ID)
#     if area_id is None:
#         if entity_entry and entity_entry.area_id is not None:
#             area_id = entity_entry.area_id
#         else:
#             area_id = match_area_with_entity_id(entity_id, areas)

#     return EnhancedEntity(
#         entity_id=entity_id,
#         area_id=area_id,
#         original_area_id=entity_entry.area_id if entity_entry is not None else None,
#         name=entity_name,
#         entity_type=entity_settings.get(CONF_TYPE, entity_type),
#         original_entity_type=entity_type,
#         sort_order=entity_settings.get(CONF_SORT_ORDER, DEFAULT_SORT_ORDER),
#     )
# return {
#     CONF_ENTITY_ID: entity_id,
#     ATTR_AREA_ID: area_id,
#     CONF_ORIGINAL_AREA_ID: entity_entry.area_id
#     if entity_entry is not None
#     else None,
#     ATTR_NAME: entity_name,
#     CONF_TYPE: entity_settings.get(CONF_TYPE, entity_type),
#     CONF_ORIGINAL_TYPE: entity_type,
#     CONF_SORT_ORDER: entity_settings.get(CONF_SORT_ORDER, DEFAULT_SORT_ORDER),
#     CONF_VISIBLE: entity_settings.get(CONF_VISIBLE, True),
#     CONF_DISABLED: entity_entry.disabled if entity_entry is not None else False,
# }


def get_entities(
    entity_id: str = None, include_hidden: bool = False, include_disabled: bool = False
) -> List[EnhancedEntity]:
    if entity_id is not None:
        return EnhancedEntity(entity_id)

    entities = []
    for entity_id in get_base().hass.states.async_entity_ids():
        enhanced_entity = EnhancedEntity(entity_id)
        if (include_hidden or enhanced_entity.visible) and (
            include_disabled or not enhanced_entity.disabled
        ):
            entities.append(enhanced_entity)

    return entities


# async def add_entity_to_registry(entity_id: str) -> None:
#     """Add an entity to the registry"""

#     base = get_base()

#     entities = base.entities
#     entity: Optional[RegistryEntry] = base.hass.data["entity_registry"].async_get(
#         entity_id
#     )
#     entity_type = original_entity_type(entity_id)

#     if entity.disabled:
#         return

#     entities.append(
#         {
#             CONF_ENTITY_ID: entity_id,
#             ATTR_AREA_ID: entity.area_id,
#             CONF_ORIGINAL_AREA_ID: entity.area_id,
#             ATTR_NAME: entity.name,
#             CONF_TYPE: entity_type,
#             CONF_ORIGINAL_TYPE: entity_type,
#             CONF_SORT_ORDER: DEFAULT_SORT_ORDER,
#             CONF_VISIBLE: True,
#         }
#     )


# async def remove_entity_from_registry(entity_id: str) -> None:
#     """Remove an entity from the registry"""

#     base = get_base()

#     entities = base.entities
#     for entity in entities:
#         if entity[CONF_ENTITY_ID] == entity_id:
#             entities.remove(entity)
#             break


# async def update_entity_from_registry(entity_id: str) -> None:
#     """Update an entity from the registry"""

#     base = get_base()
#     hass = base.hass
#     store = Store(hass, 1, f"{DOMAIN}.{CONF_ENTITIES}")
#     data: Optional[EntitySettingsRegistry] = await store.async_load()
#     if data is None:
#         data = {}

#     entities = base.entities
#     entity: Optional[RegistryEntry] = hass.data["entity_registry"].async_get(entity_id)

#     entity_data = data.get(entity_id, {})
#     entity_state = base.hass.states.get(entity_id)
#     entity_name = entity_state.name if entity_state is not None else None
#     entity_type = original_entity_type(entity_id)
#     if entity_name is None:
#         entity_name = (
#             entity.name
#             if entity.name is not None
#             else entity.entity_id.split(".")[-1].replace("_", " ").title()
#         )

#     await remove_entity_from_registry(entity_id)

#     entities.append(
#         {
#             CONF_ENTITY_ID: entity.entity_id,
#             ATTR_AREA_ID: entity_data.get(ATTR_AREA_ID, entity.area_id),
#             CONF_ORIGINAL_AREA_ID: entity.area_id,
#             ATTR_NAME: entity_name,
#             CONF_TYPE: entity_data.get(CONF_TYPE, entity_type),
#             CONF_ORIGINAL_TYPE: entity_type,
#             CONF_SORT_ORDER: entity_data.get(CONF_SORT_ORDER, DEFAULT_SORT_ORDER),
#             CONF_VISIBLE: entity_data.get(CONF_VISIBLE, True),
#         }
#     )


# async def hass_areas() -> List[AreaSettings]:
#     """A dictionary list for the HA area registry used for this integrations domain data."""

#     hass = get_base().hass

#     areas: List[AreaSettings] = []  # make as an array so it can be sorted

#     store = Store(hass, 1, f"{DOMAIN}.{CONF_AREAS}")
#     data: Optional[AreaSettingsRegistry] = await store.async_load()
#     if data is None:
#         data = {}

#     # Sorted by original name because this is what is needed for the picker
#     area_registry: AreaRegistry = hass.data["area_registry"]
#     areas_sorted: Iterable[AreaEntry] = sorted(
#         area_registry.async_list_areas(), key=lambda entry: entry.name
#     )

#     for area in areas_sorted:
#         area_data = data.get(area.id, {})
#         area_item: AreaSettings = {
#             ATTR_ID: area.id,
#             ATTR_NAME: area_data.get(CONF_NAME, area.name),
#             CONF_ICON: area_data.get(CONF_ICON, DEFAULT_AREA_ICON),
#             CONF_ORIGINAL_NAME: area.name,
#             CONF_SORT_ORDER: area_data.get(CONF_SORT_ORDER, DEFAULT_SORT_ORDER),
#             CONF_VISIBLE: area_data.get(CONF_VISIBLE, True),
#         }
#         areas.append(area_item)

#     return areas


# def original_entity_type(entity_id: str) -> str:
#     """Entity type from defined maps in const.py or the entity domain."""

#     entity = get_base().hass.states.get(entity_id)
#     domain = entity.domain if entity is not None else entity_id.split(".")[0]

#     # def binary_sensors() -> str:
#     #     return BINARY_SENSOR_CLASS_MAP.get(
#     #         entity.attributes.get("device_class"),
#     #         BINARY_SENSOR_CLASS_MAP.get(CONF_DEFAULT, domain),
#     #     )

#     # def covers() -> str:
#     #     return COVER_CLASS_MAP.get(
#     #         entity.attributes.get("device_class"),
#     #         COVER_CLASS_MAP.get(CONF_DEFAULT, domain),
#     #     )

#     # def sensors() -> str:
#     #     return SENSOR_CLASS_MAP.get(
#     #         entity.attributes.get("device_class"),
#     #         SENSOR_CLASS_MAP.get(CONF_DEFAULT, domain),
#     #     )

#     def other() -> str:
#         # return PLATFORM_MAP.get(domain, PLATFORM_MAP.get(CONF_DEFAULT, domain))
#         return domain

#     switcher: Dict[str, Callable[[], str]] = {
#         # "binary_sensor": binary_sensors,
#         # "cover": covers,
#         # "sensor": sensors,
#     }

#     if entity is None:
#         return other()

#     return switcher.get(domain, other)()


# async def hass_entities() -> List[EntitySettings]:
#     """A dictionary list for the HA entity registry used for this integrations domain data."""

#     hass = get_base().hass

#     entities: List[EntitySettings] = []  # make as an array so it can be sorted
#     entities_processed: List[
#         str
#     ] = []  # keep track of ids so they don't get processed twice

#     store = Store(hass, 1, f"{DOMAIN}.{CONF_ENTITIES}")
#     data: Optional[EntitySettingsRegistry] = await store.async_load()
#     if data is None:
#         data = {}

#     area_registry: AreaRegistry = hass.data["area_registry"]
#     areas = area_registry.async_list_areas()

#     # Iterate through the registry first.
#     for area in areas:
#         devices: Iterable[
#             DeviceEntry
#         ] = hass.helpers.device_registry.async_entries_for_area(
#             hass.data["device_registry"], area.id
#         )
#         for device in devices:
#             entity_entries: Iterable[
#                 RegistryEntry
#             ] = hass.helpers.entity_registry.async_entries_for_device(
#                 hass.data["entity_registry"], device.id
#             )
#             for entity in entity_entries:
#                 if entity.disabled:
#                     continue

#                 entity_data = data.get(entity.entity_id, {})
#                 entity_state = hass.states.get(entity.entity_id)
#                 entity_name = entity_state.name if entity_state is not None else None
#                 entity_type = original_entity_type(entity.entity_id)
#                 if entity_name is None:
#                     entity_name = (
#                         entity.name
#                         if entity.name is not None
#                         else entity.entity_id.split(".")[-1].replace("_", " ").title()
#                     )
#                 entity_item: EntitySettings = {
#                     CONF_ENTITY_ID: entity.entity_id,
#                     ATTR_AREA_ID: entity_data.get(ATTR_AREA_ID, area.id),
#                     CONF_ORIGINAL_AREA_ID: area.id,
#                     ATTR_NAME: entity_name,
#                     CONF_TYPE: entity_data.get(CONF_TYPE, entity_type),
#                     CONF_ORIGINAL_TYPE: entity_type,
#                     CONF_SORT_ORDER: entity_data.get(
#                         CONF_SORT_ORDER, DEFAULT_SORT_ORDER
#                     ),
#                     CONF_VISIBLE: entity_data.get(CONF_VISIBLE, True),
#                 }
#                 entities.append(entity_item)
#                 entities_processed.append(entity.entity_id)

#     # Iterate through the state machine incase anything isn't listed in the registry.
#     for entity_id in hass.states.async_entity_ids():
#         if entity_id in entities_processed:
#             continue

#         entity_data = data.get(entity_id, {})
#         hass_state = hass.states.get(entity_id)
#         entity_type = original_entity_type(entity_id)
#         area_id = entity_data.get(
#             ATTR_AREA_ID, match_area_with_entity_id(entity_id, areas)
#         )
#         entity_item: EntitySettings = {
#             CONF_ENTITY_ID: entity_id,
#             ATTR_AREA_ID: area_id,
#             CONF_ORIGINAL_AREA_ID: None,
#             ATTR_NAME: hass_state.name,
#             CONF_TYPE: entity_data.get(CONF_TYPE, entity_type),
#             CONF_ORIGINAL_TYPE: entity_type,
#             CONF_SORT_ORDER: entity_data.get(CONF_SORT_ORDER, DEFAULT_SORT_ORDER),
#             CONF_VISIBLE: entity_data.get(CONF_VISIBLE, True),
#         }
#         entities.append(entity_item)

#     return sorted(entities, key=lambda entity: entity[ATTR_NAME])
