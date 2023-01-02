import unittest
from bobcatpy import Bobcat

class TestParseTemperature(unittest.IsolatedAsyncioTestCase):
    async def test_parse_valid_temperature(self):
        b = Bobcat("10.10.21.70")
        temp_string = "12 °C"
        self.assertEqual(b._parse_temperature(temp_string), "12")
        await b.close_session()
