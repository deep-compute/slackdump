import os
from os.path import expanduser

from basescript import BaseScript
from .slackdump import SlackDump
from .messagestore import MessageStore
from .nsqstore import NsqStore


class SlackCommand(BaseScript):
    DESC = "A tool to get the data from slack and store it in mongodb"

    def get_file_path(self, file_path):
        if not file_path:
            file_path = expanduser("~") + "/slack_files/"
            if not os.path.exists(file_path):
                os.makedirs(file_path)

        return file_path

    def run(self):
        file_path = self.get_file_path(self.args.file_path)

        if self.args.nsq_store:
            nsq_obj = NsqStore(topic=self.args.topic_name,
                               host=self.args.nsq_host,
                               port=self.args.nsq_port,
                               log=self.log)
        else:
            nsq_obj = None

        store = MessageStore(db_name=self.args.db_name,
                             collection_name=self.args.c_name,
                             nsq_obj=nsq_obj, log=self.log)
        s = SlackDump(auth_token=self.args.auth_token,
                      file_path=file_path, store=store, log=self.log)
        s.start()

    def define_args(self, parser):
        parser.add_argument('-a', '--auth_token', metavar='auth_token',
                            help='The legacy token of slack')
        parser.add_argument('-f', '--file_path', metavar='file_path',
                            nargs='?', default=None,
                            help='The path of the directory where you\
                            want to save slack attachments')

        #database arguments
        parser.add_argument('-d', '--db_name',
                            metavar='database_name', nargs='?',
                            default='slackdb',
                            help='Database where you want to store messages')
        parser.add_argument('-c', '--c_name', metavar='collection_name',
                            nargs='?', default='slackdb',
                            help='Collection where you want to store messages')

        #nsq arguments
        parser.add_argument('-store', '--nsq_store', metavar='nsq_store',
                            nargs='?', default=False,
                            help='Activate nsq store to store messages')
        parser.add_argument('-t', '--topic_name', metavar='topic_name',
                            nargs='?', default='slackmessage',
                            help='nsq topic name')
        parser.add_argument('-nh', '--nsq_host', metavar='nsq_host',
                            nargs='?', default='localhost',
                            help='nsq host where nsq is running')
        parser.add_argument('-np', '--nsq_port', metavar='nsq_port',
                            nargs='?', default=4151,
                            help='port at which nsq is running', type=int)


def main():
    SlackCommand().start()
