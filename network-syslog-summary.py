'''
 Script to summarise Cisco syslog and graph count over last retention period
 Output as follows:

switch.log-2019-07-17.gz's line count is 260459

Count of loglines per day over last 7 days is:
{'11-Jul': 406169, '12-Jul': 406169, '13-Jul': 300845, '14-Jul': 300845, '15-Jul': 229195, '16-Jul': 291950, '17-Jul': 260459}

Top 20 talkers are: (this bit is obfruscated)
('device_1 %MSG_A:', COUNT)
('device_2 %MSG_B:', COUNT)
etc

 Guy Morrell 2019-06
'''
import os
import fnmatch
import matplotlib.pyplot as plt
import numpy as np
import gzip
import datetime
import json
from datetime import date, timedelta

retention = 7
message_count = {}
line_count = 0
now = datetime.datetime.now()
today_ymd = "switch.log-"+now.strftime("%Y")+"-"+now.strftime("%m")+"-"+now.strftime("%d")+".gz"# YYYY-MM-DD
#today_renamed = today_ymd + "-processed"
with open("server.json", "rt") as server_f:
    credentials = json.load(server_f)
USERNAME = credentials["USERNAME"]
SERVER = credentials["SERVER"]
PATH = credentials["PATH"]
ARG = "scp " + USERNAME + "@" + SERVER + PATH + today_ymd+" ./"
update_hist = 'false'
today_d = date.today()
today_s = today_d.strftime("%d-%b")
oldest_d = today_d - timedelta(days = retention)
oldest_s = oldest_d.strftime("%d-%b")
'''
Copy today's log from the syslog server
Name format for yesterday's log is switch.log-YYYY-MM-DD.gz, where DD = today, as the rotation happens at 06:00
Need to cope with the script running multiple times in one day and should delete old logfiles
'''
if not os.path.exists(today_ymd):
    print("Copying file")
    os.system(ARG) # copy yesterday's file to the local folder
    update_hist = 'true'
with gzip.open(today_ymd, mode='rt') as f:
    log = f.readlines()
# delete any filenames starting switch.log except today's
for filename in os.listdir():
    if fnmatch.fnmatch(filename, 'switch.log*'):
        if not fnmatch.fnmatch(filename, today_ymd):
            os.remove(filename)
# Count unique messaage_id / name combined messages and store in message_count dict
for line in log:
    line_count += 1
    # Grab the unique message id, e.g. %DOT1X-5-FAIL:
    message_id = line.strip().split()[9]
    # Grab the name or IP of the device
    device_id = line.strip().split()[3]
    # Combine for easy counting
    device_message = device_id + " " + message_id
    if device_message not in message_count:
        message_count[device_message] = 1
    else:
        count = message_count[device_message]
        count += 1
        message_count[device_message] = count
print(today_ymd+"'s line count is "+str(line_count))
# Read the old history file
if os.path.exists("history.json"):
    with open("history.json", "rt") as history_f:
         history = json.load(history_f)
    print("Count of loglines per day over last "+str(retention)+" days is:")
    print(history)
else:
    print("No history file found.")
if update_hist == 'true':  # if script run multiple times in 24hr period, don't overwrite history data
    print("Updating history data")
    # get rid of the oldest entry if exists
    if oldest_s in history:
        (history.pop(oldest_s))
    else:
        print("No data for "+oldest_s+" in history")
    # add today's count
    history[today_s] = line_count
    # Re-write history
    with open('history.json', 'w') as outfile:
        json.dump(history, outfile)

# Plot a graph of the last 7 days' data
pos = 0
x_axis = []
y_axis = []
for date in history:
    x_axis.insert(pos, date)
    y_axis.insert(pos, history[date])
    pos += 1
plt.xlabel('Date')
plt.ylabel('Log Count')
np_history = np.array(y_axis, dtype=np.int64)
plt.title('Syslog Message Count over time')
plt.plot(x_axis, np_history)
plt.show()

# Print the top 20 messages by device
sorted_mc = sorted(message_count.items(), key=lambda x: x[1], reverse=1)
count = 20
print("Top "+str(count)+" talkers are: ")
for i in sorted_mc:
    if count > 0:
        print(i)
    count -= 1