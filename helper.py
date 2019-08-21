# helper.py
# helper functions

import requests
import time
import json
import datetime
import sys

DEBUG = True

def dbprint(s):
	if DEBUG:
		print(s)

# returns true if 90% of features are 0
def is_empty(features):
	dbprint("checking for empty data:")
	filtered = list(filter(lambda x: x["properties"]["SmellValue"] > 0, features))
	dbprint(len(filtered))
	return len(filtered) == 0

# returns true if date1 to date2(epoch times) is a valid date range
def is_valid_date_range(date1, date2):
	try:
		date1 = int(date1)
		date2 = int(date2)
		epoch_to_est(date1)
		epoch_to_est(date2)
	except ValueError:
		return False

	if (date1 > date2):
		return False

	if (date2 > int(datetime.datetime.now().timestamp())):
		return False
	return True

# returns true if we have a smell value scale for that channel
def is_valid_channel(channel):
	valid_channels = ["PM025", "SO2", "SONICWD_DEG", "SONICWS_MPH", "wind"]
	return channel in valid_channels

# get json data from url
def request_url(url):
	#get data and coordinates
	dbprint("requesting " + url)
	resp = requests.get(url)
	if resp.status_code != 200:
		raise Exception("(error {} from {})".format(resp.status_code, url))
		return None
	return resp.json();

# convert sensor val to smell val
def get_smell_value(sensor_value, channel="PM025"):
	if (channel == "PM025"):
		scale = [12, 35.4, 55.4, 150.4]
	elif (channel == "VOC"):
		scale = [400, 600, 800, 1000]
	elif (channel == "SO2"):
		scale = [5,15,25,50]
	else:
		dbprint("no scale for " + channel)
		exit()

	if (sensor_value==None):
		return 0
	elif sensor_value < 0:
		return 0
	elif (sensor_value >= 0 and sensor_value <= scale[0]):
		return 1
	elif (sensor_value > scale[0] and sensor_value <= scale[1]):
		return 2
	elif (sensor_value > scale[1] and sensor_value <= scale[2]):
		return 3
	elif (sensor_value > scale[2] and sensor_value <= scale[3]):
		return 4
	else:
		return 5

# make geojson feature
# manually adding local time offset for clarity but maybe this should be changed in the future
def make_feature(lat, lon, e0, e1, smell_val):
	feature = {"type":"Feature",
		"geometry" : {"type" : "Point", "coordinates" : [lon,lat]},
		"properties": {
			"PackedColor":1000,
			"Size" : 15,
	        "StartEpochTime": e0,
	        "EndEpochTime": e1,
	        "GlyphIndex": smell_val,
	        "SmellValue": smell_val,
	        "DateTimeString": epoch_to_est(e0, "%m/%d/%Y %H:%M:%S") + " -04:00"
	        }
		}
	return feature

# given start and end date strings, returns list of strings for all dates in btwn (inclusive)
def get_date_range(start_date, end_date):
	start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
	end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
	date_generated = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days)]
	return [date.strftime("%Y-%m-%d") for date in date_generated]

# convert date (string) fromm YY-mm-dd EST to epoch time
def dt_to_epoch(date, format="%Y-%m-%d"):
	return int(datetime.datetime.strptime(date, format).timestamp())

# convert epoch (int or string) to YY-mm-dd EST(default)
def epoch_to_est(epoch, format="%Y-%m-%d"):
	return datetime.datetime.fromtimestamp(int(epoch)).strftime(format)

# epoch time to utc datetime
def epoch_to_utc(epoch, format="%Y-%m-%d"):
	return datetime.datetime.utcfromtimestamp(int(epoch)).strftime(format)

# get local timezone offset, for info only
def get_tz(epoch):
	d = datetime.datetime.fromtimestamp (epoch) - datetime.datetime.utcfromtimestamp (epoch)
	return (d.days*3600*24 - d.seconds) / 3600
