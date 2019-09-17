import aiohttp
from datetime import datetime, timedelta

DEFAULT_BASE_URL = "https://api.skydrop.com/"

class SkydropController(object):
    def __init__(self, client, id, name):
        self._client = client
        self.id = id
        self.name = name
        self._controller_data = {}
        self._zones_data = {}
        self._zone_states = {}
        
    async def update(self):
        await self.update_data()
        await self.update_state()
        
    async def update_data(self):
        path = "{}/controllers/{}/all.config".format(
            self._client._base_url, self.id)
        res = await self._client._get(path)
        if 'controller_data' in res:
            self._controller_data = res['controller_data']
        if 'zones_data' in res:
            self._zones_data = res['zones_data']
            
    async def update_state(self):
        path = "{}/controllers/{}/water_state".format(
            self._client._base_url, self.id)
        res = await self._client._get(path)
        if res.get('success') and 'zone_states' in res:
            self._zone_states = res['zone_states']
        
class SkydropClient(object):
    """
    SkydropClient API client
    :param client_id: Client ID for your Skydrop App
    :type token: str
    :param client_secret: Client secret for your Skydrop App
    :type token: str
    :param session: aiohttp session to use or None
    :type session: object or None
    :param timeout: seconds to wait for before triggering a timeout
    :type timeout: integer
    """
    def __init__(self, client_id, client_secret, session=None,
                 timeout=aiohttp.client.DEFAULT_TIMEOUT):
        """
        Creates a new :class:`SkydropClient` instance.
        """
        self._headers = {'Content-Type': 'application/json'}
        if session is not None:
            self._session = session
        else:
            self._session = aiohttp.ClientSession(timeout=timeout)
        
        self._base_url = DEFAULT_BASE_URL
        self._client_id = client_id
        self._client_secret = client_secret
        
        self._access_token = None
        self._access_token_expiry = datetime.now()
        self._refresh_token = None
        
        self._controllers = []
        
        
    def set_access_token(self, access_token, expires = 86400):
        self._access_token = access_token
        self._access_token_expiry = datetime.now() + timedelta(seconds=expires)
        self._headers['Authorization'] = "Bearer {}".format(self._access_token)
        
    def set_refresh_token(self, refresh_token):
        self._refresh_token = refresh_token
        
    def get_controller(self, id):
        for c in self._controllers:
            if c.id == id:
                return c
        
    async def update_controllers(self):
        path = "{}users/get.controller.ids"
        res = await self.get(path)
        if 'controller_ids' in res:
            self._controllers = []
            for cdata in res['controller_ids']:
                id = cdata.get('public_controller_id')
                if not self.get_controller(id):
                    name = cdata.get('name')
                    cont = SkydropController(id=id, name=name)
                    self._controllers.append(controller)
        for cont in self._controllers:
            await cont.update()
        return self._controllers
        
    async def get_access_token(self, access_code):
        path = "{}oauth/token".format(self._base_url)
        data = {
            'grant_type': "authorization_code", 
            'code': access_code, 
            'client_id': self._client_id, 
            'client_secret': self._client_secret
        }
        res = await self._post(path, data = data)
        if 'access_token' in res:
            self.set_access_token(res['access_token'], 
                expires = res.get('expires_in',86400))
        if 'refresh_token' in res:
            self.set_refresh_token(res['refresh_token'])
        return res
        
    async def refresh_access_token(self, refresh_token = None):
        refresh_token = refresh_token or self._refresh_token
        if refresh_token is None:
            raise SkydropClient.ClientError("No refresh token provided")
        path = "{}oauth/token".format(self._base_url)
        data = {
            'grant_type': "refresh_token", 
            'refresh_token': refresh_token, 
            'client_id': self._client_id, 
            'client_secret': self._client_secret
        }
        res = await self._post(path, data = data)
        if 'access_token' in res:
            self.set_access_token(res['access_token'], 
                expires = res.get('expires_in',86400))
        if 'refresh_token' in res:
            self.set_refresh_token(res['refresh_token'])
        return res
        
    @staticmethod
    def handle_error(status, error):
        if status == 400:
            raise SkydropClient.BadRequest(error)
        elif status == 401:
            raise SkydropClient.Unauthorized(error)
        elif status == 403:
            raise SkydropClient.Forbidden(error)
        elif status == 429:
            raise SkydropClient.TooManyRequests(error)
        elif status == 500:
            raise SkydropClient.InternalServerError(error)
        else:
            raise SkydropClient.ClientError(error)

    async def _get(self, path, **kwargs):
        async with self._session.get(
                path, headers=self._headers, **kwargs) as resp:
            if 200 <= resp.status < 300:
                return await resp.json()
            else:
                self.handle_error(resp.status, await resp.json())

    async def _post(self, path, **kwargs):
        async with self._session.post(
                path, headers=self._headers, **kwargs) as resp:
            if 200 <= resp.status < 300:
                return await resp.json()
            else:
                self.handle_error(resp.status, await resp.json())

    async def _put(self, path, **kwargs):
        async with self._session.put(
                path, headers=self._headers, **kwargs) as resp:
            if 200 <= resp.status < 300:
                return await resp.json()
            else:
                self.handle_error(resp.status, await resp.json())

    class ClientError(Exception):
        """Generic Error."""
        pass

    class Unauthorized(ClientError):
        """Failed Authentication."""
        pass

    class BadRequest(ClientError):
        """Request is malformed."""
        pass

    class Forbidden(ClientError):
        """Access is prohibited."""
        pass

    class TooManyRequests(ClientError):
        """Too many requests for this time period."""
        pass

    class InternalServerError(ClientError):
        """Server Internal Error."""
        pass

    class InvalidData(ClientError):
        """Can't parse response data."""
        pass