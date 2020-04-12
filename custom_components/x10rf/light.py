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
import math

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

    def __init__(self, light, is_cm11a):
        """Initialize an X10rf Light."""
        X10Light.__init__(self, light, is_cm11a)
        self._brightness_step = 0


    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        if self._is_cm11a:
            x10_command(f"on {self._id}")
        else:
            x10_command(f"fon {self._id}")
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None and brightness > 0:
            cur_step = math.ceil(self._brightness / 4.0)
            new_step = math.ceil(brightness / 4.0)
            delta = new_step - cur_step
            if delta != 0:
                command = "bright" if delta > 0 else "dim"
                rf = "" if self._is_cm11a else "f"
                step = abs(delta)
                x10_command(f"{rf}{command} {self._id} {step}")
                self._brightness = (math.ceil(brightness /4.0) * 4) - 1
        self._state = True
