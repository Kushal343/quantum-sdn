"""Standard-library local client, usable from both Windows and Linux."""
import json
import os
import time
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from urllib.error import URLError


class RyuClient:
    def __init__(self, url='http://127.0.0.1:8080', token=None):
        parsed = urlparse(url)
        if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost'):
            raise ValueError('This lab client requires a loopback HTTP controller')
        self.url = url.rstrip('/')
        self.token = token or os.environ.get('QKD_SDN_TOKEN', '')
        if len(self.token) < 24:
            raise ValueError('Set QKD_SDN_TOKEN to at least 24 characters')
        self.states = {i:'active' for i in range(1,5)}

    def request(self, path, data=None):
        body = None if data is None else json.dumps(data).encode()
        req = Request(self.url+path, data=body, headers={
            'Authorization':'Bearer '+self.token, 'Content-Type':'application/json'})
        with urlopen(req, timeout=12) as response:
            result = json.load(response)
        self.states = {int(i):s for i,s in result['states'].items()}
        return result

    def initialize(self):
        deadline = time.monotonic()+20
        while True:
            try:
                status = self.request('/qkd/status')
                if status['switches'] == [1,2]:
                    result = self.request('/qkd/initialize', {})
                    if result['ready']:
                        return result
            except URLError:
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError('Ryu or both Mininet switches unavailable')
            time.sleep(.25)

    def apply(self, channel, action):
        result = self.request('/qkd/decision', dict(channel=channel, action=action))
        if not result['ready']:
            raise RuntimeError('Controller did not acknowledge ready switch state')
        return self.states[channel]

    def snapshot(self):
        return self.request('/qkd/status')
