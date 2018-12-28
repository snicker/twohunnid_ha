"""
Support for the Zwift API to create sensors.

example configuration:

```
sensor:
  - platform: zwift
    username: !secret my_zwift_username
    password: !secret my_zwift_password
    players:
      - !secret my_zwift_player_id 
      - !secret my_friends_zwift_player_id
```

"""

import logging

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['zwift-client==0.2.0']

import voluptuous as vol
from datetime import timedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.components.binary_sensor import BinarySensorDevice
from homeassistant.const import CONF_NAME, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import SERVER_SOFTWARE
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.helpers.dispatcher import dispatcher_send, \
    async_dispatcher_connect
    
CONF_UPDATE_INTERVAL = 'update_interval'
CONF_PLAYERS = 'players'

DATA_ZWIFT = 'zwift'

DEFAULT_NAME = 'Zwift'

SIGNAL_ZWIFT_UPDATE = 'zwift_update_{player_id}'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_PLAYERS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_UPDATE_INTERVAL, default=timedelta(seconds=15)): (
        vol.All(cv.time_period, cv.positive_timedelta)),
})

SENSOR_TYPES = {
    'online': {'name': 'Online', 'binary': True, 'device_class': 'connectivity'},
    'hr': {'name': 'Heart Rate', 'unit': 'bpm'},
    'speed': {'name': 'Speed', 'unit': 'mph', 'unit_metric': 'kmh'},
    'cadence': {'name': 'Cadence', 'unit': 'Hz'},
    'power': {'name': 'Power', 'unit': 'W'},
    'altitude': {'name': 'Altitude', 'unit': 'ft', 'unit_metric': 'm'}
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Zwift sensor."""

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    players = config.get(CONF_PLAYERS)
    name = config.get(CONF_NAME)
    update_interval = config.get(CONF_UPDATE_INTERVAL)
    
    
    zwift_data = ZwiftData(update_interval, username, password, players, hass)
    try:
        zwift_data._connect()
    except:
        _LOGGER.exception("Could not create Zwift sensor named '{}'!".format(name))
        return
        
    dev = []
    for player_id in zwift_data.players:
        for variable in SENSOR_TYPES:
            if SENSOR_TYPES[variable].get('binary'):
                dev.append(ZwiftBinarySensorDevice(name, zwift_data, zwift_data.players[player_id], variable))
            else:
                dev.append(ZwiftSensorDevice(name, zwift_data, zwift_data.players[player_id], variable))

    async_add_entities(dev, True)
    

class ZwiftSensorDevice(Entity):
    def __init__(self, name, zwift_data, player, sensor_type):
        """Initialize the sensor."""
        self._base_name = name
        self._zwift_data = zwift_data
        self._player = player
        self._type = sensor_type
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return "{} {} ({})".format(self._base_name,SENSOR_TYPES[self._type].get('name'),self._player.player_id)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return SENSOR_TYPES[self._type].get('unit')

    def update(self):
        """Get the latest data from the sensor."""
        self._zwift_data.update()
        self._state = getattr(self._player,self._type)
        
    async def async_added_to_hass(self):
        """Register update signal handler."""
        async def async_update_state():
            """Update sensor state."""
            await self.async_update_ha_state(True)

        async_dispatcher_connect(self.hass, SIGNAL_ZWIFT_UPDATE.format(player_id=self._player.player_id), async_update_state)
        
class ZwiftBinarySensorDevice(ZwiftSensorDevice, BinarySensorDevice):
    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state

    @property
    def device_class(self):
        """Return the device class of the binary sensor."""
        return SENSOR_TYPES[self._type].get('device_class')
  
class ZwiftPlayerData:
    def __init__(self, player_id):
        self._player_id = player_id
        self.data = {}
        self.player_profile = {}
        
    @property
    def player_id(self):
        return self._player_id
        
    @property
    def online(self):
        return self.data.get('online',False)
        
    @property
    def hr(self):
        return self.data.get('heartrate',0.0)
        
    @property
    def speed(self):
        return self.data.get('speed',0.0)
        
    @property
    def cadence(self):
        return self.data.get('cadence',0.0)
        
    @property
    def power(self):
        return self.data.get('power',0.0)
        
    @property
    def altitude(self):
        return self.data.get('altitude',0.0)
    
class ZwiftData:
    """Representation of a Zwift client data collection object."""
    def __init__(self, update_interval, username, password, players, hass):
        self._client = None
        self.username = username
        self.password = password
        self.hass = hass
        self.players = {player: ZwiftPlayerData(player) for player in players}
        self.update = Throttle(update_interval)(self._update)

    def check_zwift_auth(self, client):
        token = client.auth_token.fetch_token_data()
        if 'error' in token:
            raise Exception("Zwift authorization failed: {}".format(token))
        return True
        
    def _connect(self):
        from zwift import Client as ZwiftClient
        client = ZwiftClient(self.username,self.password)
        if self.check_zwift_auth(client):
            self._client = client
            return self._client

    def _update(self):
        if self._client is None:
            self._connect()
        if self._client:
            world = self._client.get_world(1)
            online_players = world.players['friendsInWorld']
            for player_id in self.players:
                data = {}
                online_player = next((player for player in online_players if str(player['playerId']) == str(player_id)),None)
                if online_player:
                    player_data = world.player_status(player_id)
                    data = {
                        'online': True,
                        'heartrate': float(player_data.heartrate),
                        'cadence': float(player_data.cadence),
                        'power': float(player_data.power),
                        'speed': player_data.speed / 1000000.0,
                        'altitude': float(player_data.altitude)
                    }
                    self.players[player_id].player_profile = online_player
                self.players[player_id].data = data
                _LOGGER.debug("dispatching zwift data update for player {}".format(player_id))
                dispatcher_send(self.hass, SIGNAL_ZWIFT_UPDATE.format(player_id=player_id))
            
            