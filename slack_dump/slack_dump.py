import time
import pymongo
import hashlib
import datetime
import slack_history

from slackclient import SlackClient
from pymongo import MongoClient

client = MongoClient()
db = client.slack_db
collection = db.slack_db
CONNECTION_SLEEP_INTERVAL = 1
EMPTY_READ_SLEEP_INTERVAL = .1

def initialise(auth_token):
    token = auth_token
    get_real_time_message(token)

def get_real_time_message(token):
    try:
        slack = SlackClient(token)
        while not slack.rtm_connect():
            time.sleep(CONNECTION_SLEEP_INTERVAL)

        end = format(time.time(), '0.6f')
        slack_history.get_all_channels_history(token, end)

        while True:
            msg = slack.rtm_read()
            if not msg:
                time.sleep(EMPTY_READ_SLEEP_INTERVAL)
                continue
	    print msg

            if not len(msg[0]) == 1:
                try:
                    key = hashlib.sha1(msg[0]['channel'] + msg[0]['ts']).hexdigest()
		    msg[0]["key"] = key
		    res=db.slack_db.insert_one(msg[0])
		    print "Inserted!!"
		except Exception:
                    continue
    except Exception as ex:
        print ex
	get_real_time_message(token)
