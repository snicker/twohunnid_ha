"""
Support for X10 lights using RF comms. 

I did this because for some reason one of my devices won't work with the CM11a,
only the CM17 "firecracker". Heyu already supports this; just needs to be
called with `fon/off` rather  than `on/off`
"""
import logging
from subprocess import CalledProcessError

import voluptuous as vol

from homeassistant.const import (CONF_NAME, CONF_ID, CONF_DEVICES)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, PLATFORM_SCHEMA)
from homeassistant.components.x10.light import X10Light, x10_command
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [
        {
            vol.Required(CONF_ID): cv.string,
            vol.Required(CONF_NAME): cv.string,
        }
    ]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the x10 RF Light platform."""
    try:
        x10_command('info')
    except CalledProcessError as err:
        _LOGGER.error(err.output)
        return False

    add_entities(X10RFLight(light, False) for light in config[CONF_DEVICES])


class X10RFLight(X10Light):
    """Representation of an X10 RF Light."""
