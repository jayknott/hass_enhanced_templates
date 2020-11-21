"""Shared Integration elements."""
from logging import Logger

from homeassistant.core import HomeAssistant

from .model import Configuration, IntegrationBase

SHARE = {"base": None}


def get_base() -> IntegrationBase:
    if SHARE["base"] is None:
        SHARE["base"] = IntegrationBase()

    return SHARE["base"]


def get_configuration() -> Configuration:
    base = get_base()

    if base.configuration is None:
        base.configuration = Configuration()

    return base.configuration


def get_hass() -> HomeAssistant:
    return get_base().hass


def get_log() -> Logger:
    return get_base().log
