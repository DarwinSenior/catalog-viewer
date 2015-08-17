import code
import numpy as np
import pymongo as pmg
import pandas as pd
from bson import ObjectId
import logging

client = pmg.MongoClient('localhost', 27017)
db = client['database']
meta_collection = db['meta-data']

# the data structure we are using shall be similar to quadtree. 
# It could be done with the following scheme
# The map of this kind will be considered static.
# the following is the spec of the metadata

# {
#   type: "static",
#   bound: {
#           ramin: <Number>,
#           ramax: <Number>,
#           decmin: <Number>,
#           decmax: <Number>,
#       },
#  proto: meta-map //and all the attribute of basic meta 
# }

# The reason to use bound is to create a more flexible ratio
# we currently make assumption that the map is of small region
# which suffice to use linear tranformation

meta_collection = db['meta-data']


# We use the lazy initialisation but with the proper division
# =============== utility functions =========================

def getMaps():
    """
    return the list of maps metadata
    """
    return [idConvert(item) for item in meta_collection.find()]


def areaboundWithId(_id, tile_coord):
    """
    return bound, if not found return None
    """
    meta = meta_collection.find_one({'_id': ObjectId(_id)})
    if not meta: return None
    total_bound = meta['bound']
    return areabound(total_bound, tile_coord)

def readRegion(_id, tile_coord):
    x, y, z = tile_coord
    if not (0<=x<2**z and 0<=y<2**z):
        return []
    col = collection(_id)
    result = col.find_one(
            {'loc': str(tile_coord)}, 
            {'visibledata': 1})
    if not result:
        generate(_id, tile_coord)
        result = col.find_one(
                {'loc': str(tile_coord)}, 
                {'visibledata': 1})
    return result['visibledata']

def deleteMap(_id):
    collection(_id).drop()
    meta_collection.find_one_and_delete({'_id': ObjectId(_id)}) 

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
    meta['type'] = info.get('type') or 'static'
    meta['bound'] = info.get('bound') or 'auto'
    result = meta_collection.insert_one(meta)
    new_id = str(result.inserted_id)
    newmeta = meta_collection.find_one({'_id': ObjectId(new_id)})
    newmeta['_id'] = str(newmeta['_id'])
    return newmeta

def addCSVToMap(_id, csv):
    try:
        finder = {'_id': ObjectId(_id)}
        meta = meta_collection.find_one(finder)
        if meta['status']!='empty':
            return False
        meta_collection.find_one_and_update(finder, {'$set': {'status': 'processing'}})
        data = pd.read_csv(csv)
        new_collection = createMapCollection(_id)
        meta.update(getMetaData(data))
        meta['tightbound'] = tightbound(data)
        insertCSV(_id, data)
        meta['status'] = 'ready'
        meta['bound'] = autobound(meta)
        meta_collection.find_one_and_update(finder, {'$set': meta})
        # meta_collection.find_one_and_update(finder, {'$set': {'bound': bound}})
        return True
    except:
        logging.exception('exception happend')
        collection(_id).drop()
        meta_collection.find_one_and_update(finder, {'$set': {'status': 'empty'}})
        meta_collection.find_one_and_delete(finder)
        return False

# =================== utility private functions =====================

def collection(_id):
    return db['mapstatic-%s'%_id]

def createMapCollection(_id):
    collection = db.create_collection('mapstatic-%s'%_id) 
    collection.create_index('loc')

def generate(_id, tile_coord):
    x, y, z = tile_coord
    print("generate %d %d %d"%(x,y,z))
    meta = meta_collection.find_one({'_id': ObjectId(_id)})
    if not meta: return 
    result = collection(_id).find_one({'loc': str(tile_coord)}, {'loc': 1})
    if not result:
        upper_coord = (x//2, y//2, z-1) if z>0 else 'root'
        if z>0:
            generate(_id, upper_coord)
        result = collection(_id).find_one({'loc': str(upper_coord)}, {'data': 1})
        if not result: return
        upper_region = result['data']
        upper_bound = meta['bound']
        if z>0:
            splits = regionSplit(upper_coord, upper_bound, upper_region)
        else:
            splits = [((0,0,0), upper_bound, upper_region)]
        print(len(upper_region))
        for coord, bound, data in splits:
            print(len(data), coord, bound, (bound['ramax']-bound['ramin'])*(bound['decmax']-bound['decmin']))
            visibledata = list(filter(visibleInArea(bound), data))
            saveRegion(_id, coord, data, visibledata) 

def saveRegion(_id, coord, data, visible_data):
    print("save coord %s"%(str(coord)))
    collection(_id).update(
            {'loc': str(coord)},
            {'$set': {'loc': str(coord), 'data': data, 'visibledata': visible_data} }, 
            True)

def insertCSV(_id, data):
    data = [dict(row) for (idx, row) in data.iterrows()]
    collection(_id).insert_one({'loc': 'root', 'data': data})



#================= pure =======================

def visibleInArea(bound, size=None):
    """
    Return a function that takes the data to see if it fits the area
    """
    size = size or (0.1/256)
    bound_range = max(bound['ramax']-bound['ramin'], bound['decmax']-bound['decmin'])
    return lambda data: (data['B_IMAGE']*0.23/3600.0/bound_range>size)


def areabound(bound, tile_coord):
    """
    Given the the total bound (0,0,0),
    Output the bound of the tile
    """
    x, y, z = tile_coord
    RA_range = bound['ramax']-bound['ramin']
    DEC_range = bound['decmax']-bound['decmin']
    size = 2**z
    return {
                'ramax': bound['ramin']+(RA_range/size*(x+1)),
                'ramin': bound['ramin']+(RA_range/size*x),
                'decmax': bound['decmin']+(DEC_range/size*(y+1)),
                'decmin': bound['decmin']+(DEC_range/size*y),
            }


def intersection(bound1, bound2):
    """
    return True if two bounds are intersecting with each other
    """
    return not (
                bound2['ramax'] < bound1['ramin'] or
                bound2['ramin'] > bound1['ramax'] or
                bound2['decmax'] < bound1['decmin'] or
                bound2['decmin'] > bound1['decmax'])

def tightbound(data):
    """
    Input: panda DataFrame,
    Output: bound object {ramin, ramax, demin, decmax}
    """
    return {
            'ramin': np.min(data.RA.values-data.A_IMAGE.values*0.23/3600),
            'ramax': np.max(data.RA.values+data.A_IMAGE.values*0.23/3600),
            'decmin': np.min(data.DEC.values-data.A_IMAGE.values*0.23/3600),
            'decmax': np.max(data.DEC.values+data.A_IMAGE.values*0.23/3600),
            }


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


def regionSplit(tile_coord, bound, data):
    """
    given bound and the tileCoord,
    split the data into four quads 
    returns [(tile_coord, bound, data)*4] for four area 
    """
    x, y, z = tile_coord
    quad_coords = [(x*2, y*2, z+1), (x*2+1, y*2, z+1), (x*2, y*2+1, z+1), (x*2+1, y*2+1, z+1)]
    quads = [(coord, areabound(bound, coord), []) for coord in quad_coords]
    for datum in data:
        for coord, bound, element_list in quads:
            radius = datum['A_IMAGE']*0.23/3600.0
            dec = datum['DEC']
            ra = datum['RA']
            rect = {'ramax': ra+radius, 'ramin': ra-radius, 'decmax': dec+radius, 'decmin': dec-radius}
            if intersection(rect, bound):
                element_list.append(datum)
    return quads

def idConvert(data):
    """
    Convert the _id entry so that data is fully json instead of bson
    """
    data['_id'] = str(data['_id'])
    return data

def autobound(meta, margin=0.5):
    """
    Input a meta object, 
    if the bound is auto,
    returns the new generated bound, square with margin
    else, return origional bound
    """
    if (meta and meta['bound'] == 'auto'):
        try:
            center_y = (meta['DEC']['max']+meta['DEC']['min'])/2
            center_x = (meta['RA']['max']+meta['RA']['min'])/2
            size_y = (meta['DEC']['max']-meta['DEC']['min'])
            size_x = (meta['RA']['max']-meta['RA']['min'])
            size = max(size_x, size_y)*(1+margin)
            bound = {
                    'decmax': center_y+size/2,
                    'decmin': center_y-size/2,
                    'ramax': center_x+size/2,
                    'ramin': center_x-size/2,
                    }
            return bound
        except:
            logging.exception('exception happend')
            return meta['bound']
    else:
        return meta['bound']


