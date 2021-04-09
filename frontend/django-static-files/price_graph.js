function createPriceGraph(jsonString) {

    var parseDate = d3.timeParse("%m/%d/%Y");
    var margin = {left: 50, right: 20, top: 20, bottom: 50};

    var width = 960 - margin.left - margin.right;
    var height = 500 - margin.top - margin.bottom;


    var maxPrice = 0;

    var xNudge = 50;
    var yNudge = 20;

    var minDate = new Date();
    var maxDate = new Date();

    var rawData = JSON.parse(jsonString);
    var data = [];
    rawData.forEach(function (d) {
        let date = parseDate(d.date);
        let price = Number(d.price.trim());
        let valid_minutes = Number(d.valid_minutes.trim());
        data.push({
            date: date,
            price: price,
            valid_minutes: valid_minutes
        });
    });
    minPrice = d3.min(data, function (d) {
        return d.price;
    });
    maxPrice = d3.max(data, function (d) {
        return d.price;
    });
    minDate = d3.min(data, function (d) {
        return d.date;
    });
    maxDate = d3.max(data, function (d) {
        return d.date;
    });


    var yScale = d3.scaleLinear()
        .domain([minPrice, maxPrice])
        .range([height, 0]);

    var xScale = d3.scaleTime()
        .domain([minDate, maxDate])
        .range([0, width]);

    var yAxis = d3.axisLeft(yScale);

    var xAxis = d3.axisBottom(xScale);

    var line = d3.line()
        .x(function (d) {
            return xScale(d.date);
        })
        .y(function (d) {
            return yScale(d.price);
        });


    var svgContainer = d3.select("body").append("div").attr("width", "100%").attr("height", "100%").attr("align", "center");
    var svg = svgContainer.append("svg").attr("id", "svg").attr("height", height + margin.bottom + margin.top + yNudge + "px").attr("width", width + margin.left + margin.right + xNudge + "px");
    svg.on("dblclick", resetPriceGraph);
    var defTransform = "translate(" + xNudge + "," + yNudge + ")";
    var chartGroup = svg.append("g").attr("class", "chartGroup").attr("id", "price_graph").attr("transform", defTransform);


    chartGroup.append("path")
        .attr("class", "line")
        .attr("d", function (d) {
            return line(data);
        });

    var tooltip = d3.select("body")
        .append("div")
        .attr("id", "tooltip")
        .style("position", "absolute")
        .style("z-index", "10")
        .style("visibility", "hidden")
        .style("background-color", "hsla(0, 0%, 20%, 0.9)")
        .style("color", "#fff")
        .style("padding-right", "5px")
        .style("padding-left", "5px")
        .style("padding-top", "2px")
        .style("padding-bottom", "2px")
        .style("border-radius", "3px")
        .style("font", "arial")
        .style("pointer-events", "none")
        .text("a simple tooltip");

    chartGroup.selectAll("line-circle")
        .data(data)
        .enter().append("circle")
        .attr("class", "data-circle")
        .attr("r", 0.75)
        .attr("cx", function (d) {
            return xScale(d.date);
        })
        .attr("cy", function (d, i) {
            if (d.price < 0)
                return yScale(data[Math.max(0, i - 1)].price);
            return yScale(d.price);
        })
        .attr("fill", function (d) {
            return d.price < 0 ? "red" : "black";
        })
        .style("cursor", "crosshair")
        .on("mouseenter", function (d) {
            // Show the tooltip
            if (d.price < 0)
                tooltip.text("Missing data on " + (d.date.getMonth() + 1) + "/" + d.date.getDate() + "/" + d.date.getFullYear());
            else tooltip.text("$" + d.price.toFixed(2) + " on " + (d.date.getMonth() + 1) + "/" + d.date.getDate() + "/" + d.date.getFullYear() + " (" + d.valid_minutes + "/390 valid mins)");
            tooltip.style("visibility", "visible");
        })
        .on("mousemove", function () {
            if (event.pageX > width)
                return tooltip.style("top", (event.pageY - 10) + "px").style("left", (event.pageX - $('#tooltip').width() - 10) + "px");
            else
                return tooltip.style("top", (event.pageY - 10) + "px").style("left", (event.pageX + 10) + "px");
        })
        .on("mouseout", function () {
            tooltip.style("visibility", "hidden");
        })
        .on("mousedown", function (d) {
            // Zoom to the dot
            var x = xScale(d.date),
                y = yScale(d.price);
            var scale = 5;
            var translate = [xNudge + (width / 2) - (scale * x), -yNudge + (height / 2) - (scale * y)];

            chartGroup.transition()
                .duration(750)
                .attr("transform", "translate(" + translate + ")scale(" + scale + ")");
        });


    chartGroup.append("g")
        .attr("class", "axis x")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    chartGroup.append("g")
        .attr("class", "axis y")
        .call(yAxis);

    function resetPriceGraph() {
        chartGroup.transition()
            .duration(750)
            .attr("transform", defTransform);
    }
}