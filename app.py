# app.py
# serves requests for sensor data given date range and channel
from flask import Flask, jsonify, request, Response
from process_sensor_data import *

app = Flask(__name__)

@app.route('/')
def api_root():
	return "Hello\n"

@app.route('/sensor_data')
def api_sensor_data():
	# sample request: https://cyb.org/sensor_data?from=2019-05-01&to=2019-05-02&channel=PM025
	if ('from' in request.args) and ('to' in request.args) and ('channel' in request.args):
		start_date = request.args['from']
		end_date = request.args['to']
		channel = request.args['channel']
		gjs = process_and_output(start_date, end_date, channel)
		resp = jsonify(gjs)
		resp.status_code = 200
		return resp
	else:
		msg = {"status":400, "message":"Malformed Request: " + request.url}
		resp = jsonify(msg)
		resp.status_code = 400
		return resp

@app.route('/smell_reports')
def api_smell_reports():
	#sample request: "http://staging.api.smellpittsburgh.org/api/v2/smell_reports?format=geojson&city_ids=1&start_time=1556683200&end_time=1559361599&timezone_string=America%2FNew_York"
	if ('from' in request.args) and ('to' in request.args):
		start = str(dt_to_epoch(request.args['from']))
		end = str(dt_to_epoch(request.args['to']))
		url_template = "http://staging.api.smellpittsburgh.org/api/v2/smell_reports?format=geojson&city_ids=1&start_time={}&end_time={}&timezone_string=America%2FNew_York"
		url = url_template.format(start,end)
		gjs = request_url(url)
		print(url)
		resp = jsonify(gjs)
		resp.status_code = 200
		return resp
	else:
		msg = {"status":400, "message":"Malformed Request: " + request.url}
		resp = jsonify(msg)
		resp.status_code = 400
		return resp

# if __name__ == '__main__':
# 	app.run()