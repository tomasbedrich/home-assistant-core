"""The SystemAir IAM integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import systemair
from .const import DOMAIN, NAME

PLATFORMS: list[Platform] = [Platform.CLIMATE]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SystemAir IAM from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    unit = systemair.AiohttpSystemAirIAM()
    if not await unit.ping():
        await unit.close()
        raise ConfigEntryNotReady("Cannot ping the unit")

    coordinator = SystemAirUpdateCoordinator(hass, unit)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = (unit, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


class SystemAirUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, unit):
        super().__init__(
            hass,
            _LOGGER,
            name=NAME,
            update_interval=timedelta(seconds=30),
        )
        self.unit = unit

    async def _async_update_data(self):
        return await self.unit.sync()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        unit, _ = hass.data[DOMAIN].pop(entry.entry_id)
        await unit.close()

    return unload_ok
