import fitbit
import ConfigParser
import json

import sys
import sched
import time
from datetime import datetime as dt
import datetime
import codecs
from twilio.rest import TwilioRestClient

def twilio_setup():
    parser = ConfigParser.SafeConfigParser()
    parser.read('config.ini')
    user_id = parser.get('Twilio', 'TWIL_ACCOUNT_SID')
    user_token = parser.get('Twilio', 'TWIL_AUTH_TOKEN')
    twil_client = TwilioRestClient(user_id, user_token)
    return twil_client

def fitbit_setup():
    parser = ConfigParser.SafeConfigParser()
    parser.read('config.ini')
    client_key = parser.get('Fitbit', 'CLIENT_KEY')
    client_secret = parser.get('Fitbit', 'CLIENT_SECRET')
     
    # Set up an unauthorized client
    unauth_client = fitbit.Fitbit(client_key, client_secret)

    # Get data for the user
    user_key = parser.get('Fitbit', 'USER_KEY')
    user_secret = parser.get('Fitbit', 'USER_SECRET')

    # Set up the client object
    client = fitbit.Fitbit(client_key, client_secret, resource_owner_key=user_key, resource_owner_secret=user_secret)
    return client 
 
def step_alert(fitbit_client, twil_client, daily_time, scheduler, msg_type):
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    data = fitbit_client._COLLECTION_RESOURCE('activities', date=today)
    step_count = json.dumps(data["summary"]["steps"], indent=2)

    if msg_type == "near_day_end":
        t = dt.combine(dt.now() + datetime.timedelta(days=1), near_day_end)
    elif msg_type == "day_end": 
        t = dt.combine(dt.now() + datetime.timedelta(days=1), day_end)
    scheduler.enterabs(time.mktime(t.timetuple()), 1, step_alert, (fitbit_client, twil_client, daily_time, scheduler, msg_type))
    report_step_count(step_count, twil_client, msg_type)

def report_step_count(count, twil_client, msg_type):
    parser = ConfigParser.SafeConfigParser()
    parser.read('config.ini')
    target_phone = parser.get('Phone Numbers', 'TARGET_PHONE')
    twil_phone = parser.get('Phone Numbers', 'TWIL_PHONE')

    if msg_type == "near_day_end":
        gap = 10000 - int(count)
        msg = "Today you've taken " + count + " steps. Only " + str(gap) + " more steps to reach 10K!"
    elif msg_type == "day_end":
        msg = "Your step count for today was " + count + " steps."
    twil_client.messages.create(to=target_phone, from_=twil_phone, body=msg)

def main():
    twil_client = twilio_setup()
    fitbit_client = fitbit_setup()
    near_day_end = datetime.time(23) # 11 p.m.
    day_end = datetime.time(23, 59) # 11:59 p.m.
    scheduler = sched.scheduler(time.time, time.sleep)

    near_day_end_time = dt.combine(dt.now(), near_day_end)
    day_end_time = dt.combine(dt.now(), day_end)
    scheduler.enterabs(time.mktime(near_day_end_time.timetuple()), 1, step_alert, (fitbit_client, twil_client, near_day_end, scheduler, "near_day_end"))
    scheduler.enterabs(time.mktime(day_end_time.timetuple()), 1, step_alert, (fitbit_client, twil_client, day_end, scheduler, "day_end"))
    scheduler.run()

main()
