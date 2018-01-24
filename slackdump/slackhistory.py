import time
import hashlib

from slacker import Slacker
from pymongo import MongoClient, ASCENDING, DESCENDING


class SlackHistory(object):

    def __init__(self, auth_token = 0, connect_time = time.time()):
        self.client = MongoClient()
        self.db = self.client.slackdb
        self.connect_time = connect_time
        self.auth_token = auth_token
        self.slack = Slacker(self.auth_token)
        self._collection = self.db.slackdb

    def start(self):
        self.get_public_channels_history()
        self.get_private_channels_history()
        self.get_direct_channels_history()

    def get_key(self, message):
        return hashlib.sha1((message['channel']
                             + message['ts']).encode('utf8')).hexdigest()

    def insert_into_db(self, message):
        self.db.slackdb.insert_one(message)
        print("Inserted")

    def get_history(self, slack_object, channel_id, end_time, start_time = 0):
        messages = []
        last_time_stamp = end_time
        oldest_time_stamp = start_time

        while True:
            response = slack_object.history(channel_id,
                                            last_time_stamp, oldest_time_stamp,
                                            count = 100).body

            messages.extend(response['messages'])

            for message in messages:
                message['channel'] = channel_id
                key = self.get_key(message)
                message["key"] = key
                print(message)
                self.insert_into_db(message)

            if (response['has_more'] == True):
                last_time_stamp = messages[-1]['ts']
                messages = []
            else:
                break

    def get_public_channels(self):
        return self.slack.channels.list().body['channels']

    def get_public_channels_history(self):
        public_channels = self.get_public_channels()
        
        for channel in public_channels:
            last_db_time = last_time = self.connect_time
            last_db_time = [one_record['ts'] for one_record in self._collection.find(
                {'channel': channel['id']}).sort('ts', ASCENDING).limit(1)]
            last_time = [one_record['ts'] for one_record in self._collection.find(
                {'channel': channel['id']}).sort('ts', DESCENDING).limit(1)]
            self.get_history(self.slack.channels, channel['id'], last_db_time)

            if last_time != self.connect_time:
                self.get_history(self.slack.channels,
                                 channel['id'], self.connect_time, last_time)

            print("Inserted Public channel data")

    def get_private_channels(self):
        return self.slack.groups.list().body['groups']

    def get_private_channels_history(self):
        private_channels = self.get_private_channels()
        
        for channel in private_channels:
            last_db_time = last_time = self.connect_time
            last_db_time = [one_record['ts'] for one_record in self._collection.find(
                {'channel': channel['id']}).sort('ts', ASCENDING).limit(1)]
            last_time = [one_record['ts'] for one_record in self._collection.find(
                {'channel': channel['id']}).sort('ts', DESCENDING).limit(1)]
            self.get_history(self.slack.groups, channel['id'], last_db_time)

            if last_time != self.connect_time:
                self.get_history(self.slack.groups,
                                 channel['id'], self.connect_time, last_time)

            print("Inserted Private channel data")

    def get_direct_channels(self):
        return self.slack.im.list().body['ims']

    def get_direct_channels_history(self):
        direct_channels = self.get_direct_channels()

        for counter in range(0, len(direct_channels)):
            last_db_time = last_time = self.connect_time
            last_db_time = [one_record['ts'] for one_record in self._collection.find(
                {'channel': direct_channels[counter]['id']}).sort('ts', ASCENDING).limit(1)]
            last_time = [one_record['ts'] for one_record in self._collection.find(
                {'channel': direct_channels[counter]['id']}).sort('ts', DESCENDING).limit(1)]

            self.get_history(
                self.slack.im, direct_channels[counter]['id'], last_db_time)

            if last_time != self.connect_time:
                self.get_history(self.slack.im,
                                 direct_channels[counter]['id'], self.connect_time, last_time)

            print("Inserted direct channel data")
