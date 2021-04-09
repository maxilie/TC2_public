function createRunHistoryGraph(jsonString) {

    var parseTime = d3.timeParse("%m/%d/%Y_%H:%M%S");
    var margin = {left: 50, right: 20, top: 20, bottom: 50};

    var width = 960 - margin.left - margin.right;
    var height = 500 - margin.top - margin.bottom;


    var xNudge = 40;
    var yNudge = 15;

    var minDate = new Date();
    var maxDate = new Date();

    var rawData = JSON.parse(jsonString);
    var data = [];
    rawData.forEach(function (d_raw) {
        let startTime = parseTime(d_raw.start_time);
        let endTime = parseTime(d_raw.end_time);
        let buyTime = d_raw.buy_time.trim() === "" ? null : parseTime(d_raw.buy_time);
        let buyPrice = d_raw.buy_price.trim() === "" ? null : Number(d_raw.buy_price.trim());
        let sellPrice = d_raw.sell_price.trim() === "" ? null : Number(d_raw.sell_price.trim());
        let profit = sellPrice == null ? 0 : 100.0 * (sellPrice - buyPrice) / sellPrice;
        data.push({
            startTime: startTime,
            endTime: endTime,
            buyTime: buyTime,
            buyPrice: buyPrice,
            sellPrice: sellPrice,
            profit: profit
        });
    });
    minProfit = d3.min(data, function (d) {
        return d.profit;
    });
    maxProfit = d3.max(data, function (d) {
        return d.profit;
    });
    minDate = d3.min(data, function (d) {
        return d.startTime;
    });
    maxDate = d3.max(data, function (d) {
        return d.startTime;
    });


    var yScale = d3.scaleLinear()
        .domain([minProfit, maxProfit])
        .range([height, 0]);

    var xScale = d3.scaleTime()
        .domain([minDate, maxDate])
        .range([0, width]);

    var yAxis = d3.axisLeft(yScale);

    var xAxis = d3.axisBottom(xScale);


    var svgContainer = d3.select("body").append("div").attr("width", "100%").attr("height", "100%").attr("align", "center");
    var svg = svgContainer.append("svg").attr("id", "svg").attr("height", height + margin.bottom + margin.top + yNudge + "px").attr("width", width + margin.left + margin.right + xNudge + "px");
    svg.on("dblclick", resetGraph);
    var defTransform = "translate(" + xNudge + "," + yNudge + ")";
    var chartGroup = svg.append("g").attr("class", "chartGroup").attr("id", "run_history_graph").attr("transform", defTransform);

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
        .attr("r", 1)
        .attr("cx", function (d) {
            return xScale(d.startTime);
        })
        .attr("cy", function (d, i) {
            return yScale(d.profit);
        })
        .attr("fill", function (d) {
            return Math.abs(d.profit) < 0.0001 ? "gray" :
                d.profit < 0 ? "red" : "green";
        })
        .style("cursor", "crosshair")
        .on("mouseenter", function (d) {
            // Show the tooltip
            if (Math.abs(d.profit) < 0.0001)
                tooltip.text("Failed to buy at " + (d.startTime.getTwelveHours()) + ":" + (d.startTime.getMinutes())
                    + ":" + (d.startTime.getSeconds()) + " on " + (d.startTime.getMonth() + 1) + "/" + d.startTime.getDate() + "/" + d.startTime.getFullYear());
            else if (d.profit > 0)
                tooltip.text("Made " + d.profit.toFixed(2) + " at " + (d.startTime.getTwelveHours()) + ":" + (d.startTime.getMinutes())
                    + ":" + (d.startTime.getSeconds()) + " on " + (d.startTime.getMonth() + 1) + "/" + d.startTime.getDate() + "/" + d.startTime.getFullYear()
                    + "%  (bought: $" + d.buyPrice.toFixed(2) + ";  sold: $" + d.sellPrice.toFixed(2) + ")");
            else
                tooltip.text("Lost " + d.profit.toFixed(2) + " at " + (d.startTime.getTwelveHours()) + ":" + (d.startTime.getMinutes())
                    + ":" + (d.startTime.getSeconds()) + " on " + (d.startTime.getMonth() + 1) + "/" + d.startTime.getDate() + "/" + d.startTime.getFullYear()
                    + "%  (bought: $" + d.buyPrice.toFixed(2) + ";  sold: $" + d.sellPrice.toFixed(2) + ")");
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
            var x = xScale(d.startTime),
                y = yScale(d.profit);
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

    function resetGraph() {
        chartGroup.transition()
            .duration(750)
            .attr("transform", defTransform);
    }
}