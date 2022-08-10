from . import ZHI_REMOTE_SCHEMA, ZhiRemoteEntity
from homeassistant.components.fan import FanEntity, PLATFORM_SCHEMA, SPEED_OFF, DIRECTION_REVERSE, DIRECTION_FORWARD, SUPPORT_PRESET_MODE, SUPPORT_DIRECTION, SUPPORT_OSCILLATE
from homeassistant.const import STATE_HOME, STATE_OFF, STATE_ON


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(ZHI_REMOTE_SCHEMA)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([ZhiRemoteFan(config)])


class ZhiRemoteFan(ZhiRemoteEntity, FanEntity):

    def __init__(self, conf):
        super().__init__(conf)

        self._mode = SPEED_OFF
        self._last_mode = None

        self._direction = DIRECTION_FORWARD
        self._oscillating = False

    @property
    def supported_features(self):
        features = 0
        if 'preset_modes' in self.command:
            features = SUPPORT_PRESET_MODE
        if DIRECTION_REVERSE in self.command and DIRECTION_FORWARD in self.command:
            features |= SUPPORT_DIRECTION
        if 'oscillate' in self.command:
            features |= SUPPORT_OSCILLATE
        return features

    @property
    def state(self):
        return STATE_OFF if self._mode == SPEED_OFF else STATE_ON

    @property
    def preset_modes(self):
        return list(self.command.get('preset_modes').keys())

    @property
    def preset_mode(self):
        return self._mode

    @property
    def oscillating(self):
        return self._oscillating

    @property
    def current_direction(self):
        return self._direction

    async def async_turn_on(self, speed=None, percentage=None,  preset_mode=None, **kwargs):
        if 'on' in self.command:
            await self.send_command('on')
            from asyncio import sleep
            sleep(1)
        if 'preset_modes' in self.command:
            return self.set_preset_mode(preset_mode or self._last_mode or self.preset_modes[1])
        self._mode = STATE_ON
        await self.async_update_ha_state()

    async def async_turn_off(self):
        self._mode = SPEED_OFF
        await self.async_command('off')

    async def async_set_preset_mode(self, preset_mode):
        self._mode = preset_mode
        if preset_mode != SPEED_OFF:
            self._last_mode = preset_mode
        await self.async_command('preset_modes', preset_mode)

    async def async_oscillate(self, oscillating):
        self._oscillating = oscillating
        await self.async_command('oscillate')

    async def async_set_direction(self, direction):
        self._direction = direction
        await self.async_command(direction)

    def update_from_last_state(self, state):
        attributes = state.attributes
        self._mode = attributes.get('speed', self._mode)
        #self._last_mode = attributes.get('last_mode', self._last_mode)
        self._direction = attributes.get('direction', self._direction)
        self._oscillating = attributes.get('oscillating', self._oscillating)

    def update_from_sensor(self, state):
        self._mode = (self._last_mode or self.preset_modes[1] if 'preset_modes' in self.command else STATE_ON) if state.state in [STATE_ON, STATE_HOME] else SPEED_OFF
