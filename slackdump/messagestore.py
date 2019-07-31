import hashlib

from deeputil import Dummy
from diskdict import DiskDict

DUMMY_LOG = Dummy

import sqlite3
import json


class SQLiteStore(object):
    def __init__(self, db_name="slackdb", table_name="messages", log=DUMMY_LOG):
        self.db_name = db_name
        self.table_name = table_name
        self.log = log

        self.con = sqlite3.connect(
            db_name, check_same_thread=False, isolation_level=None
        )
        self.db = self.con.cursor()
        self.db.execute(
            "CREATE TABLE if not exists '%s' (key text, message text)"
            % (self.table_name)
        )

    def insert_msg(self, record):
        try:
            t_name = self.table_name
            srecord = json.dumps(record)
            self.db.execute(
                "INSERT INTO {t} VALUES (?, ?)".format(t=t_name),
                (record["key"], srecord),
            )

            self.log.info(
                "inserted_into_sqlite",
                key=record["key"],
                channel=record["channel_name"],
                user=record["user_name"],
                ts=float(record["ts"]),
            )
        except KeyError:
            self.log.info(
                "inserted_into_sqlite",
                key=record["key"],
                channel=record["channel_name"],
                ts=float(record["ts"]),
            )
        except Exception as e:
            self.log.exception(e)


class FileStore(object):
    def __init__(self, file_path=None):
        self.p = file_path

    def insert_msg(self, msg):
        with open(self.p, "a") as _file:
            _file.write(msg)


import gnsq


class NsqStore(object):
    def __init__(self, topic, host="localhost", port="4151", log=DUMMY_LOG):
        self.topic = topic
        self.log = log
        self.host = host
        self.http_port = port
        self.connection = gnsq.Nsqd(address=self.host, http_port=self.http_port)

    def insert_msg(self, record):
        try:
            self.connection.publish(self.topic, str(record))
            self.log.info(
                "inserted_into_nsq",
                key=record["key"],
                channel=record["channel_name"],
                user=record["user_name"],
                ts=float(record["ts"]),
            )
        except KeyError:
            self.log.info(
                "inserted_into_nsq",
                key=record["key"],
                channel=record["channel_name"],
                ts=float(record["ts"]),
            )
        except Exception as e:
            self.log.exception(e)


from pymongo import MongoClient, ASCENDING, DESCENDING


class MongoStore(object):
    def __init__(self, db_name, collection_name, log=DUMMY_LOG):
        self.db_name = db_name
        self.collection_name = collection_name
        self.log = log
        self.client = MongoClient()
        self.db = self.client[self.db_name][self.collection_name]

    def insert_msg(self, msg):
        # For some cases where timestamp is not present in message
        try:
            self.db.insert_one(msg)
            self.log.info(
                "inserted_into_db",
                _key=msg["key"],
                user=msg["user_name"],
                channel=msg["channel_name"],
                ts=float(msg["ts"]),
                num_msg=1,
                type="metric",
            )
        except KeyError:
            self.log.info(
                "inserted_into_db",
                _key=msg["key"],
                channel=msg["channel_name"],
                ts=float(msg["ts"]),
                num_msg=1,
                type="metric",
            )
        except Exception as e:
            self.log.exception(e)
            return False
