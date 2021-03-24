from . import ZHI_REMOTE_SCHEMA, ZhiRemoteEntity
from ..zhi.restore import ZhiRestoreEntity
from homeassistant.components.media_player import MediaPlayerEntity, PLATFORM_SCHEMA
from homeassistant.components.media_player.const import SUPPORT_TURN_OFF, SUPPORT_TURN_ON, SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK, SUPPORT_VOLUME_STEP, SUPPORT_VOLUME_MUTE
from homeassistant.const import STATE_HOME, STATE_OFF, STATE_ON

SUPPORT_FEATURES = {
    'open': SUPPORT_TURN_ON,
    'shut': SUPPORT_TURN_OFF,
    'vol+': SUPPORT_VOLUME_STEP,
    'vol-': SUPPORT_VOLUME_STEP,
    'mute': SUPPORT_VOLUME_MUTE,
    'prev': SUPPORT_PREVIOUS_TRACK,
    'next': SUPPORT_NEXT_TRACK,
    # 'sources': SUPPORT_SELECT_SOURCE,
}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(ZHI_REMOTE_SCHEMA)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    async_add_devices([ZhiRemoteMediaPlayer(config)])


class ZhiRemoteMediaPlayer(ZhiRemoteEntity, MediaPlayerEntity, ZhiRestoreEntity):

    _state = STATE_OFF

    @property
    def state(self):
        return self._state

    # @property
    # def media_content_type(self):
    #     """Content type of current playing media."""
    #     return MEDIA_TYPE_CHANNEL

    @property
    def supported_features(self):
        features = 0
        for op in self.command:
            features |= SUPPORT_FEATURES[op]
        return features

    async def async_turn_on(self):
        self._state = STATE_ON
        await self.async_command('open')

    async def async_turn_off(self):
        self._state = STATE_OFF
        await self.async_command('shut')

    async def async_volume_up(self):
        await self.async_command('vol+')

    async def async_volume_down(self):
        await self.async_command('vol-')

    async def async_mute_volume(self, mute):
        await self.async_command('mute')

    async def async_media_previous_track(self):
        await self.async_command('prev')

    async def async_media_next_track(self):
        await self.async_command('next')

    def update_from_last_state(self, state):
        self._state = state.state

    def update_from_sensor(self, state):
        self._state = (STATE_OFF, STATE_ON)[state.state in (STATE_ON, STATE_HOME)]
