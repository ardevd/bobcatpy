""" Simple Python class to interact with the Bobcat diagnoser
https://github.com/ardevd/bobcatpy
"""

from urllib.request import Request, build_opener

import json
import logging
import os
import socket

logger = logging.getLogger('bobcatpy')

class Bobcat:
    """Bobcat connection class"""

    admin_auth_header = {"Authorization": "Basic Ym9iY2F0Om1pbmVy"}

    def __init__(self,
                 miner_ip=''):
        """Init the Bobcat object

        The miner IP should be the local IP assigned to the bobcat hotspot
        """
        self.miner_ip = miner_ip

        # Verify connectivity
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((miner_ip, 80))
        if result != 0:
            print("[-] Miner not responding or not connected to the network")

    def temps(self):
        return self._get("temp.json")

    def sync_status(self):
        return self._get("status.json")
        
    def miner_status(self):
        return self._get("miner.json")
    
    def reboot(self):
        return self._post("admin/reboot", self.admin_auth_header)

    def fast_sync(self):
        return self._post("admin/fastsync", self.admin_auth_header)

    def reset(self):
        return self._post("admin/reset", self.admin_auth_header)

    def _post(self, url, headers=None):
        req = Request("http://%s/%s" %(self.miner_ip, url), headers=headers, method="POST")
        return self.__open(req)

    def _get(self, url):
        req = Request("http://%s/%s" %(self.miner_ip, url))
        return self.__open(req)

    def __open(self, req):
        opener = build_opener()
        resp = opener.open(req)
        charset = resp.info().get('charset', 'utf-8')
        resp_data = resp.read().decode(charset)
        
        if resp_data:
            try:
                return json.loads(resp_data)
            except json.JSONDecodeError:
                return resp_data
        else:
            return None