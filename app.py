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
	return "Hello\n"

@app.route('/sensor_data')
def api_sensor_data():
	# sample request: https://data.airquality.createlab.org/sensor_data?from=2019-05-01&to=2019-05-02&channel=PM025
	if ('from' in request.args) and ('to' in request.args) and ('channel' in request.args):
		start_date = request.args['from']
		end_date = request.args['to']
		channel = request.args['channel']

		if (not is_valid_date_range(start_date, end_date)):
			msg = {"status":400, "message":"Malformed Request, bad date range: " + request.url}
			return error_resp(msg)

		if (not is_valid_channel(channel)):
			msg = {"status":400, "message":"Malformed Request, bad channel name: " + request.url}
			return error_resp(msg)

		try:
			gjs = process_and_output(start_date, end_date, channel)
			resp = jsonify(gjs)
			resp.status_code = 200
			return resp
		except Exception as inst:
			msg = {"status":400, "message":"Processing Error:" + request.url + ", " + inst.args[0]}
			return error_resp(msg)
	else:
		msg = {"status":400, "message":"Malformed Request, missing arguments: " + request.url}
		return error_resp(msg)

@app.route('/smell_reports')
def api_smell_reports():
	# sample request: http://data.airquality.createlab.org/smell_reports?from=2019-04-01&to=2019-04-02
	#"http://api.smellpittsburgh.org/api/v2/smell_reports?format=geojson&city_ids=1&start_time=1556683200&end_time=1559361599&timezone_string=America%2FNew_York"
	if ('from' in request.args) and ('to' in request.args):
		start = str(dt_to_epoch(request.args['from']))
		end = str(dt_to_epoch(request.args['to']))

		if (not is_valid_date_range(request.args['from'], request.args['to'])):
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
			msg = {"status":400, "message":"Processing Error:" + request.url + ", " + inst.args[0]}
			return error_resp(msg)
	else:
		msg = {"status":400, "message":"Malformed Request, missing arguments: " + request.url}
		return error_resp(msg)

# with this you can run 'python3 app.py' from cmdline
if __name__ == '__main__':
	app.run()
