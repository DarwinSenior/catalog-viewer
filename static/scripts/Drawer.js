var Drawer = function(colorAlg, eventAlg, tileSize){
	this._colorAlg = colorAlg || function(){return "white"};
	this._eventAlg = eventAlg || function(){}; 
	this._tiles = [];
	tileSize = tileSize || [256, 256]; // width, height
	this._tileWidth = tileSize[0];
	this._tileHeight = tileSize[1];
}

Drawer.prototype.drawer = function(data, tile){
	this._tiles.push(tile);
	var svg = d3.select(tile).append("svg:svg")
				.attr('viewBox', '0 0 '+this._tileWidth+" "+this._tileHeight)
				.attr('height', '100%')
				.attr('width', '100%');

	var background = svg.append('rect')
						.attr('height', this._tileHeight)
						.attr('width', this._tileWidth)
						.attr('x', 0)
						.attr('y', 0)
						.attr('fill', 'black');

	// var text = svg.append('text')
	// 			.attr("text-anchor", "middle")
	// 			.attr("x", 128)
	// 			.attr("y", 120)
	// 			.attr('fill', "white")
	// 			.text(data.text);

	var items = data.data.map((function(item){
		return this._getEllipseData(item, data.bound);
	}).bind(this));

	var ellipses = svg.selectAll('ellipse')
						.data(items)
						.enter()
						.append('ellipse')
						.attr('cx', function(d){return d.cx})
						.attr('cy', function(d){return d.cy})
						.attr('rx', function(d){return d.rx})
						.attr('ry', function(d){return d.ry})
						.attr('transform', function(d){return d.transform})
						.attr('fill', this._colorAlg);
	ellipses.on('click', this._eventAlg);
};

Drawer.prototype.cleaner = function(tile){
	this._tiles = this._tiles.filter(function(item){return item!=tile}); // cut off the tile
	d3.select(tile).selectAll('ellipse').on('click', null);
};

Drawer.prototype.changeEvent = function(eventAlg){
	this._eventAlg = eventAlg || this._eventAlg;
	for (var i=0; i<this._tiles.length; i++){
		var tile = this._tiles[i];
		d3.select(tile)
			.selectAll('ellipse')
			.on('click', this._eventAlg);
	}
};

Drawer.prototype.changeColor = function(colorAlg){
	this._colorAlg = colorAlg || this._colorAlg;
	for (var i=0; i<this._tiles.length; i++){
		var tile = this._tiles[i];
		d3.select(tile)
			.selectAll('ellipse')
			.transition()
			.attr('fill', this._colorAlg);
	}
};
Drawer.prototype._getEllipseData = function(item, bound){
	var rangex = bound[1][0]-bound[0][0];
	var rangey = bound[1][1]-bound[0][1];
	var offsetx = bound[0][0];
	var offsety = bound[0][1];


	item.cx = (item.RA-180-offsetx)/rangex*256;
	item.cy = (item.DEC-offsety)/rangey*256;
	item.rx = (item.A_IMAGE*0.23/3600)/rangex*256;
	item.ry = (item.B_IMAGE*0.23/3600)/rangey*256;
	item.transform = ["rotate(", item.THETA_IMAGE+90.0, item.cx, item.cy, ")"].join(' ');
	return item;
};