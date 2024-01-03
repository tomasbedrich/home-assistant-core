from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SystemAirUpdateCoordinator, systemair
from .const import DOMAIN, NAME


async def async_setup_entry(hass, entry, async_add_entities):
    # assuming (unit, coordinator) stored here by __init__.py
    unit, coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SystemAirClimateEntity(unit, coordinator)])


class SystemAirClimateEntity(CoordinatorEntity, ClimateEntity):
    # The CoordinatorEntity class provides:
    #   should_poll
    #   async_update
    #   async_added_to_hass
    #   available

    _attr_has_entity_name = True
    _attr_name = NAME
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_mode = HVACMode.AUTO
    _attr_hvac_modes = [HVACMode.AUTO]
    _attr_target_temperature_step = 1.0
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, unit, coordinator: SystemAirUpdateCoordinator) -> None:
        super().__init__(coordinator)
        self.unit: systemair.ModbusSystemAirIAM = unit
        self._attr_unique_id = "test_dev0"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self.unique_id)}, name=self.name)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_target_temperature = float(self.unit.setpoint)
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            self.unit.setpoint = int(kwargs[ATTR_TEMPERATURE])
        await self.coordinator.async_request_refresh()
