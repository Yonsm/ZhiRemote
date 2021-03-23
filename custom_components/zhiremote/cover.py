import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from ..zhi.entity import ZhiEntity, ZHI_SCHEMA
from ..zhi.cover import ZhiTravelCover, PLATFORM_SCHEMA
from homeassistant.const import CONF_SENDER

CONF_COMMAND_OPEN = 'command_open'
CONF_COMMAND_CLOSE = 'command_close'
CONF_COMMAND_STOP = 'command_stop'
CONF_POSITION_SENSOR = 'position_sensor'
CONF_TRAVEL_TIME = 'travel_time'
CONF_COVERS = 'covers'

COVERS_SCHEMA = vol.Schema(ZHI_SCHEMA | {
    vol.Required(CONF_COMMAND_OPEN): cv.string,
    vol.Required(CONF_COMMAND_CLOSE): cv.string,
    vol.Required(CONF_COMMAND_STOP): cv.string,
    vol.Optional(CONF_TRAVEL_TIME, default=0): cv.positive_int,
    vol.Optional(CONF_POSITION_SENSOR): cv.entity_id,
})


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_COVERS): vol.Schema([COVERS_SCHEMA]),
    vol.Required(CONF_SENDER): cv.string,
})


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    covers = config.get(CONF_COVERS)
    sender = config.get(CONF_SENDER)
    async_add_devices([ZhiRemoteCover(sender, conf) for conf in covers])


class ZhiRemoteCover(ZhiEntity, ZhiTravelCover):

    def __init__(self, sender, conf):
        ZhiEntity.__init__(self, conf)
        ZhiTravelCover.__init__(self, conf[CONF_TRAVEL_TIME], conf.get(CONF_POSITION_SENSOR))
        self.sender = sender
        self.commands = [conf[k] for k in [CONF_COMMAND_OPEN, CONF_COMMAND_CLOSE, CONF_COMMAND_STOP]]

    async def async_control_cover(self, op):
        data = {'entity_id': self.sender, 'command': self.commands[op]}
        await self.hass.services.async_call('remote', 'send_command', data)
        return True
