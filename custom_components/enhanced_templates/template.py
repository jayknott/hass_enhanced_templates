"""Extend the template options for HA."""
import jinja2
from typing import Optional

from homeassistant.helpers.template import (
    _ENVIRONMENT,
    regex_match,
    regex_search,
    TemplateEnvironment,
)

from .registry import get_areas, get_entities
from .share import get_hass


async def setup_template() -> None:
    """Setup the template options."""

    hass = get_hass()

    jinja: Optional[TemplateEnvironment] = hass.data.get(_ENVIRONMENT)
    if jinja is None:
        jinja = hass.data[_ENVIRONMENT] = TemplateEnvironment(hass)

    # Add a loader so Jinja can use files.
    jinja.loader = jinja2.FileSystemLoader("/")

    # Add the built-in HA regex filters as tests if they do not already exist
    if jinja.tests.get("regex_match") is None:
        jinja.tests["regex_match"] = regex_match
    if jinja.tests.get("regex_search") is None:
        jinja.tests["regex_search"] = regex_search

    # await update_template_areas_global()
    # await update_template_entities_global()

    # Add custom globals
    jinja.globals["areas"] = get_areas
    jinja.globals["entities"] = get_entities
