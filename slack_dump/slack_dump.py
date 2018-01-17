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
    if collection.count() == 0:
        start1 = 0
    else:
        res = db.slack_db.find().sort('ts',pymongo.DESCENDING).limit(1)
	for r in res:
            start1 = r['ts']
    get_real_time_message(token, start1)

def get_real_time_message(token, start1):
    try:
        slack = SlackClient(token)
        while not slack.rtm_connect():
            time.sleep(CONNECTION_SLEEP_INTERVAL)
        end = format(time.time(), '0.6f')

        slack_history.get_all_channels_history(token,start1,end)

        while True:
            msg = slack.rtm_read()
            if not msg:
                time.sleep(EMPTY_READ_SLEEP_INTERVAL)
                continue
	    print (msg)

            if not len(msg[0]) == 1:
                try:
                    key = hashlib.sha1(msg[0]['channel'] + msg[0]['ts']).hexdigest()
		    msg[0]["key"] = key
		    res=db.slack_db.insert_one(msg[0])
		    print ("Inserted!!")

		except Exception:
                    continue

    except Exception as e:
        print (e)
	start1 = format(time.time(), '0.6f')
	print ("Connection failed at : "+str(start1))
	get_real_time_message(token,start1)
