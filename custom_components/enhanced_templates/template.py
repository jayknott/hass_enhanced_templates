"""Extend the template options for HA."""
import jinja2
from typing import Any, Optional

from homeassistant.helpers.template import (
    # RenderInfo,
    _ENVIRONMENT,
    # _RENDER_INFO,
    regex_match,
    regex_search,
    TemplateEnvironment,
)

from .registry import get_areas, get_entities, get_persons
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

    # Add custom tests and filters
    if jinja.tests.get("service_exists") is None:
        jinja.tests["service_exists"] = service_exists
    if jinja.tests.get("truthy") is None:
        jinja.tests["truthy"] = truthy
    if jinja.filters.get("truthy") is None:
        jinja.filters["truthy"] = truthy
    if jinja.tests.get("falsy") is None:
        jinja.tests["falsy"] = falsy
    if jinja.filters.get("truthy") is None:
        jinja.filters["truthy"] = falsy

    # Add custom globals
    jinja.globals["areas"] = AreasTemplate()
    jinja.globals["entities"] = EntitiesTemplate()
    jinja.globals["persons"] = PersonsTemplate()
    jinja.globals["service_exists"] = service_exists


def service_exists(service: str = None) -> bool:
    """Tests if a service exists."""

    if service in [None, ""] or "." not in service:
        return False

    try:
        return get_hass().services.has_service(*service.split("."))
    except:
        return False


def truthy(obj: Any = None):
    """Check if an object or string represents true."""

    if obj is None or obj is False or obj == 0:
        return False

    if obj is True:
        return True

    if isinstance(obj, str):
        return obj.lower() in ["true", "yes", "t", "y", "1"]

    if isinstance(obj, (int, float)):
        return obj != 0

    return False


def falsy(obj: Any = None):
    """Check if an object or string represents false."""

    if obj is None or obj is False or obj == 0:
        return True

    if obj is True:
        return False

    if isinstance(obj, str):
        return obj.lower() in ["false", "no", "f", "n", "0"]

    return False


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
        """Return all the entities."""

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
        """Representation of all entities."""

        return "<template AllEntities>"

    def _create_template_listener(self):
        pass

        # TODO: Figure out how to listen for changes and update entities that
        #   use this template.


class PersonsTemplate:
    """Class to expose all enhanced persons."""

    def __getattr__(
        self,
        person_id: Optional[str] = None,
        include_hidden: bool = False,
    ):
        """Return all persons."""

        return get_persons(person_id, include_hidden)

    __getitem__ = __getattr__

    def __iter__(self):
        self._create_template_listener()
        return iter(get_persons())

    def __len__(self):
        self._create_template_listener()
        return len(get_persons())

    def __call__(
        self,
        person_id: Optional[str] = None,
        include_hidden: bool = False,
    ):
        self._create_template_listener()
        return self.__getattr__(person_id, include_hidden)

    def __repr__(self) -> str:
        """Representation of all areas."""

        return "<template AllPersons>"

    def _create_template_listener(self):
        pass

        # TODO: Figure out how to listen for changes and update entities that
        #   use this template.
