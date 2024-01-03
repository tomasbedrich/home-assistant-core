"""Config flow for SystemAir IAM."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_flow

from . import systemair
from .const import DOMAIN, NAME


async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if there are devices that can be discovered."""
    unit = systemair.AiohttpSystemAirIAM()
    res = await unit.ping()
    await unit.close()
    return res


config_entry_flow.register_discovery_flow(DOMAIN, NAME, _async_has_devices)
