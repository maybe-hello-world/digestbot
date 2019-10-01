import os
import slack

client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])

channels = client.channels_list()
print(channels)