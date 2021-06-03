"""
Support for WeightGurus wifi scales

example configuration:

```
sensor:
  - platform: weightgurus
    username: !secret weightgurus_username
    password: !secret weightgurus_username
```

"""

import logging
import threading
import time

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['requests']

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from datetime import timedelta, datetime
from homeassistant.const import CONF_NAME, CONF_USERNAME, CONF_PASSWORD
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity
    
DEFAULT_NAME = 'WeightGurus Scale'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the WeightGurus sensor."""

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    name = config.get(CONF_NAME)
    
    weightgurus_connector = WeightGurusConnector(hass, username, password)
    try:
        await weightgurus_connector._connect()
        await weightgurus_connector._update()
    except:
        _LOGGER.exception("Could not create WeightGurus sensor for '{}'!".format(username))
        return
        
    dev = []
    dev.append(WeightGurusSensor(name, weightgurus_connector))
    async_add_entities(dev, True)
    
class WeightGurusConnector:
    def __init__(self, hass, username, password, update_interval = timedelta(seconds=10)):
        self.username = username
        self.password = password
        self.hass = hass
        self.update_interval = update_interval
        self.update = self._update
        self.default_unit = 'lb'
        self.last_update = datetime.utcnow() - timedelta(days=7)
        
        self._token = None
        self._account = None
        self._most_recent_operation = {}
        
    @property
    def weight_unit(self):
        if self._account:
            return self._account.get('weightUnit') or self.default_unit
        return self.default_unit
        
    @property
    def most_recent_operation(self):
        return self._most_recent_operation
        
    @property
    def weight(self):
        return self.most_recent_operation.get('weight',0) / 10.0

    def login(self):
        import requests
        data = {"email": self.username, "password": self.password}
        login_response = requests.post("https://api.weightgurus.com/v3/account/login", data=data)
        return login_response
        
    async def _connect(self):
        login_response = await self.hass.async_add_executor_job(self.login)
        login_json = login_response.json()
        _LOGGER.debug('weightgurus login response: {}'.format(login_json))
        self._account = login_json['account']
        self._token = login_json["accessToken"]
        return self._token

    def get_data(self):
        import requests
        op_url = "https://api.weightgurus.com/v3/operation/?start={}Z".format(self.last_update.isoformat())
        data_response = requests.get(
            op_url,
            headers={
                "Authorization": 'Bearer {}'.format(self._token),
                "Accept": "application/json, text/plain, */*",
            },
        )
        response_json = data_response.json()
        return response_json
        
    async def _update(self):
        try:
            self._token = await self._connect()
            response_json = await self.hass.async_add_executor_job(self.get_data)
            _LOGGER.debug('weightgurus update response: {}'.format(response_json))
            operations = response_json.get('operations',[])
            if len(operations) > 0:
                self._most_recent_operation = next(iter(operations[-1:]),{})
            self.last_update = datetime.utcnow()
        except:
            self._token = None
            _LOGGER.exception('WeightGurus sensor failed update for user {}'.format(self.username))
        
class WeightGurusSensor(Entity):
    def __init__(self, name, weightgurus_connector):
        """Initialize the sensor."""
        self._base_name = name
        self._connector = weightgurus_connector
        self._state = None
        self._attrs = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._base_name

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._connector.weight_unit
        
    @property
    def icon(self):
        return 'mdi:relative-scale'

    async def async_update(self):
        """Get the latest data from the sensor."""
        await self._connector._update()
        self._state = self._connector.weight
        self._attrs = self._connector.most_recent_operation