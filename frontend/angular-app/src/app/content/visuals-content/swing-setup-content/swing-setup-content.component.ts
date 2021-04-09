import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../../shared_service/api/api.service";
import {Observable} from "rxjs";
import * as d3 from "d3";
import {UtilService} from "../../../shared_service/util.service";

@Component({
    selector: 'app-swing-setup-content',
    templateUrl: './swing-setup-content.component.html',
    styleUrls: ['./swing-setup-content.component.less'],
})

export class SwingSetupContentComponent implements OnInit {
    selectedSymbol = 'TXN';
    symbols: Observable<String[]>;
    lastUpdated = null;
    jsonDataStr: string;
    validDays = 0;
    totalDays = 0;
    refreshChecks = 0;
    updating = false;
    utilService = UtilService;

    dataPrinted = false;

    constructor(public api: ApiService) {
    }

    ngOnInit(): void {
        this.symbols = this.api.getSymbols();
        this.loadVisual();
    }

    public refreshVisual(firstCall: boolean) {
        /**
         * Calls update and then updates local variables once the new data is available.
         */
        if (firstCall && this.updating) {
            return;
        }

        const setupComp = this;

        function peek() {
            if (!setupComp.updating) {
                return;
            }

            const oldUpdateTime = setupComp.lastUpdated;

            function checkTimeLastUpdated(data) {
                // Decode the date, which might be null
                const updateTime = data == null ? null : UtilService.decodeDatetime(data['last_updated']);

                if (setupComp.refreshChecks >= 20) {
                    // Stop checking after 20 attempts
                    setupComp.updating = false;
                    setupComp.refreshChecks = 0;
                } else if (updateTime === null || updateTime <= oldUpdateTime) {
                    // Check again in 3 seconds
                    setupComp.refreshChecks += 1;
                } else if (setupComp.refreshChecks < 20) {
                    // Update visual display
                    setupComp.applyVisualData(data);
                    setupComp.updating = false;
                    setupComp.refreshChecks = 0;
                }
            }

            setupComp.api.getVisualData(checkTimeLastUpdated, {
                'visual_type': 'price_graph',
                'symbol': setupComp.selectedSymbol
            })
        }

        function startChecking() {
            // Check up to 20 times
            const checkerId = setInterval(peek, 3000, [false]);

            // Cancel the checker task 22 checks later
            setTimeout(() => {
                clearInterval(checkerId);
            }, 3000 * 22)
        }

        if (firstCall) {
            this.updating = true;
            this.api.generateVisual(startChecking, {
                'visual_type': 'price_graph',
                'symbol': setupComp.selectedSymbol
            });
        }
    }


    public loadVisual() {
        /**
         * Updates local variables with price graph data.
         */
        const setupComp = this;

        function callback(data) {
            setupComp.applyVisualData(data);
        }

        this.api.getVisualData(callback, {
            'visual_type': 'price_graph',
            'symbol': setupComp.selectedSymbol
        });
    }

    public applyVisualData(data) {
        // TODO Modify according to JSON from the backend
        this.jsonDataStr = data['price_graph_data'].replace(new RegExp('&quot;', 'g'), '"');
        this.validDays = data['valid_days'];
        this.totalDays = data['total_days'];
        const lastUpdated = UtilService.decodeDatetime(data['last_updated']);
        this.lastUpdated = lastUpdated != null ? lastUpdated : new Date(2000, 1, 1);
        if (!this.dataPrinted) {
            console.log(this.jsonDataStr);
        }
        this.createGraph();
    }

    public createGraph() {

        const parseDate = d3.timeParse("%m/%d/%Y");
        const margin = {left: 5, right: 2, top: 2, bottom: 5};

        const width = 1000 - margin.left - margin.right;
        const height = 300 - margin.top - margin.bottom;


        let maxPrice: number;

        const xNudge = 0;
        const yNudge = 0;

        let minDate: Date;
        let maxDate: Date;

        // TODO Modify according to JSON from the backend
        const rawData = JSON.parse(this.jsonDataStr);
        let data = [];
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
        const minPrice = d3.min(data, function (d) {
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


        const yScale = d3.scaleLinear()
            .domain([minPrice, maxPrice])
            .range([height, 0]);

        const xScale = d3.scaleTime()
            .domain([minDate, maxDate])
            .range([0, width]);

        const yAxis = d3.axisLeft(yScale);

        const xAxis = d3.axisBottom(xScale);

        const line = d3.line()
        //.curve(d3.curveBasis)
            .x(function (d) {
                // @ts-ignore
                return xScale(d.date);
            })
            .y(function (d) {
                // @ts-ignore
                return yScale(d.price);
            });


        const svgContainer = d3.select("#svgContainer");
        const svg = svgContainer.select("#svg").attr("height", height + margin.bottom + margin.top + yNudge + "px").attr("width", width + margin.left + margin.right + xNudge + "px");
        svg.on("dblclick", resetGraph);
        const defTransform = "translate(" + xNudge + "," + yNudge + ")";
        const chartGroup = svg.select("#price-graph").attr("class", "chartGroup").attr("transform", defTransform);
        chartGroup.selectAll("*").remove();
        // @ts-ignore
        $("#price-graph").empty();

        chartGroup.append("path")
            .attr("class", "line")
            .style("fill", "none")
            .style("stroke", "deepskyblue")
            .style("stroke-width", "0.3em")
            .attr("d", function () {
                return line(data);
            });

        const tooltip = d3.select("#tooltip")
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
                return d.price <= 0 ? "red" : "black";
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
                // @ts-ignore
                // noinspection JSDeprecatedSymbols
                if (event.pageX > width) { // @ts-ignore
                    // @ts-ignore
                    // noinspection JSDeprecatedSymbols
                    return tooltip.style("top", (event.pageY - 10) + "px").style("left", (event.pageX - $('#tooltip').width() - 10) + "px");
                } else { // @ts-ignore
                    // @ts-ignore
                    // noinspection JSDeprecatedSymbols
                    return tooltip.style("top", (event.pageY - 10) + "px").style("left", (event.pageX + 10) + "px");
                }
            })
            .on("mouseout", function () {
                tooltip.style("visibility", "hidden");
            })
            .on("mousedown", function (d) {
                // Zoom to the dot
                const x = xScale(d.date),
                    y = yScale(d.price);
                const scale = 5;
                const translate = [xNudge + (width / 2) - (scale * x), -yNudge + (height / 2) - (scale * y)];

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
}
