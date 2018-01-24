from basescript import BaseScript
from .slackdump import SlackDump

class SlackCommand(BaseScript):
    DESC = "A tool to get the data from slack and store it in mongodb"

    def run(self):
        slackdump_obj = SlackDump(auth_token=self.args.auth_token)
        slackdump_obj.start()

    def define_args(self, parser):
        parser.add_argument('auth_token', metavar='auth-token')

def main():
    SlackCommand().start()
