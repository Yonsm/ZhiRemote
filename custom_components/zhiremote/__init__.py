from ..zhi.entity import ZHI_SCHEMA, ZhiEntity
from homeassistant.const import CONF_COMMAND, CONF_SENDER
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


CONF_SENSOR = 'sensor'


ZHI_REMOTE_SCHEMA = ZHI_SCHEMA | {
    vol.Required(CONF_SENDER): cv.string,
    vol.Required(CONF_COMMAND): dict,
    vol.Optional(CONF_SENSOR): cv.entity_id
}


class ZhiRemoteEntity(ZhiEntity):

    def __init__(self, conf):
        super().__init__(conf)
        self.sender = conf[CONF_SENDER]
        self.command = conf[CONF_COMMAND]
        self.state_sensor = conf.get(CONF_SENSOR)

    async def send_command(self, op):
        data = {'entity_id': self.sender}
        cmds = self.command[op].rsplit('_', 1)
        if len(cmds) > 1:
            data['hold_secs'] = int(cmds[1])
        cmds = cmds[0].rsplit('@', 1)
        if len(cmds) > 1:
            data['num_repeats'] = int(cmds[1])
        data['command'] = cmds[0] if '_' in cmds[0] else 'b64:' + cmds[0]
        await self.hass.services.async_call('remote', 'send_command', data)

    async def async_command(self, op):
        await self.send_command(op)
        await self.async_update_ha_state()
