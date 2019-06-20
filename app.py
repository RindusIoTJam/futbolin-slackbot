import json
import time
import re
import sys

# 3rd party
import paho.mqtt.client as paho

from slackclient import SlackClient

config = None

with open('local_settings.json', 'r') as settings_file:
    config = json.load(settings_file)

slack_client = SlackClient(config.get('slackbot.token'))

# 1 second delay between reading from RTM
RTM_READ_DELAY = 1
QUEUE_COUPLE_REGEX = '^\+.*<@(|[WU].+?)>.*<@(|[WU].+?)>.*'
DEQUE_COUPLE_REGEX = '^-.*<@(|[WU].+?)>.*<@(|[WU].+?)>.*'


def on_message(client, userdata, message):
    #print("received message =", message.payload)

    if message.payload.startswith('++'):
        print("MQTT: Queued confirmation response.")
        channels = slack_client.api_call('channels.list', exclude_archived=True, exclude_members=True).get('channels')
        for channel in channels:
            if channel.get('is_member'):
                # print(channel.get('id'), channel.get('name_normalized'))
                # slack_client.api_call("chat.postMessage", channel='CFZA33VSB',
                slack_client.api_call("chat.postMessage", channel=channel.get('id'),
                                      text="Added " + message.payload[2:] + " to the futbolin queue.")

    if message.payload.startswith('--'):
        print("MQTT: Dequeued confirmation response.")
        channels = slack_client.api_call('channels.list', exclude_archived=True, exclude_members=True).get('channels')
        for channel in channels:
            if channel.get('is_member'):
                # slack_client.api_call("chat.postMessage", channel='CFZA33VSB',
                slack_client.api_call("chat.postMessage", channel=channel.get('id'),
                                      text="Removed " + message.payload[2:] + " from the futbolin queue.")

    if message.payload == 'qq':
        print("MQTT: Queue list response.")
        channels = slack_client.api_call('channels.list', exclude_archived=True, exclude_members=True).get('channels')
        for channel in channels:
            if channel.get('is_member'):
                # slack_client.api_call("chat.postMessage", channel='CFZA33VSB',
                slack_client.api_call("chat.postMessage", channel=channel.get('id'),
                                      text="List current queue not implemented yet")

    if message.payload == 'ss':
        print("MQTT: Statistic response.")
        channels = slack_client.api_call('channels.list', exclude_archived=True, exclude_members=True).get('channels')
        for channel in channels:
            if channel.get('is_member'):
                # slack_client.api_call("chat.postMessage", channel='CFZA33VSB',
                slack_client.api_call("chat.postMessage", channel=channel.get('id'),
                                      text="Show statistic not implemented yet")


# def on_log(client, userdata, level, buf):
#     print("log: ",buf)


def on_connect(client, userdata, flags, rc):
    print("MQTT: connected ")
    client.subscribe(config.get('mqtt.topic'))


client = paho.Client()

client.on_message=on_message
# client.on_log = on_log
client.on_connect = on_connect
# client.on_message = lambda *args: None
client.on_log = lambda *args: None
# client.on_connect = lambda *args: None

if config.get('mqtt.secure'):
    client.tls_set_context(context=None)
    client.tls_insecure_set(True)

client.username_pw_set(config.get('mqtt.username'), config.get('mqtt.password'))
client.connect(config.get('mqtt.hostname'), int(config.get('mqtt.port')), 60)

# start loop to process received messages
client.loop_start()


def handle_events(slack_events):
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:

            # QUEUE COUPLE
            matches = re.search(QUEUE_COUPLE_REGEX, event["text"])
            if matches:
                print("SLACK: Queue request from " + event["user"])
                player_one = slack_client.api_call("users.info", user=matches.group(1))
                player_two = slack_client.api_call("users.info", user=matches.group(2))

                if event["user"] not in (matches.group(1), matches.group(2)):
                    slack_client.api_call("chat.postMessage", channel=event["channel"],
                                          text="You have to be part of the couple!")
                elif matches.group(1) == matches.group(2):
                    slack_client.api_call("chat.postMessage", channel=event["channel"],
                                          text="You cannot clone yourself to build a couple!")

                elif player_one['user']['is_bot'] or player_two['user']['is_bot']:
                    slack_client.api_call("chat.postMessage", channel=event["channel"],
                                          text="You cannot play with a bot, stupid!")
                else:
                    client.publish(config.get('mqtt.topic'), "+" + player_one['user']['profile']['real_name'] +
                                   "/" + player_two['user']['profile']['real_name'])

            # DEQUEUE COUPLE
            matches = re.search(DEQUE_COUPLE_REGEX, event["text"])
            if matches:
                print("SLACK: Dequeue request from " + event["user"])

                player_one = slack_client.api_call("users.info", user=matches.group(1))
                player_two = slack_client.api_call("users.info", user=matches.group(2))

                if event["user"] not in (matches.group(1), matches.group(2)):
                    slack_client.api_call("chat.postMessage", channel=event["channel"],
                                          text="You cannot unqueue a foreign couple!")
                elif matches.group(1) == matches.group(2) or player_one['user']['is_bot'] or player_two['user']['is_bot']:
                    slack_client.api_call("chat.postMessage", channel=event["channel"],
                                          text="Never ever would have accepted that to be queued!")
                else:
                    client.publish(config.get('mqtt.topic'), "-" + player_one['user']['profile']['real_name'] +
                                   "/" + player_two['user']['profile']['real_name'])

            # REQUEST QUEUE
            if event["text"] == '?q':
                print("SLACK: List queue request from " + event["user"])
                client.publish(config.get('mqtt.topic'), "q")

            # REQUEST STATISTIC
            if event["text"] == '?s':
                print("SLACK: List statistic request from " + event["user"])
                client.publish(config.get('mqtt.topic'), "s")


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        try:
            while True:
                handle_events(slack_client.rtm_read())
                time.sleep(RTM_READ_DELAY)
        except (KeyboardInterrupt, SystemExit), e:
            sys.exit(" ... exiting")

    else:
        print("Connection to SLACK failed. Exception traceback printed above.")
