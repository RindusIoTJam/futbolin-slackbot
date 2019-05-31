import json
import time
import re
import ssl

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
DEQUE_COUPLE_REGEX = '^\-.*<@(|[WU].+?)>.*<@(|[WU].+?)>.*'

def on_message(client, userdata, message):
  print("received message =", str(message.payload.decode("utf-8")))

def on_log(client, userdata, level, buf):
  print("log: ",buf)

def on_connect(client, userdata, flags, rc):
  print("connected ")

client=paho.Client()
client.on_message=on_message
client.on_log=on_log
client.on_connect=on_connect

client.tls_set_context(context=None)
client.tls_insecure_set(True)
client.username_pw_set(config.get('mqtt.username'), config.get('mqtt.password'))
client.connect("mqtt.rindus.es", 8883, 60)

##start loop to process received messages
client.loop_start()

def handle_events(slack_events):
    for event in slack_events:

        if event["type"] == "message" and not "subtype" in event:
            print(event["text"])
            matches = re.search(QUEUE_COUPLE_REGEX, event["text"])
            if matches and (matches.group(1) == matches.group(2)):
                slack_client.api_call("chat.postMessage", channel=event["channel"],
                                      text="You cannot clone yourself to build a couple!")
            else:
                if matches and (matches.group(1) != matches.group(2)):
                    player_one = slack_client.api_call("users.info", user=matches.group(1))['user']['profile']['display_name']
                    player_two = slack_client.api_call("users.info", user=matches.group(2))['user']['profile']['display_name']
                    client.publish("rindus/futbolin", "+" + player_one + "/" + player_two)
                    slack_client.api_call("chat.postMessage", channel=event["channel"],
                                                              text="Added " + player_one + " & " + player_two + "to the queue.")

                matches = re.search(DEQUE_COUPLE_REGEX, event["text"])
                if matches:
                    player_one = slack_client.api_call("users.info", user=matches.group(1))['user']['profile']['display_name']
                    player_two = slack_client.api_call("users.info", user=matches.group(2))['user']['profile']['display_name']
                    client.publish("rindus/futbolin", "+" + player_one + "/" + player_two)
                    slack_client.api_call("chat.postMessage", channel=event["channel"],
                                                              text="Removed " + player_one + " & " + player_two + "to the queue.")


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
        print("Connection failed. Exception traceback printed above.")
