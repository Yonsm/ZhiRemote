from custom_components.zhiremote import ZHI_REMOTE_SCHEMA, ZhiRemoteEntity
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from ..zhi.entity import ZhiEntity, ZHI_SCHEMA
from ..zhi.cover import ZhiTravelCover, PLATFORM_SCHEMA
from homeassistant.const import CONF_COMMAND, CONF_SENDER

CONF_SENSOR = 'sensor'
CONF_TRAVEL = 'travel'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(ZHI_REMOTE_SCHEMA | {vol.Optional(CONF_TRAVEL): cv.positive_int})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    async_add_entities([ZhiRemoteCover(config)])


class ZhiRemoteCover(ZhiRemoteEntity, ZhiTravelCover):

    def __init__(self, conf):
        ZhiRemoteEntity.__init__(self, conf)
        ZhiTravelCover.__init__(self, conf.get(CONF_TRAVEL), conf.get(CONF_SENSOR))

    async def control_cover(self, op):
        await self.send_command(('open', 'close', 'stop')[op])
        return True
