from . import ZHI_REMOTE_SCHEMA, ZhiRemoteEntity
from asyncio import sleep
from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.components.climate.const import HVAC_MODE_OFF, SUPPORT_TARGET_TEMPERATURE, SUPPORT_FAN_MODE, ATTR_HVAC_MODE
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE
import logging

_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(ZHI_REMOTE_SCHEMA)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([ZhiRemoteClimate(config)])


class ZhiRemoteClimate(ZhiRemoteEntity, ClimateEntity):

    def __init__(self, conf):
        super().__init__(conf)

        self._hvac_mode = HVAC_MODE_OFF
        self._fan_mode = self.fan_modes[0]

        self._last_operation = None
        self._current_temperature = None
        self._target_temperature = self.min_temp

    @property
    def supported_features(self):
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

    @property
    def temperature_unit(self):
        return self.hass.config.units.temperature_unit

    @property
    def precision(self):
        return PRECISION_WHOLE

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def _support_modes(self):
        mode = next(k for k in self.command if k != 'off') if self._hvac_mode == 'off' else self._hvac_mode
        return self.command[mode]

    @property
    def _support_temps(self):
        return list(self._support_modes[self._fan_mode].keys())

    @property
    def min_temp(self):
        return self._support_temps[0]

    @property
    def max_temp(self):
        return self._support_temps[-1]

    @property
    def hvac_modes(self):
        return list(self.command.keys())

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def fan_modes(self):
        return list(self._support_modes.keys())

    @property
    def fan_mode(self):
        return self._fan_mode

    @property
    def current_temperature(self):
        return self._current_temperature

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None or temperature < self.min_temp or temperature > self.max_temp:
            _LOGGER.warning('The temperature value is out of min/max range')
            return
        else:
            self._target_temperature = temperature

        hvac_mode = kwargs.get(ATTR_HVAC_MODE)
        if hvac_mode:
            return await self.async_set_hvac_mode(hvac_mode)
        await self.async_control()

    async def async_set_hvac_mode(self, hvac_mode):
        self._hvac_mode = hvac_mode
        if not hvac_mode == HVAC_MODE_OFF:
            self._last_operation = hvac_mode
        await self.async_control(True)

    async def async_set_fan_mode(self, fan_mode):
        self._fan_mode = fan_mode
        await self.async_control()

    async def async_turn_off(self):
        await self.async_set_hvac_mode(HVAC_MODE_OFF)

    async def async_turn_on(self):
        await self.async_set_hvac_mode(self.hvac_modes[1] if self._last_operation is None else self._last_operation)

    async def async_control(self, can_off=False):
        if self._hvac_mode.lower() == HVAC_MODE_OFF:
            if can_off:
                await self.async_command('off')
            else:
                await self.async_update_ha_state()
            return

        if 'on' in self.command:
            await self.send_command('on')
            await sleep(1)

        await self.async_command(self._hvac_mode, self._fan_mode, self._target_temperature)

    def update_from_last_state(self, state):
        self._hvac_mode = state.state
        attributes = state.attributes
        fan_mode = attributes['fan_mode']
        if fan_mode in self._support_modes:
            self._fan_mode = fan_mode
        self._target_temperature = attributes['temperature']
        self._last_operation = attributes.get('last_on_operation')

    def update_from_sensor(self, state):
        self._current_temperature = float(state.state)
