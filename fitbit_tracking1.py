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
 
def step_alert(fitbit_client, twil_client, daily_time, scheduler):
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    data = fitbit_client._COLLECTION_RESOURCE('activities', date=today)
    step_count = json.dumps(data["summary"]["steps"], indent=2)

    t = dt.combine(dt.now() + datetime.timedelta(days=1), daily_time)
    scheduler.enterabs(time.mktime(t.timetuple()), 1, step_alert, (fitbit_client, twil_client, daily_time, scheduler))
    report_step_count(step_count, twil_client)

def report_step_count(count, twil_client):
    parser = ConfigParser.SafeConfigParser()
    parser.read('config.ini')
    target_phone = parser.get('Phone Numbers', 'TARGET_PHONE')
    twil_phone = parser.get('Phone Numbers', 'TWIL_PHONE')

    gap = 10000 - int(count)
    msg = "Today you've taken " + count + " steps. Only " + str(gap) + " more steps to reach 10K!"
    twil_client.messages.create(to=target_phone, from_=twil_phone, body=msg)

def main():
    twil_client = twilio_setup()
    fitbit_client = fitbit_setup()
    daily_time = datetime.time(23) # 11 p.m.
    scheduler = sched.scheduler(time.time, time.sleep)

    first_time = dt.combine(dt.now(), daily_time)
    scheduler.enterabs(time.mktime(first_time.timetuple()), 1, step_alert, (fitbit_client, twil_client, daily_time, scheduler))
    scheduler.run()

main()
