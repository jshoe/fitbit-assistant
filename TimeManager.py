import datetime
import json
import codecs
import urllib.request
from datetime import datetime as dt

class TimeManager:
    near_sunset = datetime.time(18, 41) # 6:41 p.m. as seed value
    near_sunset_time = dt.combine(dt.now(), near_sunset)
    near_day_end = datetime.time(23) # 11 p.m.
    near_day_end_time = dt.combine(dt.now(), near_day_end)
    day_end = datetime.time(23, 59) # 11:59 p.m.
    day_end_time = dt.combine(dt.now(), day_end)

    def update_sunset_time(self):
        """Update the next sunset time."""
        utf_decoder = codecs.getreader("utf-8")
        query = 'http://api.sunrise-sunset.org/json?lat=37.863946&lng=-122.267158'
        api_response = urllib.request.urlopen(query)
        sunset = json.load(utf_decoder(api_response))['results']['sunset']
        print("New sunset time in UTC is " + sunset + ".")
        sunset = dt.strptime(sunset, "%H:%M:%S %p")
        sunset = sunset - datetime.timedelta(hours=7)
        hour = int(sunset.strftime("%H")) - 1 # Set to hour before sunset
        minute = int(sunset.strftime("%M"))
        self.near_sunset = datetime.time(hour, minute)
        self.near_sunset_time = dt.combine(dt.now(), self.near_sunset)