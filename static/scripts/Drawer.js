var Drawer = function(colorAlg, eventAlg, tileSize){
    this._colorAlg = colorAlg || function(){return 'white'};
    this._eventAlg = eventAlg || function(){}; 
    this._tiles = [];
    tileSize = tileSize || [256, 256]; // width, height
    this._tileWidth = tileSize[0];
    this._tileHeight = tileSize[1];
    // this._bound = [0, 1, 0, 1]; //top bottom left right
}

Drawer.prototype.drawer = function(data, tile){
    this._tiles.push(tile);
    var svg = d3.select(tile).append('svg:svg')
                .attr('viewBox', '0 0 '+this._tileWidth+' '+this._tileHeight)
                .attr('height', '100%')
                .attr('width', '100%');

    var background = svg.append('rect')
                        .attr('height', this._tileHeight)
                        .attr('width', this._tileWidth)
                        .attr('x', 0)
                        .attr('y', 0)
                        .attr('fill', 'black');

    var items = data.data.map((function(item){
        return this._getEllipseData(item, data.bound);
    }).bind(this));
    
    var ellipses = this.drawEllipse(svg, items);
    // this.drawBoundary(svg, data.position);
    ellipses.on('click', this._eventAlg);
};

Drawer.prototype.drawEllipse = function(svg, items){
    
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
    item.transform = ['rotate(', item.THETA_IMAGE+90.0, item.cx, item.cy, ')'].join(' ');
    return item;
};

// Drawer.prototype.drawBoundary = function(svg, pos){
//     var x, y, z;
//     x = pos[0]; y = pos[1]; z = pos[2];
//     var size = Math.pow(2, z);
//     var top, bottom, left, right;
//     top = size*this._bound[0];
//     bottom = size*this._bound[1];
//     left = size*this._bound[2];
//     right = size*this._bound[3];
//     
//     var draw = function(x, width, y, height){
//         if (height && width){
//             svg.append('rect').classed('boundary', true)
//                 .attr('x', x).attr('y', y)
//                 .attr('height', height)
//                 .attr('width', width)
//                 .attr('fill', 'white');
//         }    
//     }
//     
//
//     var limitHeight = (function(x){
//         return Math.max(-1, Math.min(this._tileHeight+1, x));
//     }).bind(this);
//     var limitWidth = (function(x){
//         return Math.max(-1, Math.min(this._tileWidth+1, x));
//     }).bind(this);
//     
//     var x0 = limitWidth((left-x)*size*this._tileWidth);
//     var x1 = limitWidth((right-x)*size*this._tileWidth);
//     var y0 = limitHeight((top-y)*size*this._tileHeight);
//     var y1 = limitHeight((bottom-y)*size*this._tileHeight);
//     
//
//     svg.append('rect').classed('boundary', true)
//         .attr('height', y1-y0)
//         .attr('width', x1-x0)
//         .attr('x', x0)
//         .attr('y', y0)
//         .attr('fill', 'white')
//     // draw(x0, x1-x0, y0-1, 2);
//     // draw(x0, x1-x0, y1-1, 2);
//     // draw(x0-1, 2, y0, y1-y0);
//     // draw(x0-1, 2, y0, y1-y0);
//     // #<{(|
//     //  * pos is [x, y, z] components
//     //  * and svg is the tile that we would like to draw on
//     //  * thus, the bound is specified by 4 numbers 
//     //  * the bound is accessed by this._bound ([top, bottom, left, right])
//     //  * the bound would always remains only two pixels, 
//     //  * sometimes the bound could be too small to see, 
//     //  * thus, it will shrink to just one point
//     //  |)}>#
//     //
//     // var x,y,z;
//     // x = pos[0]; y = pos[1]; z = pos[2];
//     // var size = Math.pow(2, z);
//     //
//     // var top, bottom, left, right ;
//     // top = this._bound[0]*size; 
//     // bottom = this._bound[1]*size; 
//     // left = this._bound[2]*size; 
//     // right = this._bound[3]*size;
//     //
//     // var limitHeight = (function(x){
//     //     return Math.max(0, Math.min(this._tileHeight, x));
//     // }).bind(this);
//     // var limitWidth = (function(x){
//     //     return Math.max(0, Math.min(this._tileWidth, x));
//     // }).bind(this);
//     // // console.log(top, bottom, left, right, x, y);
//     // var drawRect = (function(x1, x2, y1, y2){
//     //     var xl = limitWidth((x1-x)*this._tileWidth/size);
//     //     var yt = limitHeight((y1-y)*this._tileHeight/size);
//     //     var xr = limitWidth((x2-x)*this._tileWidth/size);
//     //     var yb = limitHeight((y2-y)*this._tileWidth/size);
//     //     var width = xr-xl, height = yb-yt;
//     //     // console.log(this._bound);
//     //     console.log(xl, xr, yt, yb);        
//     //       svg.append('rect').classed('bound', true)
//     //             .attr('x', xl).attr('width', width)
//     //             .attr('y', yt).attr('height', height)
//     //             .attr('fill', 'white');
//     // }).bind(this);
//     //
//     // var strokew = 2*size/this._tileWidth; // The stoke is about 2px wide 
//     // var strokeh = 2*size/this._tileHeight; // The stoke is about 2px wide 
//     //
//     // console.log('top');
//     // drawRect(left, right, top-strokeh/2, top+strokeh/2);
//     // console.log('bottom');
//     // drawRect(left, right, bottom-strokeh/2, bottom+strokeh/2);
//     // console.log('left');
//     // drawRect(left-strokew/2, left+strokew/2, top, bottom);
//     // console.log('right');
//     // drawRect(right-strokew/2, right+strokew/2, top, bottom);
//     //
// }

//     #<{(|
//      * if the bound is not empty, it will set the bound
//      * and it will return the new bound back
//      * if it is empty, it do nothing other than 
//      * return the bound
//      * You could either pass in [top, bottom, left, right]
//      * or you could pass in an object that {top: bottom: left: right:}
//      * or any number of the argument
//      |)}>#
//     if (bound){
//         if (Array.isArray(bound)){
//             this._bound = bound;
//         }else{
//             this._bound[0] = bound.top;
//             this._bound[1] = bound.bottom;
//             this._bound[2] = bound.left;
//             this._bound[3] = bound.right;
//         }
//     }
//     return this._bound;
// }
