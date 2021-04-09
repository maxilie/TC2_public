function createPriceSpreadChart(jsonString) {
    var rawData = JSON.parse(jsonString);
    var data = [];

    rawData.forEach(function (d) {
        data.push({
            name: d.name,
            frequency: Number(d.frequency.trim())
        });
    });


    var svg = d3.select("svg"),
        width = +svg.attr("width"),
        height = +svg.attr("height"),
        totalBins = 6,
        binWidth = width / (totalBins * 1.3);

    var binNumber = 0;
    data.forEach(function (bin) {

        var binX = binNumber * (width / totalBins);
        var freqPct = bin.frequency / 60.0;
        var binHeight = (height / 100) * (freqPct * 100);
        var bottom = 300;

        svg.append("rect")
            .attr("x", binX)
            .attr("y", bottom - binHeight)
            .attr("width", binWidth)
            .attr("height", binHeight)
            .attr("fill", "gray");

        svg.append("text")
            .attr("x", binX)
            .attr("dx", (binNumber == 0 || binNumber == 5) ? binWidth / 3 : binWidth / 5)
            .attr("y", bottom)
            .attr("dy", "0.85em")
            .attr("font", "14px sans-serif")
            .attr("font-weight", "800")
            .text(bin.name);

        svg.append("text")
            .attr("x", binX)
            .attr("dx", binWidth / 3)
            .attr("y", Math.min(bottom - (height / 100) * 3, bottom - binHeight + 7))
            .attr("dy", ".75em")
            .attr("fill", "white")
            .attr("font", "10px sans-serif")
            .text(bin.frequency + " days");

        binNumber = binNumber + 1;
    });
}