from flask import Flask, Response, request, redirect

import json
# import data
import staticdata as data


app = Flask(__name__, static_url_path="/static")


@app.route('/api/tile/<_id>/<int:z>/<int:x>/<int:y>.json', methods=["GET"])
def jsons(_id, x, y, z):
    """
    Returns the tile, look at leaflet for details
    """
    the_data = data.readRegion(_id , (x, y, z))
    content = json.dumps({
                "position": [x, y, z],
                "count": len(the_data),
                "data": the_data,
                "bound" : data.areaboundWithId(_id, (x, y, z))
                });
    return Response(mimetype="application/json", status=200, response=content)

@app.route('/api/maps', methods=["GET"])
def get_maps():
    content = json.dumps(data.getMaps())
    return Response(mimetype="application/json", status=200, response=content)

@app.route('/api/map/<_id>', methods=["GET"])
def get_map(_id):
    """
    Return the metadata of a specific map
    """
    content = json.dumps(data.getMetaMap(_id))
    return Response(mimetype="application/json", status=200, response=content)



@app.route('/api/maps', methods=["POST"])
def change_map():
    '''
    this is the post api for modifying map
    it could modify the name and the description
    _id is a must field and 'name'/'description' are optional
    '''
    info = {}
    info['NAME'] = request.form.get('name')
    info['DESCRIPTION'] = request.form.get('description')
    data.modifyMap(request.form.get('id'), info)
    content = json.dumps(data.getMaps())
    return Response(mimetype="application/json", status=200, response=content)



@app.route('/api/maps/upload', methods=["POST"])
def attach_file():
    '''
    Attach the file of an given _id,
    thus the data is in the multipart-form
    '''
    _id = request.form.get('id')
    csv = request.files.get('csv')
    result = data.addCSVToMap(_id, csv)
    content = json.dumps(data.getMaps())
    return Response(mimetype='application/json', status=200, response=content)
    



@app.route('/api/maps', methods=["PUT"])
def put_map():
    """
    put a new map with name and description, the response would be the created new map metadata 
    if failed, return 500 <TODO> later
    """
    name = request.form.get("name") or "untitled"
    description = request.form.get("description") or ""
    info = {"NAME": name, "DESCRIPTION" : description}
    newmeta = data.createMap(info)

    content = json.dumps(newmeta)
    return Response(mimetype="application/json", status=200, response=content)

@app.route('/api/maps', methods=["DELETE"])
def delete_map():
    """
    Delete a map with its id and return the new updated metadata
    """
    _id = request.form.get("id")
    data.deleteMap(_id)
    content = json.dumps(data.getMaps())
    return Response(mimetype="application/json", status=200, response=content)


@app.route("/")
def hello():
    """
    start the first page
    """
    return redirect('/viewmap/main')

@app.route("/viewmap/<path:path>")
def pages(path):
    '''
    Serving the starting page
    '''
    return app.send_static_file('./index.html')

if __name__ == "__main__":
    # app.run(debug=True, host='0.0.0.0', port=80)
    app.run(debug=True, host='localhost', port=3000)
    
    
    
