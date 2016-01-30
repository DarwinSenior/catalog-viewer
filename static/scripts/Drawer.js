"use strict"
let Drawer = function(colorAlg, eventAlg, filterAlg, tileSize){
    this._colorAlg = colorAlg || function(){return 'white'};
    this._eventAlg = eventAlg || function(){}; 
    this._filterAlg = filterAlg || function(){return true};
    this._tiles = [];
    tileSize = tileSize || [256, 256]; // width, height
    this._tileWidth = tileSize[0];
    this._tileHeight = tileSize[1];
    this._intensity = 4;
    this._scale = 1;
}

Drawer.prototype.drawer = function(data, tile){
    this._tiles.push(tile);
    let tile_select = d3.select(tile)
    let svg = tile_select.append('svg:svg')
                .attr('viewBox', '0 0 '+this._tileWidth+' '+this._tileHeight)
                .attr('height', '100%')
                .attr('width', '100%');

    let canvas = tile_select.append('canvas')
                .attr('height', this._tileHeight)
                .attr('width', this._tileHeight)
                .style({height: "100%",
                        width: "100%"});

    let ctx = canvas.node().getContext('2d');

    
    let items = data.data.map(item => this._getEllipseData(item, data.bound));
    let radius_limit = 0.5*this._scale;    

    let svgitems = items.filter(d => d.ry>=radius_limit || d.rx>=radius_limit);
    let canvasitems = items.filter(d => d.ry<radius_limit && d.rx<radius_limit);
    canvas.datum(canvasitems);

    let ellipses = this.drawSvg(svg, svgitems);

    this.drawCanvas(ctx, canvasitems);

    ellipses.on('click', this._eventAlg);
};


Drawer.prototype.drawCanvas = function(canvas, data){
    /*
     * This function is for drawing the squres that has size less than one pixel
     * thus lose the ability to interact with
     */
    let intensity = this._intensity;
    canvas.fillStyle = '#000000';
    canvas.clearRect(0, 0, this._tileWidth, this._tileHeight);
    data.forEach( d => {
        canvas.fillStyle = this._colorAlg(d);
        let area = (d.rx*d.ry*Math.PI*this._scale*this._scale);
        let side = Math.sqrt(area);
        if (this._filterAlg(d)){
            for (let i=0; i<intensity; i++){
                canvas.fillRect(d.cx, d.cy, side, side);
            }
        }
    });
}


Drawer.prototype.drawSvg = function(svg, items){

    let ellipses = svg.selectAll('ellipse')
    .data(items)
    .enter()
    .append('ellipse')
    .attr('cx', d => d.cx)
    .attr('cy', d => d.cy)
    .attr('rx', d => d.rx*this._scale)
    .attr('ry', d => d.ry*this._scale)
    .attr('transform', d => d.transform)
    .attr('fill', this._colorAlg)
    .attr('display', d => this._filterAlg(d)?"block":"none")
    return ellipses;
}

Drawer.prototype.cleaner = function(tile){
    this._tiles = this._tiles.filter(item => item!=tile);
    d3.select(tile).selectAll('ellipse').on('click', null);
};

Drawer.prototype.changeEvent = function(eventAlg){
    this._eventAlg = eventAlg || this._eventAlg;
    for (let tile of this._tiles){
        d3.select(tile)
            .selectAll('ellipse')
            .on('click', this._eventAlg);
    }
};

Drawer.prototype.changeScale = function(scale){
    this._scale = scale;
    for (let tile of this._tiles){
        let tile_select = d3.select(tile);
        let data = tile_select.data()[0];
        tile_select.html('');
        this.drawer(data, tile);
    }
}
Drawer.prototype.changeColor = function(colorAlg){
    this._colorAlg = colorAlg || this._colorAlg;
    for (let tile of this._tiles){
        d3.select(tile)
            .selectAll('ellipse')
            .transition()
            .attr('fill', this._colorAlg);
        var canvas = d3.select(tile).select('canvas');
        this.drawCanvas(canvas.node().getContext('2d'), canvas.datum());
    }

};

Drawer.prototype.changeFilter = function(filterAlg){
    this._filterAlg = filterAlg || this._filterAlg;

    for (let tile of this._tiles){
        d3.select(tile)
            .selectAll('ellipse')
            .attr('display', d => this._filterAlg(d)?"block":"none");

        var canvas = d3.select(tile).select('canvas');
        this.drawCanvas(canvas.node().getContext('2d'), canvas.datum());
    }
}

Drawer.prototype.changeIntensity = function(new_intensity){
    this._intensity = new_intensity;
    // for (var i=0; i<this._tiles.length; i++){
    //     var tile = this._tiles[i];
    for (let tile of this._tiles){
        var canvas = d3.select(tile).select('canvas');

        this.drawCanvas(canvas.node().getContext('2d'), canvas.datum());
    }
}

Drawer.prototype._getEllipseData = function(item, bound){
    let rangex = bound.ramax-bound.ramin;
    let rangey = bound.decmax-bound.decmin;
    let offsetx = bound.ramin;
    let offsety = bound.decmin;


    item.cx = (item.RA-offsetx)/rangex*256;
    item.cy = (item.DEC-offsety)/rangey*256;
    item.rx = (item.A_IMAGE*0.23/3600)/rangex*256;
    item.ry = (item.B_IMAGE*0.23/3600)/rangey*256;
    item.transform = ['rotate(', item.THETA_IMAGE+90.0, item.cx, item.cy, ')'].join(' ');
    return item;
};


