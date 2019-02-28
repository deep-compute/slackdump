import hashlib

from pymongo import MongoClient, ASCENDING, DESCENDING
from deeputil import Dummy

DUMMY_LOG = Dummy


class MessageStore(object):
    def __init__(self, db_name, collection_name,
                 nsq_obj=None, log=DUMMY_LOG):
        self.nsq_obj = nsq_obj
        self.db_name = db_name
        self.collection_name = collection_name
        self.log = log
        self.client = MongoClient()
        self.db = self.client[self.db_name][self.collection_name]

    def insert_into_db(self, msg):
        # For some cases where timestamp is not present in message
        try:
            #import pdb;pdb.set_trace()
            key = self.get_key(msg.channel, msg.ts)
            msg.key = key
            if self.nsq_obj:
                self.nsq_obj.store_in_nsq(dict(msg))
            self.db.insert(dict(msg))
            self.log.info("inserted_into_db", _key=msg.key, user=msg.user_name,
                            channel=msg.channel_name, ts=float(msg.ts), num_msg=1, type='metric')
        except KeyError:
            self.log.info("inserted_into_db", _key=msg.key,
                            channel=msg.channel_name, ts=float(msg.ts), num_msg=1, type='metric')
        except Exception as e:
            self.log.exception(e)
            return False

    def get_key(self, channel, timestamp):
        return hashlib.sha1((channel + timestamp).encode('utf8')).hexdigest()

    def get_latest_timestamp(self, channel_id):
        ts = [one_record['ts'] for one_record in self.db.find({'channel': channel_id}).sort('ts', DESCENDING).limit(1)]
        return ts

    def get_oldest_timestamp(self, channel_id):
        ts = [one_record['ts'] for one_record in self.db.find({'channel': channel_id}).sort('ts', ASCENDING).limit(1)]
        return ts
