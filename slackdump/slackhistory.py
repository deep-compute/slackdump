import os
import time
import hashlib
from copy import deepcopy
from multiprocessing.pool import ThreadPool
from operator import itemgetter

import requests
from expiringdict import ExpiringDict
from slackclient import SlackClient
from diskdict import DiskDict
from deeputil import Dummy, AttrDict

DUMMY_LOG = Dummy()


class SlackHistory(object):
    '''
    FIXME: explain the responsbilities of this abstraction
    This module gives all the history between given timestamps
    '''

    CACHE_LEN = 100
    CACHE_LIFE_TIME = 500
    CHUNK_SIZE = 1024

    def __init__(self, auth_token=None, connect_time=time.time(),
                 dict_path='/tmp', file_path=None,
                 targets=None, log=DUMMY_LOG):
        self.auth_token = auth_token
        self.slack = SlackClient(self.auth_token)
        self.connect_time = connect_time

        self.targets = targets
        self.file_path = file_path
        self.dd = DiskDict(dict_path + "/disk.dict")

        self.log = log
        self.username_cache = ExpiringDict(self.CACHE_LEN,
                                           self.CACHE_LIFE_TIME)
        self._pool = ThreadPool()

    def get_username(self, _id):
        '''
        >>> from mock import Mock
        >>> ob = SlackHistory()
        >>> ob.slack.api_call = Mock(ob.slack.api_call, return_value={"user":{"name":"asdf"}})
        >>> ob.get_username(677)
        'asdf'
        '''
        name = self.username_cache

        if _id in name:
            return name['user_id']

        user_name = self.slack.api_call("users.info", user=_id)
        name['user_id'] = user_name['user']['name']

        return name['user_id']

    def get_permalink(self, channel_id, ts):
        '''
        >>> from mock import Mock
        >>> ob = SlackHistory()
        >>> ob.slack.api_call = Mock(ob.slack.api_call,
        ...     return_value={"permalink":'https://justadummy.com'})
        >>> ob.get_permalink(677, 123545)
        'https://justadummy.com'
        >>> ob.slack.api_call = Mock(ob.slack.api_call,
        ...     return_value={"error":"No link found"})
        >>> ob.get_permalink(677, 123545)
        False
        '''
        link = self.slack.api_call('chat.getPermalink', channel=channel_id,
                                   message_ts=ts)
        if 'permalink' in link:
            return link['permalink']

        return False

    def get_file(self, url, filename):
        headers = {'Authorization': 'Bearer ' + self.auth_token}
        r = requests.get(url, headers=headers)
        with open(os.path.join(self.file_path, filename), 'wb') as f:
            for chunk in r.iter_content(self.CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

    def replace_text(self, text):
        '''
        >>> from mock import Mock
        >>> ob = SlackHistory()
        >>> ob.get_username = Mock(ob.get_username, return_value="asdf")
        >>> ob.replace_text('<@677> hii')
        '@asdf hii'
        '''
        self.log.debug("replacing text")
        text_list = text.split(' ')
        for counter in range(0, len(text_list)):
            if '<@' in text_list[counter]:
                user_id = text_list[counter].split('<@')[1].split('>')[0]
                if '|' in user_id:
                    user_id = user_id.split('|')[0]
                username = self.get_username(user_id)
                text_list[counter] = '@' + username

        return ' '.join(text_list)

    def get_key(self, channel, timestamp):
        '''
        >>> ob = SlackHistory()
        >>> ob.get_key("U8S2NSX6J", "1518582605.000239")
        '18a920561dec17877db2a4628c13734e2f63df1d'
        '''
        return hashlib.sha1((channel + timestamp).encode('utf8')).hexdigest()

    def parse_dict(self, msg):
        '''
        >>> from mock import Mock
        >>> ob = SlackHistory()
        >>> ob.get_permalink = Mock(ob.get_permalink, return_value="http://justadummy.com")
        >>> ob.replace_text = Mock(ob.replace_text, return_value="uploaded a file @asdf")
        >>> ob.get_username = Mock(ob.get_username, return_value="justaname")
        >>> ob.get_file = Mock()
        >>> ob.parse_dict(AttrDict({'channel': 'abcd', 'user': 'U8S2NSX6J', 'text': 'uploaded a file <@123>', 'ts': '1518582605.000239'}))
        AttrDict({'permalink': 'http://justadummy.com', 'text': 'uploaded a file @asdf', 'ts': '1518582605.000239', 'user': 'U8S2NSX6J', 'user_name': 'justaname', 'channel': 'abcd'})
        '''
        p = self.get_permalink(msg.channel, msg.ts)
        if p:
            msg.permalink = p

        if 'user' in msg:
            user_name = self.get_username(msg.user)
            msg.user_name = user_name

        if 'text' in msg and '<@' in msg.text:
            msg.text = self.replace_text(msg.text)

        if 'uploaded a file' in msg.text and self.file_path is not None:
            filename = str(msg.ts) + '_' + msg.file.name.replace(' ', '_')
            self.get_file(msg.file.url_private_download, filename)


        return msg

    def change_status(self, _id, ts):
        if _id + '_oldest' in self.dd.keys() and ts > self.dd[_id + '_oldest']:
            self.dd[_id + '_latest'] = ts
        else:
            self.dd[_id + '_oldest'] = ts

    def _send_msgs_to_target(self, target, msg):
        while 1:
            try:
                msg['key'] = self.get_key(msg['channel'], msg['ts'])
                target.insert_msg(msg)
                self.change_status(msg['channel'], msg['ts'])
                break
            except (SystemExit, KeyboardInterrupt): raise
            except:
                self.log.exception('_send_msgs_to_target_failed', target=target)
                time.sleep(self.WAIT_TIME_TARGET_FAILURE)

    def _write_messages(self, msg):
        if self.targets:
            fn = self._send_msgs_to_target

            jobs = []
            for t in self.targets:
                jobs.append(self._pool.apply_async(fn, (t, deepcopy(msg))))

            for j in jobs:
                j.wait()


    def get_history(self, slack, _id, _name, end_ts, start_ts=0):
        '''
        >>> from mock import Mock
        >>> ob = SlackHistory()
        >>> ob.slack.api_call = Mock(ob.slack.api_call)
        >>> ob.slack.api_call.side_effect= [{'messages' :[{'message': 'Dummy <@123>', 'ts': '123.234'}], 'has_more': True}, {'messages' :[{'message': 'Dummy <@123>', 'ts': '122.234'}], 'has_more': False}]
        >>> ob.parse_dict = Mock(ob.parse_dict, return_value={'message': 'Dummy @asdf', 'ts': '123.234'})
        >>> ob._write_messages = Mock()
        >>> ob.get_history('users.info', '1234', 'general', 12345)
        2
        '''
        messages = []
        ts = end_ts
        num = 0
        while True:
            response = self.slack.api_call(slack, channel=_id,
                                           latest=ts, oldest=start_ts,
                                           count=1000)
            if 'messages' not in response:
                return num

            messages.extend(response['messages'])
            messages = sorted(messages, key=itemgetter('ts'))
            for message in messages:
                msg = AttrDict(message)
                msg.channel = _id
                msg.channel_name = _name

                msg = self.parse_dict(msg)

                self._write_messages(dict(msg))

            num += len(messages)

            if response['has_more']:
                ts = messages[-1]['ts']
                messages = []
            else:
                return num

    def get_channel_status(self, _type, _id, name):

        if not _id + '_oldest' in self.dd.keys():
            last_ts = self.connect_time
        else:
            last_ts = self.dd[_id + '_oldest']

        num = self.get_history(_type, _id, name, last_ts)

        if not _id + '_latest' in self.dd.keys():
            latest_ts = 0
        else:
            latest_ts = self.dd[_id + '_latest']

        if latest_ts != self.connect_time:
            num = num + self.get_history(_type, _id, name, self.connect_time, latest_ts)

        self.log.info("finished_inserting_channel_data", channel=_id,
                channel_name=name, num_msg=num, type='metric')

        time.sleep(1)

    def get_public_channels_list(self):
        _type = "channels.history"
        public_channels = self.slack.api_call("channels.list")['channels']
        for channel in public_channels:
            self.log.info("fetching_public_channel_message", channel=channel['name'])
            self.get_channel_status(_type, channel['id'], channel['name'])

    def get_private_channels_list(self):
        _type = "groups.history"
        private_channels = self.slack.api_call("groups.list")['groups']
        for channel in private_channels:
            self.log.info("fetching_private_channel_message", channel=channel['name'])

            self.get_channel_status(_type, channel['id'], channel['name'])

    def get_direct_channels_list(self):
        _type = "im.history"
        direct_channels = self.slack.api_call("im.list")['ims']
        for channel in direct_channels:
            self.log.info("fetching_direct_channel_message", channel=channel['user'])
            self.get_channel_status(_type, channel['id'], channel['user'])

    def start(self):
        self.get_public_channels_list()
        self.get_private_channels_list()
        self.get_direct_channels_list()
