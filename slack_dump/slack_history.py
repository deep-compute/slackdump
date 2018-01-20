import time
import hashlib
import pymongo

from slacker import Slacker
from pymongo import MongoClient

client = MongoClient()
db = client.slack_db
collection = db.slack_db


def get_all_channels_history(auth_token, connect_time):
    slack = Slacker(auth_token)
    get_public_channels_history(slack, connect_time)
    get_private_channels_history(slack, connect_time)
    get_direct_channels_history(slack, connect_time)


def getHistory(pageableObject, channelId, end_time, start_time=0):
    messages = []
    lastTimestamp = end_time
    oldest = start_time
    while(True):
        response = pageableObject.history(
            channelId, lastTimestamp, oldest, count=10).body
        messages.extend(response['messages'])
        for every_message in messages:
            every_message['channel'] = channelId
            key = hashlib.sha1(
                every_message['channel'] + every_message['ts']).hexdigest()
            every_message["key"] = key
            print every_message
            res = db.slack_db.insert_one(every_message)
        if (response['has_more'] == True):
            lastTimestamp = messages[-1]['ts']
            messages = []
        else:
            break


def get_public_channels_history(slack, connect_time):
    public_channels = slack.channels.list().body['channels']
    for every_channel in public_channels:
        half_time = db.slack_db.find({'channel': every_channel['id']}).sort(
            'ts', pymongo.ASCENDING).limit(1)
        temp1 = connect_time
        temp2 = connect_time
        for temp in half_time:
            temp1 = temp['ts']
        last_time = db.slack_db.find({'channel': every_channel['id']}).sort(
            'ts', pymongo.DESCENDING).limit(1)
        for temp in last_time:
            temp2 = str(temp['ts'])
        getHistory(slack.channels, every_channel['id'], temp1)
        if (temp) != connect_time:
            getHistory(slack.channels,
                       every_channel['id'], connect_time, temp2)
        print "Inserted Public channel data"


def get_private_channels_history(slack, connect_time):
    private_channels = slack.groups.list().body['groups']
    for every_channel in private_channels:
        half_time = db.slack_db.find({'channel': every_channel['id']}).sort(
            'ts', pymongo.ASCENDING).limit(1)
        temp1 = connect_time
        temp2 = connect_time
        for temp in half_time:
            temp1 = temp['ts']
        last_time = db.slack_db.find({'channel': every_channel['id']}).sort(
            'ts', pymongo.DESCENDING).limit(1)
        for temp in last_time:
            temp2 = str(temp['ts'])
        getHistory(slack.groups, every_channel['id'], temp1)
        if (temp2) != connect_time:
            getHistory(slack.groups, every_channel['id'], connect_time, temp2)
        print "Inserted Private channel data"


def get_direct_channels_history(slack, connect_time):
    direct_channels = slack.im.list().body['ims']
    for counter in range(0, len(direct_channels)):
        # print direct_channels[counter]
        half_time = db.slack_db.find({'channel': direct_channels[counter]['id']}).sort(
            'ts', pymongo.ASCENDING).limit(1)
        temp1 = connect_time
        temp2 = connect_time
        for temp in half_time:
            temp1 = temp['ts']
        last_time = db.slack_db.find({'channel': direct_channels[counter]['id']}).sort(
            'ts', pymongo.DESCENDING).limit(1)
        for temp in last_time:
            temp2 = str(temp['ts'])
        getHistory(slack.im, direct_channels[counter]['id'], temp1)
        if temp2 != connect_time:
            getHistory(
                slack.im, direct_channels[counter]['id'], connect_time, temp2)
        print "Inserted direct channel data"
