import os
from os.path import expanduser

from basescript import BaseScript

import util
from .slackdump import SlackDump
from .messagestore import *

class SlackCommand(BaseScript):
    DESC = "A tool to get the data from slack and store it in mongodb"

    def _parse_msg_target_arg(self, t):
        path, args = t.split(':', 1)
        path = path.split('=')[1]
        args = dict(a.split('=', 1) for a in args.split(':'))
        args['log'] = self.log

        return path, args

    def msg_store(self):
        targets = []

        for t in self.args.target:
            #import pdb; pdb.set_trace()
            imp_path, args = self._parse_msg_target_arg(t)
            target_class = util.load_object(imp_path)
            target_obj = target_class(**args)
            targets.append(target_obj)

        return targets

    def run(self):
        targets = self.msg_store()
        #import pdb;pdb.set_trace()
        s = SlackDump(auth_token=self.args.auth_token,
                      file_path=self.args.image_folder,
                      status_path=self.args.status_path,
                      targets=targets, log=self.log)
        s.start()

    def define_args(self, parser):
        parser.add_argument('-a', '--auth_token', metavar='auth_token',
                            help='The legacy token of slack')
        parser.add_argument('-status_path', '--status_path', metavar='status_path',
                            help='File path where the status of slack messages needs to be stored.')
        parser.add_argument('-image_folder', '--image_folder',
                            help='Path of the folder where the images needs to be stored.')
        parser.add_argument('-target', '--target', nargs='+',
                help='format for Mongo: store=<MongoStore-classpath>:db_name=<database-name>:collection_name=<collection-name> \
                      format for SQLite: store=<SQLiteStore-classpath>:host=<hostname>:port=<port-number>:db_name=<db-name>:table_name=<table-name>" \
                      format for NSQ: store=<NsqStore-classpath>:host=<hostname>:port=<port-number>:topic=<topic-name> \
                      format for file: store=<FileStore-classpath>:file_path=<file-path>')

def main():
    SlackCommand().start()
