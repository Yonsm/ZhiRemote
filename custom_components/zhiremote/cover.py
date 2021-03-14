import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.cover import CoverEntity, PLATFORM_SCHEMA, SUPPORT_OPEN, SUPPORT_CLOSE
from homeassistant.const import CONF_NAME, CONF_SENDER, STATE_CLOSED
from homeassistant.helpers.event import track_utc_time_change
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.core import callback

DEFAULT_NAME = 'Remote'

CONF_COMMAND_OPEN = 'command_open'
CONF_COMMAND_CLOSE = 'command_close'
CONF_COMMAND_STOP = 'command_stop'
CONF_POS_SENSOR = 'position_sensor'
CONF_TRAVEL_TIME = 'travel_time'
CONF_COVERS = 'covers'

COVERS_SCHEMA = vol.Schema({
    vol.Required(CONF_COMMAND_OPEN): cv.string,
    vol.Required(CONF_COMMAND_CLOSE): cv.string,
    vol.Optional(CONF_COMMAND_STOP): cv.string,
    vol.Optional(CONF_TRAVEL_TIME, default=0): cv.positive_int,
    vol.Optional(CONF_POS_SENSOR): cv.entity_id,
})


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_COVERS, default={}): vol.Schema({cv.string: COVERS_SCHEMA}),
    vol.Required(CONF_SENDER): cv.string,
})


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    covers = config.get(CONF_COVERS)
    sender = config.get(CONF_SENDER)
    async_add_devices([ZhiRemoteCover(hass, sender, name, conf) for name, conf in covers.items()], True)
    return True


class ZhiRemoteCover(CoverEntity, RestoreEntity):
    """Representation of a cover."""

    def __init__(self, hass, sender, name, conf):
        """Initialize the cover."""
        self.hass = hass
        self.sender = sender

        self._name = name
        self._cmd_open = conf[CONF_COMMAND_OPEN]
        self._cmd_close = conf[CONF_COMMAND_CLOSE]
        cmd_stop = conf.get(CONF_COMMAND_STOP)
        travel_time = conf.get(CONF_TRAVEL_TIME)
        pos_entity_id = conf.get(CONF_POS_SENSOR)

        if travel_time:
            self._position = 50
            self._travel_time = travel_time
            self._step = round(100.0 / travel_time, 2)
            self._device_class = 'window'
        else:
            self._position = None
            self._device_class = 'garage'

        if cmd_stop:
            self._cmd_stop = cmd_stop
            self._supported_features = None
        else:
            self._position = None
            self._supported_features = (SUPPORT_OPEN | SUPPORT_CLOSE)
            self._device_class = 'garage'

        self._requested_closing = True
        self._unsub_listener_cover = None
        self._is_opening = False
        self._is_closing = False
        self._travel = 0
        self._closed = False
        self._delay = False

        if pos_entity_id:
            async_track_state_change(hass, pos_entity_id, self._async_pos_changed)
            temp_state = hass.states.get(pos_entity_id)
            if temp_state:
                self._async_update_pos(temp_state)

    def _async_update_pos(self, state):
        if state.state in ('false', STATE_CLOSED, 'off'):
            if self._device_class == 'window':
                self._position = 0
            self._closed = True
        else:
            self._closed = False
            if self._position == 0:
                self._position = 100

    @callback
    async def _async_pos_changed(self, entity_id, old_state, new_state):
        if new_state is None:
            return
        self._async_update_pos(new_state)
        await self.async_update_ha_state()

    @property
    def unique_id(self):
        from homeassistant.util import slugify
        return self.__class__.__name__.lower() + '.' + slugify(self.name)

    @property
    def name(self):
        return self._name

    @property
    def device_class(self):
        return self._device_class

    @property
    def supported_features(self):
        return self._supported_features or super().supported_features

    @property
    def should_poll(self):
        return False

    @property
    def current_cover_position(self):
        return self._position

    @property
    def is_closed(self):
        if self._position is None:
            return self._closed
        else:
            return self._position == 0

    @property
    def is_closing(self):
        return self._is_closing

    @property
    def is_opening(self):
        return self._is_opening

    @property
    def device_class(self):
        return self._device_class

    def close_cover(self, **kwargs):
        if self._position == 0:
            return
        elif self._position is None:
            if self.send_command(self._cmd_close):
                self._closed = True
                self.schedule_update_ha_state()
            return

        if self.send_command(self._cmd_close):
            self._travel = self._travel_time + 1
            self._is_closing = True
            self._listen_cover()
            self._requested_closing = True
            self.schedule_update_ha_state()

    def open_cover(self, **kwargs):
        if self._position == 100:
            return
        elif self._position is None:
            if self.send_command(self._cmd_open):
                self._closed = False
                self.schedule_update_ha_state()
            return

        if self.send_command(self._cmd_open):
            self._travel = self._travel_time + 1
            self._is_opening = True
            self._listen_cover()
            self._requested_closing = False
            self.schedule_update_ha_state()

    def set_cover_position(self, position, **kwargs):
        if position <= 0:
            self.close_cover()
        elif position >= 100:
            self.open_cover()
        elif round(self._position) == round(position):
            return
        elif self._travel > 0:
            return
        else:
            steps = abs((position - self._position) / self._step)
            if steps >= 1:
                self._travel = round(steps, 0)
            else:
                self._travel = 1
            self._requested_closing = position < self._position
            if self._requested_closing:
                if self.send_command(self._cmd_close):
                    self._listen_cover()
            else:
                if self.send_command(self._cmd_open):
                    self._listen_cover()

    def stop_cover(self, **kwargs):
        self._is_closing = False
        self._is_opening = False
        if self._position is None:
            self.send_command(self._cmd_stop)
            return
        elif self._position > 0 and self._position < 100:
            self.send_command(self._cmd_stop)

        if self._unsub_listener_cover is not None:
            self._unsub_listener_cover()
            self._unsub_listener_cover = None

    def _listen_cover(self):
        if self._unsub_listener_cover is None:
            self._unsub_listener_cover = track_utc_time_change(
                self.hass, self._time_changed_cover)
            self._delay = True

    def _time_changed_cover(self, now):
        if self._delay:
            self._delay = False
        else:
            if self._requested_closing:
                if round(self._position - self._step) > 0:
                    self._position -= self._step
                else:
                    self._position = 0
                    self._travel = 0
            else:
                if round(self._position + self._step) < 100:
                    self._position += self._step
                else:
                    self._position = 100
                    self._travel = 0

            self._travel -= 1

            if self._travel <= 0:
                self.stop_cover()

            self.schedule_update_ha_state()

    def send_command(self, command):
        data = {'entity_id': self.sender, 'command': command}
        self.hass.services.call('remote', 'send_command', data)
        return True

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()

        if last_state:
            self._position = last_state.attributes['current_position']
