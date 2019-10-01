import os
import time
from slackclient import SlackClient
import psycopg2


#id and token
keyfile = open('key.txt','r')
key = keyfile.read()
key = key.split()
# starterbot's ID as an environment variable
BOT_ID = key[0]

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate Slack & Twilio clients
slack_client = SlackClient(key[1])

#connection to the database
conn = psycopg2.connect(dbname='digest', user='test_user', 
                        password='qwerty', host='localhost')
try:
	cursor = conn.cursor()
	cursor.execute('''CREATE TABLE messages(channel VARCHAR (20),
										client_msg_id VARCHAR (20),
										event_ts VARCHAR (20),
										source_team VARCHAR (20),
										suppress_notification VARCHAR (20),
										team VARCHAR (20),
										ts VARCHAR (20),
										type VARCHAR (20),
										username VARCHAR (20),
										user_team VARCHAR (20));''')
	cursor.close()
except Exception as e:
	print(e)

def incert():
	cursor = conn.cursor()
	conn.execute('INSERT INTO messages (channel, client_msg_id, event_ts, source_team, suppress_notification, team, ts, type, username, user_team) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)' % (output['channel'], output['client_msg_id'], output['event_ts'], output['source_team'], output['suppress_notification'], output['team'], output['ts'], output['type'], output['username'], output['user_team']))
	cursor.close()

'''
def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)
'''

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output: #and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                incert()
    return None, None
 
if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")