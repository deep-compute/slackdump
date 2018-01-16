import slack_dump
from basescript import BaseScript

class Slack_Command(BaseScript):
    DESC = 'Reads event messages in real-time from a Slack workplace'

    def run(self):
        slack_dump.initialise(self.args.auth_token)

    def define_args(self,parser):
        parser.add_argument('auth_token', metavar = 'auth-token')

def main():
    Slack_Command().start()

if __name__ == '__main__':
    main()
