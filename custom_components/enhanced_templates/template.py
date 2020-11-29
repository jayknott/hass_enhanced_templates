"""Extend the template options for HA."""

# from homeassistant.const import ATTR_ENTITY_ID
# from homeassistant.helpers.event import TrackTemplate
# from homeassistant.helpers.typing import TemplateVarsType
# from custom_components.enhanced_templates.const import EVENT_AREAS_CHANGED
# from homeassistant.core import Event
import jinja2
from typing import Optional

from homeassistant.helpers.template import (
    # RenderInfo,
    _ENVIRONMENT,
    # _RENDER_INFO,
    regex_match,
    regex_search,
    TemplateEnvironment,
)

from .registry import get_areas, get_entities
from .share import get_hass


async def setup_template() -> None:
    """Setup the template options."""

    hass = get_hass()

    jinja = hass.data[_ENVIRONMENT] = EnhancedTemplateEnvironment(hass)

    # Add a loader so Jinja can use files.
    jinja.loader = jinja2.FileSystemLoader("/")

    # Add the built-in HA regex filters as tests if they do not already exist
    if jinja.tests.get("regex_match") is None:
        jinja.tests["regex_match"] = regex_match
    if jinja.tests.get("regex_search") is None:
        jinja.tests["regex_search"] = regex_search

    # Add custom globals
    jinja.globals["areas"] = AreasTemplate()
    jinja.globals["entities"] = EntitiesTemplate()


class EnhancedTemplateEnvironment(TemplateEnvironment):
    """Class to override safe callables."""

    def is_safe_callable(self, obj):
        """Test if callback is safe."""

        return isinstance(
            obj, (AreasTemplate, EntitiesTemplate)
        ) or super().is_safe_callable(obj)

    def is_safe_attribute(self, obj, attr, value):
        """Test if attribute is safe."""

        if isinstance(obj, (AreasTemplate, EntitiesTemplate)):
            return not attr[0] == "_"

        return super().is_safe_attribute(obj, attr, value)


class AreasTemplate:
    """Class to expose all enhanced areas"""

    def __getattr__(self, id: Optional[str] = None, include_hidden: bool = False):
        """Return all the areas."""

        self._create_template_listener()
        return get_areas(id, include_hidden)

    __getitem__ = __getattr__

    def __iter__(self):
        self._create_template_listener()
        return iter(get_areas())

    def __len__(self):
        self._create_template_listener()
        return len(get_areas())

    def __call__(self, id: Optional[str] = None, include_hidden: bool = False):
        self._create_template_listener()
        return self.__getattr__(id, include_hidden)

    def __repr__(self) -> str:
        """Representation of all areas."""

        return "<template AllAreas>"

    def _create_template_listener(self):
        pass

        # TODO: Figure out how to listen for changes and update entities that
        #   use this template.

        # hass = get_hass()
        # render_info: RenderInfo = hass.data.get(_RENDER_INFO)

        # if render_info is None or render_info.template is None:
        #     return

        # hass.bus.async_listen(EVENT_AREAS_CHANGED, refresh_template)


class EntitiesTemplate:
    """Class to expose all enhanced entities."""

    def __getattr__(
        self,
        entity_id: Optional[str] = None,
        include_hidden: bool = False,
        include_disabled: bool = False,
    ):
        """Return all the areas."""

        return get_entities(entity_id, include_hidden, include_disabled)

    __getitem__ = __getattr__

    def __iter__(self):
        self._create_template_listener()
        return iter(get_entities())

    def __len__(self):
        self._create_template_listener()
        return len(get_entities())

    def __call__(
        self,
        entity_id: Optional[str] = None,
        include_hidden: bool = False,
        include_disabled: bool = False,
    ):
        self._create_template_listener()
        return self.__getattr__(entity_id, include_hidden, include_disabled)

    def __repr__(self) -> str:
        """Representation of all areas."""

        return "<template AllEntities>"

    def _create_template_listener(self):
        pass

        # TODO: Figure out how to listen for changes and update entities that
        #   use this template.
