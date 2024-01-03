"""In ideal world, this should be a separate Python library instead."""

from collections.abc import Iterable
import json
import logging

import aiohttp
import aiohttp.client_exceptions

_LOGGER = logging.getLogger(__name__)

DEFAULT_HOSTNAME = "saveconnect.local"

ModbusKeys = str
ModbusValues = int
ModbusData = dict[ModbusKeys, ModbusValues]


class ModbusSystemAirIAM:
    _setpoint: int
    _known_registers = {
        "2000": "setpoint",
    }

    def __init__(self) -> None:
        self.dirty = False

    def feed(self, data: ModbusData) -> None:
        """Update unit state based on passed modbus data."""
        if setpoint := data.get("2000"):
            self._setpoint = setpoint

    @property
    def setpoint(self) -> int:
        """Temperature setpoint for the supply air."""
        return self._setpoint // 10

    @setpoint.setter
    def setpoint(self, value: int):
        self._setpoint = value * 10
        self.dirty = True


class AiohttpSystemAirIAM(ModbusSystemAirIAM):
    def __init__(self, host=DEFAULT_HOSTNAME) -> None:
        self.host = host
        self.session = aiohttp.ClientSession(
            read_timeout=5, conn_timeout=5, raise_for_status=True
        )
        super().__init__()

    async def ping(self) -> bool:
        """Return if unit is reachable over HTTP."""
        try:
            async with self.session.get(f"http://{self.host}") as res:
                return res.status == 200
        except aiohttp.client_exceptions.ClientError:
            return False

    async def _read(self, keys: Iterable[ModbusKeys]) -> ModbusData:
        payload = {key: 1 for key in keys}
        url = f"http://{self.host}/mread?{json.dumps(payload)}"
        _LOGGER.debug(f"Reading from {url}")
        async with self.session.get(url) as res:
            return await res.json()

    async def _write(self, payload: ModbusData) -> bool:
        url = f"http://{self.host}/mwrite?{json.dumps(payload)}"
        _LOGGER.debug(f"Writing to {url}")
        async with self.session.get(url) as res:
            return (await res.text()).strip() == "OK"

    async def sync(self) -> None:
        """Write dirty registers, read all and update unit state."""
        # write
        if self.dirty:
            to_write = {
                register: getattr(self, f"_{property_name}")
                for register, property_name in self._known_registers.items()
            }
            write_success = await self._write(to_write)
            if write_success:
                self.dirty = False
        # read
        to_read = self._known_registers.keys()
        modbus_data = await self._read(to_read)
        self.feed(modbus_data)

    async def close(self):
        """Close HTTP session."""
        return await self.session.close()
