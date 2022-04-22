""" Simple Python class to interact with the Bobcat diagnoser
https://github.com/ardevd/bobcatpy
"""

from urllib.request import Request, build_opener

import json
import logging
import time
import socket
import re
import warnings

from datetime import datetime, timezone

logger = logging.getLogger('bobcatpy')


class Bobcat:
    """Bobcat connection class"""

    admin_auth_header = {"Authorization": "Basic Ym9iY2F0Om1pbmVy"}

    def __init__(self,
                 miner_ip='',
                 get_timeout=20,
                 auto_connect=True
                 ):
        """Init the Bobcat object

        The miner IP should be the local IP assigned to the bobcat hotspot
        """
        self.miner_ip = miner_ip
        self.get_timeout = get_timeout

        if auto_connect and self.ping() != 0:
            logger.warning("[-] Miner not responding or not connected to the network")

    def ping(self):
        """Verify connectivity"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return sock.connect_ex((self.miner_ip, 80))

    def temps(self):
        """Retrieve temperature information from the miner"""
        return self._get("temp.json")

    def sync_status(self):
        """Get the blockchain synchronization channel"""
        return self._get("status.json")

    def miner_status(self):
        """Get the miner status"""
        return  self._get("miner.json")

    def status_summary(self):
        """Get a condensed summary of the miner status"""
        summary = {}

        summary['state'] = "unavailable"

        try:
            miner_status = self.miner_status()

            if miner_status:
                summary['ota_version'] = miner_status['ota_version']
                summary['image'] = miner_status['miner']['Image']
                summary['image_version'] = summary['image'].split(':', 1)[1] if ':' in summary['image'] else None
                summary['animal'] = miner_status['animal']
                summary['state'] = miner_status['miner']['State']
                summary['created'] = miner_status['miner']['Created']
                summary['miner_height'] = int(miner_status['miner_height'])
                summary['blockchain_height'] = self.blockchain_height()
                summary['public_ip'] = miner_status['public_ip']
                summary['private_ip'] = miner_status['private_ip']
                summary['temp'] = self._parse_temperature(miner_status['temp0'])
                summary['sync_gap'] = max(0, summary['blockchain_height'] - summary['miner_height'])
                summary['error'] = miner_status['errors'] != ''
        except Exception as ex:
            logger.error('Exception during status update: %s', ex)

        return summary

    def _parse_temperature(self, temperature_string):
        """Parse the temperature value from temperature value string"""
        return re.findall(r"\d+", temperature_string)[0]

    def blockchain_height(self):
        """Return the current Helium blockchain height"""
        req = Request("https://api.helium.io/v1/blocks/height")
        height = self.__open(req)
        return height['data']['height']

    def reboot(self):
        """Reboot the hotspot"""
        return self._post("admin/reboot", "The hotspot will reboot", self.admin_auth_header)

    def fast_sync(self):
        """Download and load the latest blockchain snapshot"""
        return self._post("admin/fastsync", "The hotspot will download and load the latest snapshot. This will take a while and cause the miner to reboot",
                          self.admin_auth_header)

    def reset(self):
        """Reset the hotspot"""
        return self._post("admin/reset", "The hotspot sync data and Helium software will be reset", self.admin_auth_header)

    def resync(self):
        """Resync the hotspot"""
        return self._post("admin/resync", "The hotspot will delete local sync data and restart sync", self.admin_auth_header)

    def diagnose(self):
        """Diagnose the hotspot by running a series of checks"""
        answer = input(
            "A series of requests will be sent to your miner. This will take some time and slow down your miner.\nContinue (y/n)? ")
        if answer.lower() in ["y", "yes"]:
            self._do_diagnose()

    def _do_diagnose(self):
        print("[*] Checking connectivity")
        if self.ping() == 0:
            print("[+] Local Network: OK")
        else:
            print("[-] Local Network: [FAIL] Hotspot does not respond to requests")
            return

        print("[*] Checking temperatures")
        self._assert_temperatures(self.temps())
        time.sleep(3)
        print("[*] Checking sync state")
        self._assert_sync_state(self.sync_status())
        time.sleep(3)
        print("[*] Checking miner state")
        time.sleep(3)
        self._assert_miner_state(self.miner_status())
        print("[+] Diagnostics complete")

    def _assert_temperatures(self, temp_data):
        temp0 = int(temp_data["temp0"])
        temp1 = int(temp_data["temp1"])

        if temp0 > 70 or temp1 > 70:
            print(
                f"[-] Temperature: [WARN] Onboard temperature is high {temp0}/{temp1}c")
        else:
            print("[+] Temperature: OK")

    def _assert_sync_state(self, sync_data):
        sync_gap = sync_data["gap"]
        sync_eval = "[+]"
        sync_eval_message = "OK"
        if sync_gap.isnumeric():
            if int(sync_gap) > 800:
                sync_eval_message = "[WARN] Large sync gap. Fast sync recommended"
                sync_eval = "[-]"
        else:
            sync_eval_message = "[FAIL] Unexpected sync state. Miner software might not be running"
            sync_eval = "[-]"

        print(f"{sync_eval} Sync State: {sync_eval_message}")

    def _assert_miner_state(self, miner_status):
        state = miner_status["miner"]["State"]
        if state == "running":
            print("[+] Miner State: Miner running")
        else:
            print("[-] Miner State: [FAIL] Miner not running")

        errors = miner_status["errors"]
        if errors:
            print(f"[-] Miner State: [WARN] Miner reports error: {errors}")
        else:
            print("[+] Miner State: No errors reported")

    def _post(self, url, message, headers=None):
        answer = input(f"{message}\nContinue (y/n)? ")
        if answer.lower() in ["y", "yes"]:
            req = Request(f"http://{self.miner_ip}/{url}",
                          headers=headers, method="POST")
            return self.__open(req)

    def _get(self, url):
        req = Request(f"http://{self.miner_ip}/{url}")
        return self.__open(req, timeout=self.get_timeout)

    def __open(self, req, timeout=None):
        opener = build_opener()
        resp_data = None
        try:
            resp = opener.open(req, timeout=timeout)
            charset = resp.info().get('charset', 'utf-8')
            resp_data = resp.read().decode(charset)
        except socket.timeout:
            warnings.warn("Caught a socket.timeout")
        if resp_data:
            try:
                return json.loads(resp_data)
            except json.JSONDecodeError:
                return resp_data
        else:
            return None
