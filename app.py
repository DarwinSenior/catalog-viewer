from flask import Flask, Response, request
import json
import data
app = Flask(__name__, static_url_path="")


@app.route("/")
def hello():
    return app.send_static_file('./index.html')

@app.route('/test', methods=["POST"])
def test():
	content = json.dumps(list(request.form.keys()))
	print(list(request.files.keys()))
	return Response(mimetype="application/json", status=200, response=content)

@app.route('/tile/<_id>/<int:z>/<int:x>/<int:y>.json', methods=["GET"])
def jsons(_id, x, y, z):
	count, objs = data.readRegion(data.db["map-%s"%_id], (x,y,z))
	content = json.dumps({
			"text": '<x>:%d <y>:%d <z>:%d'%(x, y, z), 
			"count": count,
			"data": objs,
			"bound" : data.areabound((x,y,z))
			})
	return Response(mimetype="application/json", status=200, response=content)

@app.route('/maps', methods=["GET"])
def get_maps():
	content = json.dumps(data.getMaps())
	return Response(mimetype="application/json", status=200, response=content)

@app.route('/maps', methods=["PUT"])
def put_map():
	name = request.form.get("name") or "untitled"
	description = request.form.get("description") or ""
	csv = request.files.get("csv")
	info = {"NAME": name, "DESCRIPTION" : description}
	print(list(request.form.keys()))
	data.createMap(csv, info)
	content = json.dumps(data.getMaps())
	return Response(mimetype="application/json", status=200, response=content)
	# return json.dumps(info)

@app.route('/maps', methods=["DELETE"])
def delete_map():
	_id = request.form.get("id")
	data.deleteMap(_id)
	content = json.dumps(data.getMaps())
	return Response(mimetype="application/json", status=200, response=content)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')