"""Setup and manage area or entity registries."""
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Union
import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.const import (
    ATTR_AREA_ID,
    CONF_ICON,
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.area_registry import AreaEntry, AreaRegistry
from homeassistant.helpers.device_registry import DeviceRegistry, DeviceEntry
from homeassistant.helpers.entity_registry import EntityRegistry, RegistryEntry

from .const import (
    CONF_ENTITY_TYPE,
    CONF_SORT_ORDER,
    CONF_VISIBLE,
    DEFAULT_AREA_ICON,
    DEFAULT_SORT_ORDER,
    PLATFORM_BINARY_SENSOR,
)
from .model import (
    AreaSettingsEntry,
    EntitySettingsEntry,
)
from .share import get_base, get_hass

PLATFORM = PLATFORM_BINARY_SENSOR

CONF_DEFAULT = "default"
ENTITY_TYPES = []
SENSOR_CLASS_MAP = {CONF_DEFAULT: "sensor"}
BINARY_SENSOR_CLASS_MAP = {CONF_DEFAULT: "binary_sensor"}
COVER_CLASS_MAP = {CONF_DEFAULT: "cover"}
PLATFORM_MAP = {}


async def setup_registry() -> None:
    """Setup registry."""

    update_registry()

    register = get_hass().components.websocket_api.async_register_command
    register(websocket_get_entity_types)


def update_registry() -> None:
    """Update registry."""

    update_area_registry()


def update_area_registry() -> None:
    """Update area registry."""

    get_base().area_registry = _areas_registry_data()


class EnhancedArea:
    """Model for an Area."""

    def __init__(
        self,
        id: str,
        area_settings: Optional[AreaSettingsEntry] = None,
        area_entry: Optional[AreaEntry] = None,
    ) -> None:
        self.id = id
        self.area_settings = self._get_area_settings(area_settings)
        self.area_entry = self._get_area_entry(area_entry)

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

    def _get_area_settings(
        self, area_settings: Optional[AreaSettingsEntry] = None
    ) -> AreaSettingsEntry:
        """If the settings are None find the settings and provide an empty dictionary if None."""

        settings = area_settings
        if settings is None:
            settings = get_base().areas.get(self.id)

        return settings if settings is not None else {}

    def _get_area_entry(
        self, area_entry: Optional[AreaEntry] = None
    ) -> Optional[AreaEntry]:
        """If the entry is None, find the entry if it exists."""

        entry = area_entry
        if entry is None:
            registry: AreaRegistry = get_hass().data["area_registry"]
            entry = registry.async_get_area(self.id)

        return entry

    def __getitem__(self, item: str) -> Any:
        """Get and attribute, needed for Jinja templates."""

        return getattr(self, item)

    def __repr__(self):
        """Representation of an EnhancedArea."""

        return (
            f"<EnhancedArea id={self.id}, "
            f"name={self.name}, "
            f"original_name={self.original_name}, "
            f"icon={self.icon}, "
            f"sort_order={self.sort_order}, "
            f"visible={self.visible}>"
        )

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "original_name": self.original_name,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "visible": self.visible,
        }


class EnhancedEntity:
    """Model for entity settings stored in IntegrationBase."""

    def __init__(
        self,
        entity_id: str,
        entity_settings: EntitySettingsEntry = None,
        entity_state: State = None,
        entity_entry: RegistryEntry = None,
        device_entry: DeviceEntry = None,
    ):
        self.entity_id = entity_id
        self.entity_settings = self._get_entity_settings(entity_settings)
        self.entity_state = self._get_entity_state(entity_state)
        self.entity_entry = self._get_entity_entry(entity_entry)
        self.device_entry = self._get_device_entry(device_entry)

    @property
    def area_id(self) -> Optional[str]:
        """Area ID from settings first, then the entry, then inferred from the entity ID."""

        id: Optional[str] = self.entity_settings.get(ATTR_AREA_ID)

        if id is None and self.original_area_id is not None:
            id = self.original_area_id

        if id is None:
            id = self._match_area_with_entity_id()

        return id

    @property
    def area(self) -> Optional[EnhancedArea]:
        """Get the EnhancedArea that this entity belongs to."""

        area_id = self.area_id

        if area_id is None:
            return None

        return EnhancedArea(self.area_id)

    @property
    def original_area_id(self) -> Optional[str]:
        """Area ID from the entry."""

        if self.entity_entry is not None and self.entity_entry.area_id is not None:
            return self.entity_entry.area_id

        if self.device_entry is not None and self.device_entry.area_id is not None:
            return self.device_entry.area_id

        return None

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

        return self.entity_settings.get(CONF_ENTITY_TYPE, self.original_entity_type)

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

    @property
    def state(self):
        """Wrapper for entity_state."""

        return self.entity_state

    @property
    def entry(self):
        """Wrapper for entity_entry"""

        return self.entity_entry

    def _get_entity_settings(
        self, entity_settings: Optional[EntitySettingsEntry] = None
    ) -> EntitySettingsEntry:
        """If the settings are None find the settings and provide an empty dictionary if None."""

        settings = entity_settings
        if entity_settings is None:
            settings = get_base().entities.get(self.entity_id)

        return settings if settings is not None else {}

    def _get_entity_state(self, entity_state: Optional[State] = None) -> State:
        """If the state is None, find the state."""

        state = entity_state
        if state is None:
            state = get_hass().states.get(self.entity_id)

        return state

    def _get_device_entry(
        self, device_entry: Optional[DeviceEntry] = None
    ) -> Optional[DeviceEntry]:
        """If the entry is None, find the device if it exists."""

        entry = device_entry
        if entry is None and self.entity_entry is not None:
            registry: DeviceRegistry = get_hass().data["device_registry"]
            entry = registry.async_get(self.entity_entry.device_id)

        return entry

    def _get_entity_entry(
        self, entity_entry: Optional[RegistryEntry] = None
    ) -> Optional[RegistryEntry]:
        """If the entry is None, find the entry if it exists."""

        entry = entity_entry
        if entry is None:
            registry: EntityRegistry = get_hass().data["entity_registry"]
            entry = registry.async_get(self.entity_id)

        return entry

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
            regex = (
                f"(all_)?({name.replace(quote, '')}|{name.replace(quote, '_')})(_|$)"
            )
            if re.match(regex, self.entity_id.split(".")[-1]):
                return area.id

        return None

    def _original_entity_type(self) -> str:
        """Entity type from defined maps in const.py or the entity domain."""

        def binary_sensors() -> str:
            return BINARY_SENSOR_CLASS_MAP.get(
                self.state.attributes.get("device_class"),
                BINARY_SENSOR_CLASS_MAP.get(CONF_DEFAULT, self.domain),
            )

        def covers() -> str:
            return COVER_CLASS_MAP.get(
                self.state.attributes.get("device_class"),
                COVER_CLASS_MAP.get(CONF_DEFAULT, self.domain),
            )

        def sensors() -> str:
            return SENSOR_CLASS_MAP.get(
                self.state.attributes.get("device_class"),
                SENSOR_CLASS_MAP.get(CONF_DEFAULT, self.domain),
            )

        def other() -> str:
            return PLATFORM_MAP.get(
                self.domain, PLATFORM_MAP.get(CONF_DEFAULT, self.domain)
            )

        switcher: Dict[str, Callable[[], str]] = {
            "binary_sensor": binary_sensors,
            "cover": covers,
            "sensor": sensors,
        }

        return switcher.get(self.domain, other)()

    def __getitem__(self, item: str) -> Any:
        """Get and attribute, needed for Jinja templates."""

        return getattr(self, item)

    def __repr__(self):
        """Representation of EnhancedEntity"""

        return (
            f"<EnhancedEntity entity_id={self.entity_id}, "
            f"area_id={self.area_id}, "
            f"original_area_id={self.original_area_id}, "
            f"name={self.name}, "
            f"domain={self.domain}, "
            f"entity_type={self.entity_type}, "
            f"original_entity_type={self.original_entity_type}, "
            f"sort_order={self.sort_order}, "
            f"visible={self.visible}, "
            f"disabled={self.disabled}, "
            f"area={self.area}, "
            f"state={self.state}>"
        )

    def as_dict(self):
        return {
            "entity_id": self.entity_id,
            "area_id": self.area_id,
            "original_area_id": self.original_area_id,
            "name": self.name,
            "domain": self.domain,
            "entity_type": self.entity_type,
            "original_entity_type": self.original_entity_type,
            "sort_order": self.sort_order,
            "visible": self.visible,
            "disabled": self.disabled,
        }


@websocket_api.websocket_command(
    {vol.Required("type"): "enhanced_templates_entity_types"}
)
@websocket_api.async_response
async def websocket_get_entity_types(hass: HomeAssistant, connection: str, msg: dict):
    """Get entity types available to all entities."""

    connection.send_result(msg["id"], ENTITY_TYPES)


def _areas_registry_data() -> Iterable[AreaEntry]:
    area_registry: AreaRegistry = get_hass().data["area_registry"]
    return sorted(area_registry.async_list_areas(), key=lambda entry: entry.name)


def get_areas(
    area_id: str = None, include_hidden: bool = False
) -> Union[EnhancedArea, List[EnhancedArea]]:
    """Get all areas or a single area."""

    if area_id is not None:
        return EnhancedArea(area_id)

    areas = []
    for area in get_base().area_registry:
        enhanced_area = EnhancedArea(id=area.id, area_entry=area)
        if include_hidden or enhanced_area.visible:
            areas.append(enhanced_area)

    return areas


def get_entities(
    entity_id: str = None, include_hidden: bool = False, include_disabled: bool = False
) -> List[EnhancedEntity]:
    """Get all or a single area."""

    if entity_id is not None:
        return EnhancedEntity(entity_id)

    entities = []
    for entity_id in get_hass().states.async_entity_ids():
        enhanced_entity = EnhancedEntity(entity_id)
        if (include_hidden or enhanced_entity.visible) and (
            include_disabled or not enhanced_entity.disabled
        ):
            entities.append(enhanced_entity)

    return entities
