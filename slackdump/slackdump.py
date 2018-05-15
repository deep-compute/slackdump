import time
import traceback

from slackclient import SlackClient
from expiringdict import ExpiringDict
from deeputil import Dummy, AttrDict, keeprunning

from slackhistory import SlackHistory

DUMMY_LOG = Dummy()


class SlackDump(object):
    '''
    FIXME: Document the Responsibilities of class
    '''
    CONNECTION_SLEEP_INTERVAL = 1
    EMPTY_READ_SLEEP_INTERVAL = .1
    CACHE_EXPIRY_TIME = 60
    CACHE_LEN = 100

    def __init__(self, auth_token=None, file_path=None,
                 store=None, targets=None, status_path='/tmp/', log=DUMMY_LOG):
        self.file_path = file_path
        self.auth_token = auth_token
        self.log = log
        self.store = store
        self.targets = targets
        self.status_path = status_path
        self.h = SlackHistory(auth_token=self.auth_token,
                              file_path=self.file_path,
                              dict_path=self.status_path,
                              targets=self.targets, log=self.log)

        self.slack = SlackClient(self.auth_token)
        self.channel_name_cache = ExpiringDict(self.CACHE_LEN,
                                               self.CACHE_EXPIRY_TIME)

    def make_connection(self):
        self.log.debug('In make connection')
        try:
            while not self.slack.rtm_connect():
                time.sleep(self.CONNECTION_SLEEP_INTERVAL)
            return True

        except Exception:
            self.log.exception('in make_connection')
            return False

    def get_history(self, connect_time):
        history = SlackHistory(log=self.log,
                               auth_token=self.auth_token,
                               file_path=self.file_path,
                               dict_path=self.status_path,
                               targets=self.targets,
                               connect_time=connect_time)
        history.start()

    def get_channelname(self, _id):
        '''
        >>> from mock import Mock
        >>> def side_effect(value, channel='qwer'):
        ...     if value == 'channels.info':
        ...         return {'channel': {'name': 'asdf'}}
        ...     if value == 'groups.info':
        ...         return {"group": {'name': 'abcd'}}
        ...     if value == 'im.list':
        ...         return {'ims': [{'id': 'D1234', 'user': 'U123'}, {'id': 'D6521', 'user': 'U123'}]}
        >>> ob = SlackDump()
        >>> ob.slack.api_call = Mock(side_effect=side_effect)
        >>> ob.h.get_username = Mock(ob.h.get_username, return_value='just')
        >>> ob.get_channelname('G1234')
        'abcd'
        >>> ob.get_channelname('C1234')
        'asdf'
        >>> ob.get_channelname('D1234')
        'just'
        '''
        name = AttrDict(self.channel_name_cache)

        if _id in name:
            return name.id

        if _id.startswith('C'):
            info = self.slack.api_call("channels.info", channel=_id)
            name.id = info['channel']['name']

        elif _id.startswith('G'):
            info = self.slack.api_call("groups.info", channel=_id)
            name.id = info['group']['name']

        elif _id.startswith('D'):
            ch_list = self.slack.api_call("im.list")['ims']
            for counter in range(len(ch_list)):
                if ch_list[counter]['id'] == _id:
                    name.id = self.h.get_username(ch_list[counter]['user'])

        return name.id

    def parse_message(self, msg):
        '''
        >>> from mock import Mock
        >>> ob = SlackDump()
        >>> ob.h.get_username = Mock(ob.h.get_username, return_value='name')
        >>> ob.get_channelname = Mock(ob.get_channelname, return_value='general')
        >>> ob.h.get_permalink = Mock(ob.h.get_permalink, return_value='http://justadummy.com')
        >>> ob.h.replace_text = Mock(ob.h.replace_text, return_value='@name uploaded a file and wrote a message')
        >>> ob.h.get_file= Mock()
        >>> ob.parse_message(AttrDict({'text': '<@123> uploaded a file and wrote a message', 'user': '123', 'channel': 'U1A34FT', 'ts': '123.234'}))
        AttrDict({'permalink': 'http://justadummy.com', 'text': '@name uploaded a file and wrote a message', 'ts': '123.234', 'channel_name': 'general', 'user': '123', 'user_name': 'name', 'channel': 'U1A34FT'})
        '''

        if 'user' in msg:
                msg.user_name = self.h.get_username(msg.user)

        if 'channel' in msg:
            msg.channel_name = self.get_channelname(msg.channel)

        if 'ts' in msg and 'channel' in msg:
            p = self.h.get_permalink(msg.channel, msg.ts)
            if p:
                msg.permalink = p

        if 'text' in msg and '<@' in msg.text:
            msg.text = self.h.replace_text(msg.text)
            if self.file_path is not None and "uploaded a file:" in msg.text:
                filename = msg.ts + "_" + msg.file['name'].replace(' ', '_')
                self.h.get_file(msg.file.url_private_download, filename)

        if 'subtype' in msg:
            if msg.subtype == 'message_changed':
                msg.message.text = self.h.replace_text(msg.message.text)
                msg.user_name = self.h.get_username(msg.message.user)

        return msg

    def real_time_message(self):
        self.log.info("completed history")
        while True:
            msg = self.slack.rtm_read()

            if not msg:
                time.sleep(self.EMPTY_READ_SLEEP_INTERVAL)
                continue

            if len(msg[0]) == 1:
                continue
            msg = AttrDict(msg[0])
            self.log.debug("Message recieved", msg=msg)

            msg = self.parse_message(msg)
            self.h._write_messages(dict(msg))

    def log_exception(self, __fn__):
        self.log.exception('error_in_rtm', fn=__fn__.func_name,
                           tb=repr(traceback.format_exc()))

    @keeprunning(wait_secs=1, on_error=log_exception)
    def start(self):
        p = self.make_connection()

        if p is True:
            self.get_history(time.time())
            self.real_time_message()
