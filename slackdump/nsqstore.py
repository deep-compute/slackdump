import gnsq

from deeputil import Dummy, AttrDict

DUMMY_LOG = Dummy

class NsqStore(object):
    def __init__(self, topic, host, port, log=DUMMY_LOG):
        self.topic = topic
        self.log = log
        self.host = host
        self.http_port = port
        self.connection = gnsq.Nsqd(address=self.host, http_port=self.http_port)

    def store_in_nsq(self, record):
        try:
            #import pdb;pdb.set_trace()
            self.connection.publish(self.topic, str(record))
            record = AttrDict(record)
            self.log.info("inserted_into_nsq", key=record.key, channel=record.channel_name, user=record.user_name, ts=float(record.ts))
        except KeyError:
            self.log.info("inserted_into_nsq", key=record.key, channel=record.channel_name, ts=float(record.ts))
        except Exception as e:
            self.log.exception(e)
            return False
