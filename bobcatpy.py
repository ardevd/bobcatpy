""" Simple Python class to interact with the Bobcat diagnoser
https://github.com/ardevd/bobcatpy
"""

import re
import logging
import asyncio
import json

import aiohttp

ADMIN_AUTH_HEADER = {"Authorization": "Basic Ym9iY2F0Om1pbmVy"}

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

    async def led(self):
        """Get miner led color"""
        return await self._get("led.json")

    async def dig(self):
        """Dig helium seed nodes"""
        return await self._get("dig.json")

    async def reboot(self):
        """Reboot the miner"""
        return await self._post("admin/reboot", ADMIN_AUTH_HEADER)

    async def reset(self):
        """Reset the miner"""
        return await self._post("admin/reset", ADMIN_AUTH_HEADER)

    async def _get(self, uri: str):
        """Generic GET request helper function"""
        url = f'{self.base_url}{uri}'
        async with self.session.get(url) as resp:
            status = resp.status

            # Check for Bobcat rate limiting
            if status == 429:
                raise BobcatRateLimitException(
                    "Rate limit exceeded, try again later")

            if status == 200:
                # The Bobcat diagnoser API doesnt always properly declare json responses with correct content type
                try:
                    return await resp.json()
                except aiohttp.ContentTypeError:
                    try:
                        # try to cast txt as json
                        return json.loads(await resp.text())
                    except aiohttp.ContentTypeError:
                        # Give up
                        pass

                return None

            return None

    async def _post(self, uri: str, headers=None):
        """Generic POST request helper function"""
        url = f'{self.base_url}{uri}'
        async with self.session.post(url, headers=headers) as resp:
            return await resp.text()

    async def close_session(self):
        """Close the connection session"""
        await self.session.close()

    def _parse_temperature(self, temperature_string: str):
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
            # Schedule tasks (results will correlate with scheduling order)
            tasks = []
            tasks.append(asyncio.ensure_future(self.miner_status()))
            tasks.append(asyncio.ensure_future(self.blockchain_height()))

            # Gather task results
            response_data = await asyncio.gather(*tasks)
            miner_status = response_data[0]
            blockchain_height = response_data[1]

            # To avoid rate limiting, we must retrieve led status sequentially
            miner_led = await self.led()

            if miner_led:
                summary['led'] = miner_led["led"]

            summary['blockchain_height'] = blockchain_height

            summary['ota_version'] = miner_status['ota_version']
            summary['image'] = miner_status['miner']['Image']
            summary['image_version'] = summary['image'].split(
                ':', 1)[1] if ':' in summary['image'] else None
            summary['animal'] = miner_status['animal']
            summary['state'] = miner_status['miner']['State']
            summary['created'] = miner_status['miner']['Created']
            summary['public_ip'] = miner_status['public_ip']
            summary['private_ip'] = miner_status['private_ip']
            summary['temp'] = self._parse_temperature(
                miner_status['temp0'])
            summary['error'] = miner_status['errors'] != ''

        except aiohttp.ClientError as ex:
            logger.error("Failed to connect to host %s", self.miner_ip)
            raise ex

        return summary


class BobcatRateLimitException(Exception):
    """Bobcat Miner rate limit exceeded"""
