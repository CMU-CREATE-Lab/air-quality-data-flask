# app.py
# serves requests for sensor data given date range and channel
# request format: [optional parameters]
# 	/smell_reports?from={start epoch}&to={end epoch} [cityId={num}, getMostRecent{num minutes}]
# 	/sensor_reports?from={start epoch}&to={end epoch}&channel={channel} [getMostRecent{num minutes}]
from flask import Flask, jsonify, request, Response
from process_sensor_data import *

app = Flask(__name__)

def error_resp(msg):
	resp = jsonify(msg)
	resp.status_code = 400
	return resp

@app.route('/')
def api_root():
	template1 = "/smell_reports?from={start epoch}&to={end epoch} [cityId={num}, getMostRecent{num minutes}]"
	template2 = "/sensor_reports?from={start epoch}&to={end epoch}&channel={channel} [getMostRecent{num minutes}]"
	return "Request format [optional parameters]: {}, {}".format(template1, template2)

@app.route('/sensor_data')
def api_sensor_data():
	# sample request: /sensor_data?from=1556683200&to=1559361599&channel=PM025
	if ('from' in request.args) and ('to' in request.args) and ('channel' in request.args):
		start = request.args['from']
		end = request.args['to']
		channel = request.args['channel']

		if (not is_valid_date_range(start,end)):
			msg = {"status":400, "message":"Malformed Request, bad date range: " + request.url}
			return error_resp(msg)

		if (not is_valid_channel(channel)):
			msg = {"status":400, "message":"Malformed Request, bad channel name: " + request.url}
			return error_resp(msg)

		try:
			if ("getMostRecent" in request.args):
				try:
					minutes_back = int(request.args["getMostRecent"])
				except:
					msg = {"status":400, "message":"Malformed Request, bad most recent data time range: " + request.url}
					return error_resp(msg)

				time_period =  int(minutes_back * 60)
				new_end = int(datetime.datetime.timestamp(datetime.datetime.now()))
				new_start = new_end - time_period

				# TODO timeout?
				gjs = process_all_and_output(new_start, new_end, channel)
				while is_empty(gjs["features"]):
					new_end = new_start
					new_start = new_end - time_period
					gjs = process_all_and_output(new_start, new_end, channel)

				resp = jsonify({ "startDate": new_start, "endDate": new_end, "geojson": gjs})
			else:
				gjs = process_all_and_output(start, end, channel)
				resp = jsonify(gjs)

			resp.status_code = 200
			return resp
		except Exception as inst:
			msg = {"status":400, "message":"Processing Error: " + request.url + ", " + inst.args[0]}
			return error_resp(msg)
	else:
		msg = {"status":400, "message":"Malformed Request, missing arguments: " + request.url}
		return error_resp(msg)

@app.route('/smell_reports')
def api_smell_reports():
	# sample request: /smell_reports?from=1556683200&to=1559361599
	if ('from' in request.args) and ('to' in request.args):
		start = request.args['from']
		end = request.args['to']

		if (not is_valid_date_range(start,end)):
			msg = {"status":400, "message":"Malformed Request, bad date range: " + request.url}
			return error_resp(msg)

		# url_template = "http://api.smellpittsburgh.org/api/v2/smell_reports?format=geojson&city_ids=1&start_time={}&end_time={}&timezone_string=America%2FNew_York"
		url_template = "http://api.smellpittsburgh.org/api/v2/smell_reports?format=geojson&city_ids={}&start_time={}&end_time={}&timezone_string=America%2FNew_York"
		city_id = "1" if not ('cityId' in request.args) else request.args["cityId"]

		try:
			if ("getMostRecent" in request.args):
				try:
					minutes_back = int(request.args["getMostRecent"])
				except:
					msg = {"status":400, "message":"Malformed Request, bad most recent data time range: " + request.url}
					return error_resp(msg)

				time_period =  int(minutes_back * 60)
				new_end = int(datetime.datetime.timestamp(datetime.datetime.now()))
				new_start = new_end - time_period

				# TODO timeout?
				gjs = request_url(url_template.format(city_id, new_start,new_end))
				while is_empty(gjs["features"]):
					new_end = new_start
					new_start = new_end - time_period
					gjs = request_url(url_template.format(city_id, new_start,new_end))

				resp = jsonify({ "startDate": new_start, "endDate": new_end, "geojson": gjs})
			else:
				gjs = request_url(url_template.format(city_id, start,end))
				resp = jsonify(gjs)

			resp.status_code = 200
			return resp
		except Exception as inst:
			msg = {"status":400, "message":"Processing Error: " + request.url + ", " + inst.args[0]}
			return error_resp(msg)
	else:
		msg = {"status":400, "message":"Malformed Request, missing arguments: " + request.url}
		return error_resp(msg)

# with this you can run 'python3 app.py' from cmdline
if __name__ == '__main__':
	app.run()
