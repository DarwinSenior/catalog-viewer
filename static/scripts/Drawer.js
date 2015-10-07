var Drawer = function(colorAlg, eventAlg, filterAlg, tileSize){
    this._colorAlg = colorAlg || function(){return 'white'};
    this._eventAlg = eventAlg || function(){}; 
    this._filterAlg = filterAlg || function(){return true};
    this._tiles = [];
    tileSize = tileSize || [256, 256]; // width, height
    this._tileWidth = tileSize[0];
    this._tileHeight = tileSize[1];
    this._intensity = 4;
}

Drawer.prototype.drawer = function(data, tile){
    this._tiles.push(tile);
    var svg = d3.select(tile).append('svg:svg')
                .attr('viewBox', '0 0 '+this._tileWidth+' '+this._tileHeight)
                .attr('height', '100%')
                .attr('width', '100%');

    var canvas = d3.select(tile).append('canvas')
                .attr('height', this._tileHeight)
                .attr('width', this._tileHeight)
                .style({height: "100%",
                        width: "100%"});

    ctx = canvas.node().getContext('2d');
    // var background = svg.append('rect')
    //                     .attr('height', this._tileHeight)
    //                     .attr('width', this._tileWidth)
    //                     .attr('x', 0)
    //                     .attr('y', 0)
    //                     .attr('fill', 'black');

    var items = data.data.map((function(item){
        return this._getEllipseData(item, data.bound);
    }).bind(this));
    var radius_limit = 0.5;    
    var svgitems = items.filter(function(d){ return (d.ry>=radius_limit) || (d.rx>=radius_limit)});
    var canvasitems = items.filter(function(d){ return (d.ry<radius_limit) && (d.rx<radius_limit)});
    // canvas.__data__ = canvasitems;
    canvas.data([canvasitems]);
    var ellipses = this.drawSvg(svg, svgitems);
    this.drawCanvas(ctx, canvasitems);
    // this.drawBoundary(svg, data.position);
    ellipses.on('click', this._eventAlg);
};
Drawer.prototype.drawCanvas = function(canvas, data){
    /*
     * This function is for drawing the squres that has size less than one pixel
     * thus lose the ability to interact with
     */
    intensity = this._intensity;
    canvas.fillStyle = '#000000';
    canvas.clearRect(0, 0, this._tileWidth, this._tileHeight);
    data.forEach((function(d){
        canvas.fillStyle = this._colorAlg(d);
        var area = (d.rx*d.ry*Math.PI);
        var side = Math.sqrt(area);
        if (this._filterAlg(d)){
            for (var i=0; i<intensity; i++){
                canvas.fillRect(d.cx, d.cy, side, side);
            }
        }
    }).bind(this));
}


Drawer.prototype.drawSvg = function(svg, items){
    
    var ellipses = svg.selectAll('ellipse')
    .data(items)
    .enter()
    .append('ellipse')
    .attr('cx', function(d){return d.cx})
    .attr('cy', function(d){return d.cy})
    .attr('rx', function(d){return d.rx})
    .attr('ry', function(d){return d.ry})
    .attr('transform', function(d){return d.transform})
    .attr('fill', this._colorAlg)
    .attr('display', (function(d){return (this._filterAlg(d))?"block":"none"}).bind(this));
    return ellipses;
}

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
        var canvas = d3.select(tile).select('canvas');
        this.drawCanvas(canvas.node().getContext('2d'), canvas.data()[0]);
    }

};

Drawer.prototype.changeFilter = function(filterAlg){
    this._filterAlg = filterAlg || this._filterAlg;
    for (var i=0; i<this._tiles.length; i++){
        var tile = this._tiles[i];
        d3.select(tile)
            .selectAll('ellipse')
            .attr('display', (function(d){return (this._filterAlg(d))?"block":"none"}).bind(this));

        var canvas = d3.select(tile).select('canvas');

        this.drawCanvas(canvas.node().getContext('2d'), canvas.data()[0]);
    }
}

Drawer.prototype.changeIntensity = function(new_intensity){
    this._intensity = new_intensity;
    for (var i=0; i<this._tiles.length; i++){
        var tile = this._tiles[i];
        var canvas = d3.select(tile).select('canvas');

        this.drawCanvas(canvas.node().getContext('2d'), canvas.data()[0]);
    }
}

Drawer.prototype._getEllipseData = function(item, bound){
    var rangex = bound.ramax-bound.ramin;
    var rangey = bound.decmax-bound.decmin;
    var offsetx = bound.ramin;
    var offsety = bound.decmin;


    item.cx = (item.RA-offsetx)/rangex*256;
    item.cy = (item.DEC-offsety)/rangey*256;
    item.rx = (item.A_IMAGE*0.23/3600)/rangex*256;
    item.ry = (item.B_IMAGE*0.23/3600)/rangey*256;
    item.transform = ['rotate(', item.THETA_IMAGE+90.0, item.cx, item.cy, ')'].join(' ');
    return item;
};


