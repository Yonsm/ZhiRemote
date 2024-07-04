from . import ZHI_REMOTE_SCHEMA, ZhiRemoteEntity
from ..zhi.restore import ZhiRestoreEntity
from homeassistant.components.media_player import MediaPlayerEntity, PLATFORM_SCHEMA, MediaPlayerEntityFeature
from homeassistant.const import STATE_HOME, STATE_OFF, STATE_ON

MediaPlayerEntityFeature.FEATURES = {
    'on': MediaPlayerEntityFeature.TURN_ON,
    'off': MediaPlayerEntityFeature.TURN_OFF,
    'vol+': MediaPlayerEntityFeature.VOLUME_STEP,
    'vol-': MediaPlayerEntityFeature.VOLUME_STEP,
    'mute': MediaPlayerEntityFeature.VOLUME_MUTE,
    'prev': MediaPlayerEntityFeature.PREVIOUS_TRACK,
    'next': MediaPlayerEntityFeature.NEXT_TRACK,
    # 'sources': MediaPlayerEntityFeature.SELECT_SOURCE,
}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(ZHI_REMOTE_SCHEMA)


def setup_platform(hass, conf, add_entities, discovery_info=None):
    add_entities([ZhiRemoteMediaPlayer(conf)])


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
            features |= MediaPlayerEntityFeature.FEATURES[op]
        return features

    async def async_turn_on(self):
        self._state = STATE_ON
        await self.async_command('on')

    async def async_turn_off(self):
        self._state = STATE_OFF
        await self.async_command('off')

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
