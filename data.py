import pymongo as pmg
import pandas as pd
from bson import ObjectId
import logging

client = pmg.MongoClient('localhost', 27017)
db = client['database']
meta_collection = db['meta-data']

def getMaps():
    """
    return the list of maps metadata
    """

    def convert(x):
        x['_id'] = str(x['_id'])
        return x

    return [convert(item) for item in meta_collection.find()]


def addCSVToMap(_id, csv):
    """
    Add CSV file to the map, if it is empty
    If error or the status is not empty, 
    return False else return True
    """
    finder = {'_id': ObjectId(_id)}
    try:
        if meta_collection.find_one(finder)['status']!='empty':
            return False
        meta_collection.find_one_and_update(finder, {'$set': {'status': 'processing'}})
        data = pd.read_csv(csv)
        new_collection = createMapCollection(_id)
        cached_collection = creatMapCacheCollection(_id)
        meta = getMetaData(data)
        meta['status'] = 'ready'
        insertCSV(new_collection, data)
        meta_collection.find_one_and_update(finder, {'$set': meta})
        return True
    except Exception as err:
        logging.exception('exception happend')
        noncachedCollection(_id).drop()
        cachedCollection(_id).drop()
        meta_collection.find_one_and_update(finder, {'$set': {'status': 'empty'}})
        meta_collection.find_one_and_delete(finder)
        return False


 
def createMap(info):
    """
    Create this map with Name and Description
    and then return the ID of the instance
    also it will set the status of this instance 
    as 'empty'.
    There are 4 kinds of status
    'empty' : this instance has not been initialised yet, file to be added, or there is an error
    'processing' : there is another process that is dealing with the data
    'ready' : the file added, thus ready for view
    """
    meta = dict()
    meta['NAME'] = info.get('NAME') or 'undefined'
    meta['DESCRIPTION'] = info.get('DESCRIPTION') or ""
    meta['status'] = 'empty'
    meta['type'] = info.get('type') or 'cached'
    result = meta_collection.insert_one(meta)
    new_id = str(result.inserted_id)
    newmeta = meta_collection.find_one({'_id': ObjectId(new_id)})
    newmeta['_id'] = str(newmeta['_id'])
    return newmeta

   

def modifyMap(_id, info):
    """
    The Name and the descriptions are two items are allowed to modify
    """
    meta = meta_collection.find_one({"_id": ObjectId(_id)})
    meta['NAME'] = info['NAME'] or meta['NAME']
    meta['DESCRIPTION'] = info['NAME'] or meta['DESCRIPTION']
    result = meta_collection.find_one_and_update(
            {"_id": ObjectId(_id)},
            {"$set": meta})
    return result

def deleteMap(_id):
    """
    Delete Map Collection with CSV FILE and INFO
    return _id:String if successful
    """
    try:
        cachedCollection(_id).drop()
        noncachedCollection(_id).drop()
        meta_collection.find_one_and_delete({'_id': ObjectId(_id)})
    except:
        return

def readCachedRegion(collection, tileCoord):
    """
    Find the tileCoords in the cached tileCoords
    If found, return the tile or just json file,
    else return None for missing cache
    """
    data = collection.find_one({'loc': str(tileCoord)}, {'_id': 0, 'loc': 0})
    return data['data'] if data else None

def readUncachedRegion(collection, tileCoord):
    """
    tileCoord is an tuple consisting of (x,y,z)
    """
    cursor = collection.find({
                            'loc': areaFilter(tileCoord), 
                            'B_IMAGE': sizeFilter(tileCoord)
                            }, {'_id': 0, 'loc': 0})
    return list(cursor)


def readRegion(_id, tileCoord):
    cached_collection = cachedCollection(_id)
    nonecached_collection = noncachedCollection(_id)
    data = readCachedRegion(cached_collection, tileCoord)
    data = None
    if data:
        print('cached!')
        return data
    else:
        print('not cached!')
        data = readUncachedRegion(nonecached_collection, tileCoord)
        if len(data)>0:
            cached_collection.insert_one({'loc': str(tileCoord), 'data': data})
        return data

#=============== database utility ========================
def cachedCollection(_id):
    return db['mapcache-%s'%_id]

def noncachedCollection(_id):
    return db['map-%s'%_id]

def creatMapCacheCollection(_id):
    """
    Create the map collection for cache tile system
    """
    collection = db.create_collection('mapcache-%s'%_id)
    collection.create_index('loc')

def createMapCollection(_id):
    """
    create the map collection with the corrent id,
    if it is already existed, it will raise exception,
    indexed by 'loc'
    """
    collection = db.create_collection('map-%s' % _id)
    collection.create_index([('loc', pmg.GEOSPHERE)])
    return collection

def insertCSV(collection, data):
    """
    The data object shall be in the panda dataFrame,
    the requirement field include RA, DEC, A_IMAGE, B_IMAGE, THETA
    """
    collection.insert([indexedItem(dict(row)) for (idx, row) in data.iterrows()])


def getMetaData(data):
    """
    Input : panda DataFrame,
    Output : {
    "HEADER" : [<String>] // set of all the header name
    <ENTRY> : {
        "type" : "String" or "FLOAT" or "INT"
        "max" : <Number>,
        "min" : <Number> // max and min only exists if its time is Number
        }
    }
    """
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

def bound(number, domain):
    (lower, higher) = domain
    return (number - lower) % (higher - lower) + lower

def ratioScale(coord):
    """
    scale an (lng, lat) from [(-180,-90), (180, 90)] to [(0,0), (1,1)]
    """
    lng, lat = coord
    return (lng + 180.)/360., (lat + 90.)/180.


def geoScale(point):
    """
    scale an (x,y) from [(0,0), (1,1)] to [(-180,-90), (180, 90)]
    """
    x, y = point
    return x*360. - 180., y*180. - 90.

def areabound(tileCoord):
    x, y, z = tileCoord
    size = 2.**z
    lng1, lat1 = geoScale((x/size, y/size))
    lng2, lat2 = geoScale(((x + 1)/size, (y + 1)/size))
    return (lng1, lat1), (lng2, lat2)

def sizeFilter(tileCoord):
    """
    a query that filter out the ellipsis to small to display
    all ellipsis less than one pixel will not be displayed
    """
    (x, y, z) = tileCoord
    pixelsize = 0.1
    return {'$gt': 648000.0*pixelsize/(0.23*2**z*256)}

def areaFilter(tileCoord):
    """
    project (x,y,z) -> geojson square
    """
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
    """
    generate spatial index as geojson spec for the item 
    for each ellipses, we consider it as a square box for max boundary lng/lat(+/-)majorsemi
    thus, add 'loc' property
    """
    lng = item['RA'] - 180.
    lat = item['DEC']
    a = item['A_IMAGE']*0.23/3600.0
    latbound = [-90., 90.]
    lngbound = [-180., 180.]
    lng1, lng2 = bound(lng - a, lngbound), bound(lng + a, lngbound)
    lat1, lat2 = bound(lat - a, latbound), bound(lat + a, latbound)
    item['loc'] = {'type': 'Polygon', 'coordinates': [[[lng1, lat1], [lng2, lat1], [lng2, lat2], [lng1, lat2], [lng1, lat1]]]}
    return item


