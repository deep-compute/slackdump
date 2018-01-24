import time
from slackhistory import SlackHistory


obj = SlackHistory(
    auth_token="xoxp-297136158787-296584015872-298342155223-29a08d7da680e45888e875e13035dce4", connect_time=time.time())
obj.start()
