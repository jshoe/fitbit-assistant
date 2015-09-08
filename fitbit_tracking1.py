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
 
def step_alert(fitbit_client, twil_client, daily_time, scheduler, msg_type):
    """Start setting up a step count alert for the user."""
    now = datetime.datetime.now()
    today = now.strftime("%Y-%m-%d")
    data = fitbit_client._COLLECTION_RESOURCE('activities', date=today)
    step_count = json.dumps(data["summary"]["steps"], indent=2)

    if msg_type == "near_day_end":
        t = dt.combine(dt.now() + datetime.timedelta(days=1), near_day_end)
    elif msg_type == "day_end": 
        t = dt.combine(dt.now() + datetime.timedelta(days=1), day_end)
    elif msg_type == "near_sunset":
        t = dt.combine(dt.now() + datetime.timedelta(days=1), near_sunset)
    scheduler.enterabs(time.mktime(t.timetuple()), 1, step_alert, (fitbit_client, twil_client, daily_time, scheduler, msg_type))
    report_step_count(step_count, twil_client, msg_type)
    update_sunset_time()

def update_sunset_time():
    """Update the next sunset time."""
    utf_decoder = codecs.getreader("utf-8")
    query = 'http://api.sunrise-sunset.org/json?lat=37.863946&lng=-122.267158'
    api_response = urllib.request.urlopen(query)
    sunset = json.load(utf_decoder(api_response))['results']['sunset']
    #print("New sunset time in UTC is " + sunset + ".")
    sunset = dt.strptime(sunset, "%H:%M:%S %p")
    sunset = sunset - datetime.timedelta(hours=7)
    hour = int(sunset.strftime("%H")) - 1 # Set to hour before sunset
    minute = int(sunset.strftime("%M"))
    near_sunset = datetime.time(hour, minute)

def report_step_count(count, twil_client, msg_type):
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
    twil_client.messages.create(to=target_phone, from_=twil_phone, body=msg)

near_day_end = datetime.time(23) # 11 p.m.
day_end = datetime.time(23, 59) # 11:59 p.m.
near_sunset = datetime.time(18, 41) # 6:41 p.m. as seed value

def main():
    twil_client = twilio_setup()
    fitbit_client = fitbit_setup()
    scheduler = sched.scheduler(time.time, time.sleep)

    near_day_end_time = dt.combine(dt.now(), near_day_end)
    day_end_time = dt.combine(dt.now(), day_end)
    near_sunset_time = dt.combine(dt.now(), near_sunset)
    scheduler.enterabs(time.mktime(near_day_end_time.timetuple()), 1, step_alert, (fitbit_client, twil_client, near_day_end, scheduler, "near_day_end"))
    scheduler.enterabs(time.mktime(day_end_time.timetuple()), 1, step_alert, (fitbit_client, twil_client, day_end, scheduler, "day_end"))
    scheduler.enterabs(time.mktime(near_sunset_time.timetuple()), 1, step_alert, (fitbit_client, twil_client, day_end, scheduler, "near_sunset"))
    scheduler.run()

main()
