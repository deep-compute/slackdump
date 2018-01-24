import time
import hashlib

from slackclient import SlackClient
from pymongo import MongoClient

from .slackhistory import SlackHistory

CONNECTION_SLEEP_INTERVAL = 1
EMPTY_READ_SLEEP_INTERVAL = .1


class SlackDump(object):
    def __init__(self, auth_token):
        self.auth_token = auth_token
        self.slack = SlackClient(self.auth_token)
        self.client = MongoClient()
        self.db = self.client.slackdb

    def make_connection(self):
        try:
            while not self.slack.rtm_connect():
                time.sleep(CONNECTION_SLEEP_INTERVAL)
            return True

        except Exception as ex:
            return ex

    def get_history(self, connect_time):
        history = SlackHistory(auth_token=self.auth_token,
                               connect_time=connect_time)
        history.start()

    def real_time_message(self):
        while True:
            msg = self.slack.rtm_read()

            if not msg:
                time.sleep(EMPTY_READ_SLEEP_INTERVAL)
                continue
            print(msg)

            if not len(msg[0]) == 1:

                try:
                    key = SlackHistory().get_key(msg[0])
                    msg[0]["key"] = key
                    SlackHistory().insert_into_db(msg[0])

                except Exception:
                    continue

    def start(self):
        try:
            p = self.make_connection()

            if p is True:
                self.get_history(time.time())
                self.real_time_message()

        except Exception:
            self.start()
