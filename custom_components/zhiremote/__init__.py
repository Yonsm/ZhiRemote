from ..zhi.restore import ZhiRestoreEntity
from ..zhi.entity import ZHI_SCHEMA, ZhiEntity
from homeassistant.const import CONF_COMMAND, CONF_SENDER
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

CONF_SENSOR = 'sensor'


ZHI_REMOTE_SCHEMA = ZHI_SCHEMA | {
    vol.Required(CONF_SENDER): cv.string,
    vol.Required(CONF_COMMAND): vol.Any(dict, cv.string),
    vol.Optional(CONF_SENSOR): cv.entity_id
}


class ZhiRemoteEntity(ZhiEntity, ZhiRestoreEntity):

    def __init__(self, conf):
        super().__init__(conf)
        self.sender = conf[CONF_SENDER]
        self.command = conf[CONF_COMMAND]
        self.state_sensor = conf.get(CONF_SENSOR)
        if isinstance(self.command, str):
            from os import path
            from homeassistant.util.yaml import load_yaml
            self.command = load_yaml(path.join(path.dirname(path.abspath(__file__)), 'codes', self.command + '.yaml'))

    async def send_command(self, *ops):
        command = self.command
        for op in ops:
            last_dict = command
            command = command.get(op)
            if command is None:
                from logging import getLogger
                getLogger(__name__).warning("No command for %s", ops)
                return
        if command[0] == '=':
            command = command[1:]
            ops = command.split('-')
            if len(ops) > 1:
                return await self.send_command(*ops)
            command = last_dict[command]
        data = {'entity_id': self.sender}
        cmds = command.rsplit('_', 1)
        if len(cmds) > 1:
            data['hold_secs'] = int(cmds[1])
        cmds = cmds[0].rsplit('@', 1)
        if len(cmds) > 1:
            data['num_repeats'] = int(cmds[1])
        data['command'] = cmds[0] if '_' in cmds[0] else 'b64:' + cmds[0]
        await self.hass.services.async_call('remote', 'send_command', data)

    async def async_command(self, *ops):
        await self.send_command(*ops)
        await self.async_update_ha_state()
