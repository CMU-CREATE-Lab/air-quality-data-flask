# process_sensor_data.py
# process direct calls to esdr as well as aggregates
# returns json as string, doesn't output
# only works for SO2 and PM025 rn(no other scale)

from helper import *

# for one day, generate array of "features" for geojson
# given sensor_data json, start_epoch for day, channel
# (aggregates)
def process_day(sensor_data, start_epoch, channel):
	features = []
	sums = [0,0,0,0,0,0]

	# each row 98 elem long, 96 sensor vals
	for sensor in sensor_data:
		lat = sensor[0]
		lon = sensor[1]
		for i in range(0,len(sensor)-2):
			val = sensor[2+i]
			e0 = start_epoch + i*900
			e1 = e0 + 900

			smell_val = get_smell_value(val, channel)
			sums[smell_val] += 1

			feature = make_feature(lat,lon, e0, e1, smell_val)
			features.append(feature)

	dbprint("smell val sums = " + str(sums))
	return features


# get feed id from api request
def get_id(api_request):
	start = api_request.find("/feeds") + len("/feeds/")
	end = api_request.find("/channels")
	return api_request[start:end]

# get latitude and longitude by making new api request
# for pm25 achd and wind
def get_latlong(api_request):
	# that one sensor
	if (get_id(api_request) == "11067"):
		x = api_request.find("/feeds") + len("/feeds/")
		new_request = api_request[0:x] + "43"
	else:
		new_request = api_request[0:api_request.find("/channels")]
	resp = requests.get(new_request)
	if resp.status_code != 200:
		raise Exception('error {} getting latlong from {}'.format(resp.status_code, new_request))
	return [resp.json()['data']['latitude'], resp.json()['data']['longitude']]

# process pm25 channels from direct esdr calls
def process_pm25_achd(start_date, end_date):
	# find indexes of channels w keyword
	def find_indexes(keyword, channels):
		ret = []
		for i in range(0,len(channels)):
			if channels[i].lower().find(keyword) >= 0:
				ret += [i+1]
		return ret

	# takes column indexes to merge and orig data, returns merged data w 2 columns
	# know there's > 1 column
	def merge_data(cols, data):
		def merge_cols(row):
			#remove None
			for i in range(0,len(row)):
				if row[i] == None:
					row[i] = -1

			max_val = max([row[c] for c in cols])
			return [row[0], max_val]

		num_cols = len(cols)
		merged = list(map(merge_cols, data))
		return merged

	def process_request(api_request):
		resp_json = request_url(api_request)
		channel_names = resp_json['channel_names']
		data = resp_json['data']

		dbprint("requesting lat long")
		coord = get_latlong(api_request)
		if (coord[0] == None or coord[1] == None):
			dbprint("bad coords")
			return []

		#filter out channels we don't want
		if (len(channel_names) > 1):
			indexes = find_indexes('pm25',channel_names)
			if len(indexes) == 0 :
				dbprint("no pm25 channels")
				return []
			else:
				data = merge_data(indexes,data)

		# create geojson features
		# maybe change to 15 minutes?
		features = []
		sums = [0,0,0,0,0,0]
		for i in range(0,len(data)):
			if (i == len(data)-1):
				end_epoch = data[i][0] + 3600 #1 hr
			else:
				end_epoch = data[i+1][0]

			smell_val = get_smell_value(data[i][1])
			feature = make_feature(coord[0], coord[1], data[i][0], end_epoch, smell_val)
			features.append(feature)
			sums[smell_val] += 1

		dbprint("smell val sums = " + str(sums))
		return features

	api_requests = ['https://esdr.cmucreatelab.org/api/v1/feeds/29/channels/PM25_UG_M3,PM25T_UG_M3/export?format=json',
	'https://esdr.cmucreatelab.org/api/v1/feeds/26/channels/SONICWS_MPH,SONICWD_DEG,PM25B_UG_M3/export?format=json',
	'https://esdr.cmucreatelab.org/api/v1/feeds/11067/channels/SONICWS_MPH,SONICWD_DEG,PM25T_UG_M3/export?format=json',
	'https://esdr.cmucreatelab.org/api/v1/feeds/1/channels/SONICWS_MPH,SONICWD_DEG,PM25B_UG_M3,PM25T_UG_M3/export?format=json',
	'https://esdr.cmucreatelab.org/api/v1/feeds/30/channels/PM25_UG_M3/export?format=json'
	]

	e0 = dt_to_epoch(start_date)
	e1 = dt_to_epoch(end_date) + 86400 #get data from last day

	# change time range
	for i in range(0,len(api_requests)):
		r = api_requests[i]
		api_requests[i] = r + '&from=' + str(e0) + '&to=' + str(e1)

	# loop through all sensors
	all_sensor_feats = []
	for r in api_requests:
		sensor_feats = process_request(r)
		if (len(sensor_feats) > 0):
			all_sensor_feats += sensor_feats

	return all_sensor_feats

# process aggregates
# if channel is pm025, get extra sensors directly from esdr
# inputs start and end are epoch times
def process_all_and_output(start, end, channel):
	if (channel == "SONICWS_MPH" or channel == "SONICWD_DEG"):
		return process_wind(start, end, channel)

	start_date = epoch_to_est(start)
	end_date = epoch_to_est(end)

	date_range = get_date_range(start_date, end_date)
	ROOT = "https://data2.createlab.org/esdr-aggregates/"

	# for each day, get feature array, append to total 
	all_features = []
	for date in date_range:
		url = ROOT + channel + "_" + date + ".json"
		sensor_data = request_url(url)
		if (sensor_data == None):
			raise Exception("bad data from request from " + url)
			continue
		day_features = process_day(sensor_data, dt_to_epoch(date), channel)
		all_features += day_features

	if channel == "PM025":
		dbprint("getting pm25 achd")
		all_features += process_pm25_achd(start_date, end_date)

	geojson_out = {"type":"FeatureCollection", "features": all_features}
	return geojson_out

# get wind direction
def process_wind(start, end, channel):
	feed_ids = [1, 3, 26, 28, 32, 35, 43, 11067]
	esdr_root = 'https://esdr.cmucreatelab.org/api/v1/'

	features = []
	for fid in feed_ids:
		url = esdr_root + 'feeds/' + str(fid) + '/channels/' + channel
		url += '/export?format=json&from=' + str(start) + '&to=' + str(end)

		dbprint("requesting lat long")
		coord = get_latlong(url)
		if (coord[0] == None or coord[1] == None):
			dbprint("bad coords")
			continue

		resp_json = request_url(url)
		data = resp_json['data']

		for i in range(0,len(data)):
			epoch0 = data[i][0]
			if (i == len(data)-1):
				epoch1 = data[i][0] + 3600 #1 hr
			else:
				epoch1 = data[i+1][0]

			# some hack w smell_val, convert deg to glyph index
			deg = data[i][1]
			num_glyphs = 16
			chunk = 360 / num_glyphs
			glyph_idx = int(round(deg / chunk, 0))

			feature = make_feature(coord[0], coord[1], epoch0, epoch1, glyph_idx)
			features.append(feature)

	# dbprint(features[0:10])
	geojson_out = {"type":"FeatureCollection", "features": features}
	return geojson_out