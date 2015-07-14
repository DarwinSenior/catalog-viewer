/*
SVGLayer is a layer giving up control to the user to do specialised drawing.

Instead of loading an image for each tile, each tile is associate with data
specified by the url (usually json).

When the tile is loaded along with the data, you could use the data to draw 
on that div with your own function: Data -> Div -> Div
where Data is specified by the URL and Div is a <div> with 256x256 size.

When the tile is detached, you could provide your own cleaner function or you
could leave it empty: Div -> Div.
*/

L.SVGLayer = L.GridLayer.extend({
	options : {
		maxZoom : 18,

		subdomains: 'abc',
		errorTileUrl: '',
		zoomOffset: 0,

		maxNativeZoom: null, // Number
		tms: false,
		zoomReverse: false,
		crossOrigin: false
	},

	initialize : function(url, options, drawer, cleaner){
		this._url = url;
		this.drawer = drawer || L.Util.falseFn; // svg drawing
		this.cleaner = cleaner || L.Util.falseFn;
		this.options = L.setOptions(this, options);

		this._xhrs = {};

		this.on('tileunload', (this._onremove).bind(this));
	},

	setUrl : function(url){
		this._url = url;
		this.redraw();
		return this;
	},

	createTile : function(coords, done){
		var tile = document.createElement('div');
		var url = this.getTileUrl(coords);
		
		var key = this._getKey(coords);

		this._xhrs[key] = d3.json(url);
		this._xhrs[key].on('load', (function(data){
				this._onload(data, tile, done);
			}).bind(this));
		this._xhrs[key].on('error', (function(error){
				this._onerror(error, tile, done);
		}).bind(this));
		this._xhrs[key].get();

		return tile;
	},

	getTileUrl : function(coords){
		return L.Util.template(this._url, L.extend({
			s : this._getSubdomain(coords),
			x : coords.x,
			y : this.options.tms ? this._globalTileRange.max.y - coords.y : coords.y,
			z : this._getZoomForUrl()
		}, this.options));
	},


	_onremove : function(evt){
		// console.log(evt.target);
		// The target consists {coords :{x, y, z}, target, tile}
		this.cleaner(evt.tile);
	},

	_onload : function(data, tile, done){
		this.drawer(data, tile, this);
		done(null, tile);
	},

	_onerror : function(error, tile, done){
		var errorUrl = this.options.errorTileUrl;
		done(null, tile);
	},

	_getZoomForUrl: function () {

		var options = this.options,
		    zoom = this._tileZoom;

		zoom += options.zoomOffset;

		return options.maxNativeZoom ? Math.min(zoom, options.maxNativeZoom) : zoom;
	},

	_getSubdomain: function (tilePoint) {
		var index = Math.abs(tilePoint.x + tilePoint.y) % this.options.subdomains.length;
		return this.options.subdomains[index];
	},

	_abortLoading : function(){
		var i, tile, xhr;
		for (i in this._tiles){
			tile = this._tiles[i];
			if (!tile.complete){
				L.DomUtil.remove(tile);
			}
		}
		for (i in this._xhrs){
			xhr = this._xhrs[i];
			xhr.on('load', L.Util.falseFn);
			xhr.on('error', L.Util.falseFn);
		}

	},

	_getKey : function(coords){
		z = this._getZoomForUrl();
		x = coords.x;
		y = coords.y;
		return x + ':' + y + ':' + z
	}
});

L.svgLayer = function(url, options, drawer, cleaner){
	return new L.SVGLayer(url, options, drawer, cleaner);
}