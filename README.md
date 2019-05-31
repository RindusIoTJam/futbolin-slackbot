# futbolin-slackbot

## Mission Statement

Create a chat based tool to register for out kicker matches.

## Installation

Prerequisites

- python
- virtualenv 

```
git clone https://github.com/RindusIoTJam/slackbot.git
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Runtime

```
source slackbot/bin/activate
python app.py
```

Set all properties in the config file `local_settings.json` 
in the repository top directory with the content

```
{
  "slackbot.token": "xoxo-398954462386-sRsuiJAN645vtkGxozNbkeVe",

  "mqtt.hostname": "mqtt.rindus.es",
  "mqtt.port":     8883,
  "mqtt.secure":   "True",

  "mqtt.username": "futbolin",
  "mqtt.password": "TopfSekreet",
  "mqtt.topic": "rindus/test/futbolin"
}
```
