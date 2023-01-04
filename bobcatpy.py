""" Simple Python class to interact with the Bobcat diagnoser
https://github.com/ardevd/bobcatpy
"""

import re
import logging

import aiohttp

import const

logger = logging.getLogger('bobcatpy')

class Bobcat:
    """Bobcat connection class"""

    base_url = ""

    def __init__(self,
                 miner_ip='',
                 ):
        """Init the Bobcat object

        The miner IP should be the local IP assigned to the bobcat hotspot
        """
        self.miner_ip = miner_ip
        self.session = aiohttp.ClientSession()
        self.base_url = f"http://{miner_ip}/"

    async def miner_status(self):
        """Get miner status"""
        return await self._get("miner.json")

    async def temps(self):
        """Get miner temperatures"""
        return await self._get("temp.json")

    async def dig(self):
        """Dig helium seed nodes"""
        return await self._get("dig.json")

    async def reboot(self):
        """Reboot the miner"""
        return await self._post("admin/reboot", const.ADMIN_AUTH_HEADER)

    async def reset(self):
        """Reset the miner"""
        return await self._post("admin/reset", const.ADMIN_AUTH_HEADER)
    
    async def _get(self, uri):
        """Generic GET request helper function"""
        url = f'{self.base_url}{uri}'
        async with self.session.get(url) as resp:
            return await resp.json()

    async def _post(self, uri, headers=None):
        """Generic POST request helper function"""
        url = f'{self.base_url}{uri}'
        async with self.session.post(url, headers = headers) as resp:
            return await resp.text()

    async def close_session(self):
        """Close the connection session"""
        await self.session.close()
    
    def _parse_temperature(self, temperature_string):
        """Parse the temperature value from temperature value string"""
        return re.findall(r"\d+", temperature_string)[0]

    async def blockchain_height(self):
        """Return the current Helium blockchain height"""
        url = "https://api.helium.io/v1/blocks/height"
        async with self.session.get(url) as resp:
            response_json = await resp.json()
            return response_json['data']['height']

    async def status_summary(self):
        """Get a condensed summary of the miner status"""
        summary = {}

        summary['state'] = "unavailable"

        try:
            miner_status = await self.miner_status()
            
            if miner_status:
                summary['ota_version'] = miner_status['ota_version']
                summary['image'] = miner_status['miner']['Image']
                summary['image_version'] = summary['image'].split(':', 1)[1] if ':' in summary['image'] else None
                summary['animal'] = miner_status['animal']
                summary['state'] = miner_status['miner']['State']
                summary['created'] = miner_status['miner']['Created']
                summary['public_ip'] = miner_status['public_ip']
                summary['private_ip'] = miner_status['private_ip']
                summary['temp'] = self._parse_temperature(miner_status['temp0'])
                summary['error'] = miner_status['errors'] != ''

        except Exception as ex:
            logger.error('Exception during status update: %s', ex)

        try:
            summary['blockchain_height'] = await self.blockchain_height()
        except Exception as ex:
            logger.error('Exception during blockchain height check: %s', ex)

        return summary
