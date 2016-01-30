import tornado.escape
import tornado.ioloop
import tornado.web
import staticdata as data
import json

class tileHandler(tornado.web.RequestHandler):
    def get(self, _id, z, x, y):
        x, y, z = int(x), int(y), int(z)
        the_data = data.readRegion(_id , (x, y, z))
        content = json.dumps({
                    "position": [x, y, z],
                    "count": len(the_data),
                    "data": the_data,
                    "bound" : data.areaboundWithId(_id, (x, y, z))
                    });
        self.set_status(200)
        self.set_header('Content-Type', 'application/json')
        self.write(content)

class uploadHandler(tornado.web.RequestHandler):

    def post(self):
        csv = self.request.files.get('csv')
        if csv:
            csv = io.BytesIO(csv[0]['body'])
        _id = self.get_argument('id') 
        # ipdb.set_trace()
        result = data.addCSVToMap(_id, csv)
        content = json.dumps(data.getMaps())
        return Response(mimetype='application/json', status=200, response=content)


class mapHandler(tornado.web.RequestHandler):

    def get(self, _id):
        content = json.dumps(data.getMetaMap(_id))

        self.set_status(200)
        self.set_header('Content-Type', 'application/json')
        self.write(content)

    def post(self, _id):
        info = {}
        request_data = json.loads(self.request.body)
        info['NAME'] = request_data.get('name')
        info['DESCRIPTION'] = request_data.get('description')
        data.modifyMap(request.form.get('id'), info)
        content = json.dumps(data.getMaps())

        self.set_status(200)
        self.set_header('Content-Type', 'application/json')
        self.write(content)

    def put(self, _id):
        request_data = json.loads(self.request.body)

        name = request_data.get("name") or "untitled"
        description = request_data.get("description") or ""
        info = {"NAME": name, "DESCRIPTION" : description}
        newmeta = data.createMap(info)
        content = json.dumps(newmeta)

        self.set_status(200)
        self.set_header('Content-Type', 'application/json')
        self.write(content)

class mainHandler(tornado.web.RequestHandler):

    def get(self, *args):
        self.set_status(200)
        self.render('./static/index.html')
        

class redirectHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect('/viewmap/')

class mapsHandler(tornado.web.RequestHandler):

    def get(self, *args):
        content = json.dumps(data.getMaps())
        
        self.set_status(200)
        self.set_header('Content-Type', 'application/json')
        self.write(content)



application = tornado.web.Application([
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': './static'}),
        (r'/api/tile/([0-9a-z]+)/(-?[0-9]+)/(-?[0-9]+)/(-?[0-9]+).json', tileHandler),
        (r'/api/maps/upload', uploadHandler),
        (r'/api/map/([0-9a-z]+)', mapHandler),
        (r'/api/maps', mapsHandler),
        (r'/viewmap/(.*)', mainHandler),
        (r'/', redirectHandler),
        ], debug=True)

if __name__ == '__main__':
    application.listen('4000')
    tornado.ioloop.IOLoop.instance().start()
