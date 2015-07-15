import pymongo as pmg
import pandas as pd
from bson.objectid import ObjectId

client = pmg.MongoClient('localhost', 27017)
db = client['database']
meta_collection = db['meta-data']

def getMaps():
    '''
    return the list of maps metadata
    '''

    def convert(x):
        x['_id'] = str(x['_id'])
        return x

    return [convert(item) for item in meta_collection.find()]

def createMap(csv, info):
    '''
    Create Map Collection with the CSV FILE and info
    It will then return the ID of the instance.
    Each entry will have the following infos
    ["NAME", "DESCRIPTION", "HEADER", <ENTRY>] // capitalised since it is meta :)
    return the new_id:String if successful or None if failed
    '''
    data = pd.read_csv(csv)
    meta = getMetaData(data)
    meta['NAME'] = info['NAME']
    meta['DESCRIPTION'] = info['DESCRIPTION']
    result = meta_collection.insert_one(meta)
    new_id = str(result.inserted_id)
    new_collection = createMapCollection(new_id)
    insertCSV(new_collection, data)
    return new_id

def deleteMap(_id):
    '''
    Delete Map Collection with CSV FILE and INFO
    return _id:String if successful
    '''
    try:
        db['map-%s'%_id].drop()
        meta_collection.find_one_and_delete({'_id': ObjectId(_id)})
    except:
        return

def readRegion(collection, tileCoord):
    '''
    collection by mongo collection
    tileCoord by (x,y,z)
    '''
    cursor = collection.find({
                            'loc': areaFilter(tileCoord), 
                            'B_IMAGE': sizeFilter(tileCoord)
                            }, {'_id': 0, 'loc': 0})
    return cursor.count(), list(cursor)



#=============== database utility ========================
def createMapCollection(_id):
    '''
    create the map collection with the corrent id,
    if it is already existed, it will raise exception,
    indexed by 'loc'
    '''
    collection = db.create_collection('map-%s' % _id)
    collection.create_index([('loc', pmg.GEOSPHERE)])
    return collection

def insertCSV(collection, data):
    '''
    The data object shall be in the panda dataFrame,
    the requirement field include RA, DEC, A_IMAGE, B_IMAGE, THETA
    '''
    collection.insert([indexedItem(dict(row)) for (idx, row) in data.iterrows()])


def getMetaData(data):
    '''
    Input : panda DataFrame,
    Output : {
    "HEADER" : [<String>] // set of all the header name
    <ENTRY> : {
        "type" : "String" or "FLOAT" or "INT"
        "max" : <Number>,
        "min" : <Number> // max and min only exists if its time is Number
        }
    }
    '''
    meta = dict()
    header = meta['HEADER'] = list(data.columns)
    for column in header:
        if data.dtypes[column].name == 'float64':
            meta[column] = {'type': 'FLOAT', 'max': data[column].max(), 'min': data[column].min()}
        elif data.dtypes[column].name == 'int64':
            meta[column] = {'type': 'FLOAT', 'max': data[column].max(), 'min': data[column].min()}
        else:
            meta[column] = {'type': 'String'}
    return meta

# =============== map utility =================

def ratioScale(coord):
    '''
    scale an (lng, lat) from [(-180,-90), (180, 90)] to [(0,0), (1,1)]
    '''
    lng, lat = coord
    return (lng + 180)/360, (lat + 90)/180


def geoScale(point):
    '''
    scale an (x,y) from [(0,0), (1,1)] to [(-180,-90), (180, 90)]
    '''
    x, y = point
    return x*360 - 180, y*180 - 90

def areabound(tileCoord):
    x, y, z = tileCoord
    size = 2**z
    lng1, lat1 = geoScale((x/size, y/size))
    lng2, lat2 = geoScale(((x + 1)/size, (y + 1)/size))
    return (lng1, lat1), (lng2, lat2)

def sizeFilter(tileCoord):
    '''
    a query that filter out the ellipsis to small to display
    all ellipsis less than one pixel will not be displayed
    '''
    (x, y, z) = tileCoord
    return {'$gt': 648000.0/(0.23*2**z*256)}

def areaFilter(tileCoord):
    '''
    project (x,y,z) -> geojson square
    '''
    (lng1, lat1), (lng2, lat2) = areabound(tileCoord)
    return {
        '$geoIntersects': 
            {'$geometry': 
                {'type': 'Polygon', 
                'coordinates': 
                    [[[lng1, lat1], 
                    [lng1, lat2], 
                    [lng2, lat2], 
                    [lng2, lat1], 
                    [lng1, lat1]]]
                }
            }
        }

def indexedItem(item):
    '''
    generate spatial index as geojson spec for the item 
    for each ellipses, we consider it as a square box for max boundary lng/lat(+/-)majorsemi
    thus, add 'loc' property
    '''
    lng = item['RA'] - 180
    lat = item['DEC']
    a = item['A_IMAGE']*0.23/3600.0
    latbound = [-90, 90]
    lngbound = [-180, 180]
    lng1, lng2 = bound(lng - a, lngbound), bound(lng + a, lngbound)
    lat1, lat2 = bound(lat - a, latbound), bound(lat + a, latbound)
    item['loc'] = {'type': 'Polygon', 'coordinates': [[[lng1, lat1], [lng2, lat1], [lng2, lat2], [lng1, lat2], [lng1, lat1]]]}
    return item


