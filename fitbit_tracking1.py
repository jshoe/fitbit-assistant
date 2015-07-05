import fitbit
import ConfigParser
import json
import datetime
 
# Load Fitbit settings
parser = ConfigParser.SafeConfigParser()
parser.read('config.ini')
client_key = parser.get('Login Parameters', 'CLIENT_KEY')
client_secret = parser.get('Login Parameters', 'CLIENT_SECRET')
 
# Set up an unauthorized client
unauth_client = fitbit.Fitbit(client_key, client_secret)

# Get data for the user
user_key = parser.get('Login Parameters', 'USER_KEY')
user_secret = parser.get('Login Parameters', 'USER_SECRET')

# Set up the client object
authd_client = fitbit.Fitbit(client_key, client_secret, resource_owner_key=user_key, resource_owner_secret=user_secret)
 
# Start collecting your desired data
now = datetime.datetime.now()
today = now.strftime("%Y-%m-%d")
data = authd_client._COLLECTION_RESOURCE('activities', date=today)
print json.dumps(data["summary"]["steps"], indent=2)

def time_check():
    now = datetime.datetime.now().strftime("%H:%M")
    if now == '23:30':
        msg = 'Your step summary for the day.'

time_check()
