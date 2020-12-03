"""Extend the functionality of the HA YAML parser."""
from collections import OrderedDict
from custom_components.enhanced_templates.const import YAML_TAG
import io
import os
import time
from typing import (
    Any,
    Dict,
    List,
    Optional,
    OrderedDict as OrderedDictType,
    Union,
)

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.template import TemplateEnvironment, _ENVIRONMENT
from homeassistant.util.yaml import loader as hass_loader
from homeassistant.components.lovelace import dashboard

# from .const import (
#     TRANSLATIONS_PATH,
#     # JINJA_VARIABLE_TRANSLATE,
#     # JINJA_VARIABLE_USER_ID,
# )
from .share import get_hass, get_log

# TranslationDict = Dict[str, Union[str, Dict[str, str]]]

LoadedYAML = Optional[Union[Any, OrderedDictType, List[Union[Any, List, Dict]], Dict]]


async def setup_yaml_parser() -> None:
    """Setup the YAML parser."""

    hass_loader.load_yaml = load_yaml
    dashboard.load_yaml = load_yaml
    hass_loader.SafeLineLoader.add_constructor("!include", _include_yaml)
    hass_loader.SafeLineLoader.add_constructor(
        "!include_dir_list", _include_dir_list_yaml
    )
    hass_loader.SafeLineLoader.add_constructor(
        "!include_dir_merge_list", _include_dir_merge_list_yaml
    )
    hass_loader.SafeLineLoader.add_constructor(
        "!include_dir_named", _include_dir_named_yaml
    )
    hass_loader.SafeLineLoader.add_constructor("!file", _uncache_file)


def load_yaml(fname: str, args: Dict[str, Any] = {}) -> LoadedYAML:
    """Load a YAML file."""

    return parse_yaml(fname, args)


def parse_yaml(fname: str, args: Dict[str, Any] = {}) -> LoadedYAML:
    """Parse a YAML file."""

    template: str = ""

    try:
        parse = False
        with open(fname, encoding="utf-8") as f:
            if f.readline().lower().startswith(YAML_TAG):
                parse = True

        if parse:
            jinja: TemplateEnvironment = get_hass().data.get(_ENVIRONMENT)
            template = jinja.get_template(fname).render({**args, **TEMPLATE_GLOBALS})
            stream = io.StringIO(template)
            stream.name = fname

            return hass_loader.yaml.load(stream) or OrderedDict()
        else:
            return hass_loader.yaml.load(open(fname, encoding="utf-8")) or OrderedDict()

    except hass_loader.yaml.YAMLError as exc:
        get_log().error(f"{str(exc)}: {template}")
        raise HomeAssistantError(exc) from exc


def process_node(
    loader: hass_loader.SafeLineLoader, node: hass_loader.yaml.Node
) -> List[Union[str, Dict[str, Any]]]:
    """Process include nodes to see if there are arguments."""

    args: Dict[str, Any] = {}

    if isinstance(node.value, str):
        value = node.value
    else:
        value, args, *_ = loader.construct_sequence(node)

    fname = os.path.abspath(os.path.join(os.path.dirname(loader.name), value))
    return [fname, args]


def _include_yaml(
    loader: hass_loader.SafeLineLoader, node: hass_loader.yaml.Node
) -> LoadedYAML:
    """Handle !include tag"""

    node_values = process_node(loader, node)

    try:
        return hass_loader._add_reference(
            load_yaml(*node_values, loader._user_id, None, loader._translations),
            loader,
            node,
        )
    except FileNotFoundError as exc:
        get_log().error("Unable to include file %s: %s", node_values[0], exc)
        raise HomeAssistantError(exc)


def _include_dir_list_yaml(
    loader: hass_loader.SafeLineLoader, node: hass_loader.yaml.Node
) -> LoadedYAML:
    """Handle !include_dir_list tag"""
    node_values = process_node(loader, node)
    loc: str = os.path.join(os.path.dirname(loader.name), node_values[0])
    return [
        load_yaml(f, node_values[1], loader._user_id, None, loader._translations)
        for f in hass_loader._find_files(loc, "*.yaml")
        if os.path.basename(f) != hass_loader.SECRET_YAML
    ]


def _include_dir_merge_list_yaml(
    loader: hass_loader.SafeLineLoader, node: hass_loader.yaml.Node
) -> LoadedYAML:
    """Handle !include_dir_merge_list tag"""

    node_values = process_node(loader, node)
    loc: str = os.path.join(os.path.dirname(loader.name), node_values[0])
    merged_list: List[hass_loader.JSON_TYPE] = []
    for fname in hass_loader._find_files(loc, "*.yaml"):
        if os.path.basename(fname) == hass_loader.SECRET_YAML:
            continue
        loaded_yaml = load_yaml(
            fname, node_values[1], loader._user_id, None, loader._translations
        )
        if isinstance(loaded_yaml, list):
            merged_list.extend(loaded_yaml)
    return hass_loader._add_reference(merged_list, loader, node)


def _include_dir_named_yaml(
    loader: hass_loader.SafeLineLoader, node: hass_loader.yaml.Node
) -> LoadedYAML:
    """Handle !include_dir_named tag"""

    node_values = process_node(loader, node)
    mapping: OrderedDictType = OrderedDict()
    loc: str = os.path.join(os.path.dirname(loader.name), node_values[0])
    for fname in hass_loader._find_files(loc, "*.yaml"):
        filename = os.path.splitext(os.path.basename(fname))[0]
        if os.path.basename(fname) == hass_loader.SECRET_YAML:
            continue
        mapping[filename] = load_yaml(
            fname, node_values[1], loader._user_id, None, loader._translations
        )
    return hass_loader._add_reference(mapping, loader, node)


def _uncache_file(
    _loader: hass_loader.SafeLineLoader, node: hass_loader.yaml.Node
) -> str:
    """Handle !file tag"""

    path = node.value
    timestamp = str(time.time())
    if "?" in path:
        return f"{path}&{timestamp}"
    return f"{path}?{timestamp}"
