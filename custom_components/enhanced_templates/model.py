"""Base Integration class."""
import re
from custom_components.enhanced_templates.share import get_base
import attr
import logging
from typing import Iterable, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.area_registry import AreaEntry

from .const import DOMAIN
from .registry import EntitySettingsRegistry, AreaSettingsRegistry


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
    areas: AreaSettingsRegistry = []
    # built_in_entities: Dict[str, Type[Entity]] = {}
    configuration: Configuration = None
    entities: EntitySettingsRegistry = []
