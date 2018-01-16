import time
import hashlib

from slacker import Slacker
from pymongo import MongoClient

client = MongoClient()
db = client.slack_db
collection = db.slack_db

def initialise(auth_token, start_time, end_time):
    slack = Slacker(auth_token)
    get_public_channels_history(slack, start_time, end_time)
    get_private_channels_history(slack, start_time, end_time)
    get_direct_channels_history(slack, start_time, end_time)

def get_public_channels_history(slack, start_time, end_time):
    public_channels = slack.channels.list().body['channels']
    for every_channel in public_channels:
        all_messages = slack.channels.history(every_channel['id'], end_time, start_time).body['messages']
        if all_messages:
            for every_message in all_messages:
                every_message["channel"] = every_channel['id']
                key = hashlib.sha1(every_message['channel'] + every_message['ts']).hexdigest()
                every_message["key"] = key
                db.slack_db.insert_one(every_message)
            print "Inserted all Public Channel data"

def get_private_channels_history(slack, start_time, end_time):
    private_channels = slack.groups.list().body['groups']
    for every_channel in private_channels:
        all_messages = slack.groups.history(every_channel['id'], end_time, start_time).body['messages']
        if all_messages:
            for every_message in all_messages:
                every_message["channel"] = every_channel['id']
                key = hashlib.sha1(every_message['channel'] + every_message['ts']).hexdigest()
                every_message["key"] = key
                db.slack_db.insert_one(every_message)
            print "Inserted all Private Channel data"

def get_direct_channels_history(slack, start_time, end_time):
    direct_channels = slack.im.list().body['ims']
    for counter in range(0, len(direct_channels)):
        all_messages = slack.im.history(direct_channels[counter]['id'], end_time, start_time).body['messages']
        if all_messages:
            for every_message in all_messages:
                every_message["channel"] = direct_channels[counter]['id']
                key = hashlib.sha1(every_message['channel'] + every_message['ts']).hexdigest()
                every_message["key"] = key
                db.slack_db.insert_one(every_message)
            print "Inserted all Direct Channel data"
