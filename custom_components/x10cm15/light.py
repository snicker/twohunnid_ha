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
from homeassistant.components.light.x10 import X10Light, x10_command
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


CM15_SINGLETON = None

def CM15_Factory():
    if CM15_SINGLETON is None:
        CM15_SINGLETON = CM15()
    return CM15_SINGLETON
    
def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the x10 CM15 Light platform."""

    add_entities(X10CM15Light(light, CM15_Factory()) for light in config[CONF_DEVICES])


class X10CM15Light(X10Light):
    """Representation of an X10 RF Light."""

    def __init__(self, light, CM15):
        """Initialize an X10 Light."""
        X10Light.__init__(self, light, False)
        self._cm15 = CM15

    def turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        self.send_command(self._id,"ON")
        self._brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        self._state = True

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self.send_command(self._id,"OFF")
        self._state = False
        
    def send_command(self, code, command):
        self._cm15.open()
        self._cm15.sendCommand(code.upper(),command.upper())
        self._cm15.close()

    def update(self):
        """Fetch update state."""
        pass
