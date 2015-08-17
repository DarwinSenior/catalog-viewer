/*
 * A boundary layer for Leaflet map,
 * @constuctor
 * @param leaflet
 * @param {Object} bound the bound including {top, bottom, left, right}, domain [0,1]
 * @param {String} color the color of the bound, CSS color representation
 */
var BoundLayer = function(leafletmap, bound, color){
    this.color = color || '#90A4AE'; // the boundary color 
    d3.select(leafletmap.getPanes().overlayPane).style({'pointer-events': 'none'});
    this.svg = d3.select(leafletmap.getPanes().overlayPane).append('svg:svg');
    this.map = leafletmap;
    this.g = this.svg.append('g').classed('leaflet-zoom-hide', true);

    this._bound = bound || {decmin: 0, decmax:0, ramin:0, ramax:0,};
    leafletmap.on('viewreset', this.reset.bind(this));
    
    leafletmap.on('zoomend', this.reset.bind(this));

    this.g.append('rect').classed('bound', true);
    this.reset();
}



BoundLayer.prototype.reset = function(){
    // console.log("reset!");

    var z = this.map.getZoom();    
    var size = Math.pow(2, z);
    var topleft = this.map.latLngToLayerPoint([this._bound.decmin, this._bound.ramin]);
    var bottomright = this.map.latLngToLayerPoint([this._bound.decmax, this._bound.ramax]);
    var top = topleft.y ;
    var bottom = bottomright.y;
    var left = topleft.x;
    var right = bottomright.x;
    // var top = this._bound.top*256*size-origin.y;
    // var bottom = this._bound.bottom*256*size-origin.y;
    // var left = this._bound.left*256*size-origin.x;
    // var right = this._bound.right*256*size-origin.x;

    this.svg
        .attr('width', right-left) 
        .attr('height', bottom-top)
        .style('left', left+'px')
        .style('top', top+'px');

    this.g
        .attr('transform', 'translate('+(-left)+','+(-top)+')');
        
    this.g.select('rect.bound')
        .attr('x', left)
        .attr('y', top)
        .attr('width', right-left)
        .attr('height', bottom-top)
        .attr('stroke', this.color)
        .attr('stroke-width', 2)
        .attr('fill', 'transparent');
    
}

BoundLayer.prototype.color = function(color){
    if (color){
        this.color = color || this.color;
    }
    return color;
}

/*
 * if no argument, does not return
 * @param {Object} bound {top, bottom, left, right}, between [0,1]
 * @returns {Object} the bound, reference, do not modify
 */
BoundLayer.prototype.bound = function(bound){

    if (bound){
        this._bound.ramax = bound.ramax || this._bound.ramax;
        this._bound.decmin = bound.decmin || this._bound.decmin;
        this._bound.decmax = bound.decmax || this._bound.decmax;
        this._bound.ramin = bound.ramin || this._bound.ramin;
    }

    return this._bound;
}







