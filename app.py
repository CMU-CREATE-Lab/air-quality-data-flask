# app.py
# serves requests for sensor data given date range and channel
from flask import Flask, jsonify, request, Response
from process_sensor_data import *

app = Flask(__name__)

def error_resp(msg):
	resp = jsonify(msg)
	resp.status_code = 400
	return resp

@app.route('/')
def api_root():
	sample1 = "http://data.airquality.createlab.org/smell_reports?from=1556683200&to=1559361599"
	sample2 = "https://data.airquality.createlab.org/sensor_data?from=1556683200&to=1559361599&channel=PM025"
	return "Sample requests :{}, {}".format(sample1, sample2)

@app.route('/sensor_data')
def api_sensor_data():
	# sample request: https://data.airquality.createlab.org/sensor_data?from=1556683200&to=1559361599&channel=PM025
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
	# sample request: http://data.airquality.createlab.org/smell_reports?from=1556683200&to=1559361599
	if ('from' in request.args) and ('to' in request.args):
		start = request.args['from']
		end = request.args['to']

		if (not is_valid_date_range(start,end)):
			msg = {"status":400, "message":"Malformed Request, bad date range: " + request.url}
			return error_resp(msg)

		url_template = "http://api.smellpittsburgh.org/api/v2/smell_reports?format=geojson&city_ids=1&start_time={}&end_time={}&timezone_string=America%2FNew_York"
		url = url_template.format(start,end)

		try:
			gjs = request_url(url)
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