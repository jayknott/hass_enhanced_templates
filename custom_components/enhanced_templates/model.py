"""Base Integration class."""
import logging
from typing import Dict, Iterable, List, Optional, TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaEntry

from .const import DOMAIN


class AreaSettingsEntry(TypedDict, total=False):
    """Model for area settings stored in the store."""

    name: str
    icon: str
    original_name: str
    sort_order: int
    visible: bool


AreaSettingsRegistry = Dict[str, AreaSettingsEntry]


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


class PersonSettingsEntry(TypedDict, total=False):
    """Model for person settings stored in the store."""

    name: str
    original_name: str
    sort_order: int
    visible: bool


PersonSettingsRegistry = Dict[str, PersonSettingsEntry]


class PersonEntry(TypedDict, total=False):
    """Model to mimic the data in the person registry in HA."""

    id: str
    name: str
    user_id: Optional[str]
    device_trackers: List[str]
    picture: Optional[str]


PersonRegistry = Iterable[PersonEntry]


class Configuration:
    """Configuration class."""

    config: dict = {}
    config_entry: dict = {}
    config_type: Optional[str] = None


class IntegrationBase:
    """Base Integration class."""

    hass: HomeAssistant = None
    log = logging.getLogger(f"custom_components.{DOMAIN}")

    area_registry: Iterable[AreaEntry] = []
    areas: AreaSettingsRegistry = {}
    configuration: Configuration = None
    entities: EntitySettingsRegistry = {}
    person_registry: Iterable[PersonEntry] = []
    persons: PersonSettingsRegistry = {}
