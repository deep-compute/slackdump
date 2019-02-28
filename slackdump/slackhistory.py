import os
import time
import requests

from expiringdict import ExpiringDict
from slackclient import SlackClient
from deeputil import Dummy, AttrDict

DUMMY_LOG = Dummy()


class SlackHistory(object):
    CACHE_LEN = 100
    CACHE_LIFE_TIME = 500
    CHUNK_SIZE = 1024

    def __init__(self, auth_token=None, connect_time=time.time(),
                 file_path=None, store=None, log=DUMMY_LOG):
        self.file_path = file_path
        self.connect_time = connect_time
        self.auth_token = auth_token
        self.slack = SlackClient(self.auth_token)
        self.log = log
        self.store = store
        self.username_cache = ExpiringDict(self.CACHE_LEN,
                                           self.CACHE_LIFE_TIME)

    def get_username(self, _id):
        name = self.username_cache

        if _id in name:
            return name['user_id']

        user_name = self.slack.api_call("users.info", user=_id)
        name['user_id'] = user_name['user']['name']

        return name['user_id']

    def get_permalink(self, channel_id, ts):
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

    def parse_dict(self, msg):
        p = self.get_permalink(msg.channel, msg.ts)
        if p:
            msg.permalink = p

        if 'user' in msg:
            user_name = self.get_username(msg.user)
            msg.user_name = user_name

        if 'text' in msg and '<@' in msg.text:
            msg.text = self.replace_text(msg.text)

        if 'uploaded a file' in msg.text:
            filename = str(msg.ts) + '_' + msg.file.name.replace(' ', '_')
            self.get_file(msg.file.url_private_download, filename)

        return msg

    def get_history(self, slack, _id, _name, end_ts, start_ts=0):
        messages = []
        ts = end_ts
        #import pdb;pdb.set_trace()
        while True:
            response = self.slack.api_call(slack, channel=_id,
                                           latest=ts, oldest=start_ts,
                                           count=1000)

            if 'messages' not in response:
                return 0

            messages.extend(response['messages'])

            for message in messages:
                msg = AttrDict(message)
                msg.channel = _id
                msg.channel_name = _name

                self.parse_dict(msg)

                self.store.insert_into_db(msg)

            num = len(messages)

            if response['has_more']:
                ts = messages[-1]['ts']
                messages = []
            else:
                return num
                break

    def get_channel_status(self, _type, _id, name):
        #import pdb;pdb.set_trace()
        num = 0
        last_ts = self.store.get_oldest_timestamp(_id)

        if not last_ts:
            last_ts = self.connect_time

        num = self.get_history(_type, _id, name, last_ts)
        latest_ts = self.store.get_latest_timestamp(_id)

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
