import fitbit
import configparser
import json

import sys
import sched
import time
from datetime import datetime as dt
import datetime
import codecs
import urllib.request
import TimeManager
from twilio.rest import TwilioRestClient

def twilio_setup():
    """Set up the system's Twilio credentials."""
    parser = configparser.SafeConfigParser()
    parser.read('config.ini')
    user_id = parser.get('Twilio', 'TWIL_ACCOUNT_SID')
    user_token = parser.get('Twilio', 'TWIL_AUTH_TOKEN')
    twil_client = TwilioRestClient(user_id, user_token)
    return twil_client

def fitbit_setup():
    """Set up the user's Fitbit credentials."""
    parser = configparser.SafeConfigParser()
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
 
def step_alert(daily_time, scheduler, msg_type):
    """Start setting up a step count alert for the user."""
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    data = fitbit_client._COLLECTION_RESOURCE('activities', date=today)
    step_count = json.dumps(data["summary"]["steps"], indent=2)

    if msg_type == "near_day_end":
        t = dt.combine(dt.now() + datetime.timedelta(days=1), timings.near_day_end)
    elif msg_type == "day_end": 
        t = dt.combine(dt.now() + datetime.timedelta(days=1), timings.day_end)
    elif msg_type == "near_sunset":
        t = dt.combine(dt.now() + datetime.timedelta(days=1), timings.near_sunset)
    scheduler.enterabs(time.mktime(t.timetuple()), 1, step_alert, (daily_time, scheduler, msg_type))
    report_step_count(step_count, msg_type)
    timings.update_sunset_time()

def report_step_count(count, msg_type):
    """Text the current step count to the user."""
    parser = configparser.SafeConfigParser()
    parser.read('config.ini')
    target_phone = parser.get('Phone Numbers', 'TARGET_PHONE')
    twil_phone = parser.get('Phone Numbers', 'TWIL_PHONE')

    msg = ""
    if msg_type == "near_sunset":
        msg += "Sunset is in 1 hour! "
        msg_type = "near_day_end"
    if msg_type == "near_day_end":
        gap = 10000 - int(count)
        msg = msg + count + " steps taken today!"
        if gap > 0:
            msg += " " + str(gap) + " more steps to reach 10K!"
    elif msg_type == "day_end":
        weekday = dt.now().strftime("%A")
        msg = count + " was your final step total for " + weekday + "."
    print(msg)
    twil_client.messages.create(to=target_phone, from_=twil_phone, body=msg)

timings = TimeManager.TimeManager()
twil_client = twilio_setup()
fitbit_client = fitbit_setup()

def main():
    scheduler = sched.scheduler(time.time, time.sleep)
    
    timings.update_sunset_time()
    scheduler.enterabs(time.mktime(timings.near_day_end_time.timetuple()), 1, step_alert, (timings.near_day_end, scheduler, "near_day_end"))
    scheduler.enterabs(time.mktime(timings.day_end_time.timetuple()), 1, step_alert, (timings.day_end, scheduler, "day_end"))
    scheduler.enterabs(time.mktime(timings.near_sunset_time.timetuple()), 1, step_alert, (timings.day_end, scheduler, "near_sunset"))
    scheduler.run()

main()
