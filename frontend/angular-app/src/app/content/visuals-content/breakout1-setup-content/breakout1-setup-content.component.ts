import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../../shared_service/api/api.service";
import {Observable} from "rxjs";
import * as d3 from "d3";
import {UtilService} from "../../../shared_service/util.service";
import {Breakout1ModelOutput, MinuteCandle} from "../../../models/models";

@Component({
    selector: 'app-breakout1-setup-content',
    templateUrl: './breakout1-setup-content.component.html',
    styleUrls: ['./breakout1-setup-content.component.less'],
})

export class Breakout1SetupContentComponent implements OnInit {
    // Vars for the setup graph
    checkMoment = null;
    modelData: Breakout1ModelOutput = null;
    dayData: MinuteCandle[] = [];
    lastUpdated = null;

    // Vars for constructing the setup graph
    selectedSymbol = 'TXN';
    symbols: Observable<String[]>;
    datesOnFile: Observable<String[]>;
    checkMomentDate = '2020/1/3';
    checkMomentHour = 11;
    checkMomentMinute = 15;

    // Vars for displaying the setup graph
    refreshChecks = 0;
    maxRefreshChecks = 100;
    updating = false;
    utilService = UtilService;

    constructor(public api: ApiService) {
    }

    ngOnInit(): void {
        // Show empty graph
        this.createSetupGraph([], null);

        // Load symbols and dates
        this.symbols = this.api.getSymbols();
        this.getSymbolDatesOnFile(this.selectedSymbol);
        this.loadVisual();
        this.createSetupGraph(this.dayData, this.modelData);
    }

    public updateVisual(firstCall: boolean) {
        /**
         * Calls visual generation API endpoint and then updates local variables once the new data is available.
         */
        if (firstCall && this.updating) {
            return;
        }

        this.checkMoment = UtilService.decodeDatetime(this.constructCheckMoment());
        this.lastUpdated = null;
        this.modelData = null;
        this.dayData = [];
        this.createSetupGraph(this.dayData, this.modelData);
        const setupComp = this;

        function peek() {
            if (!setupComp.updating) {
                return;
            }

            const oldUpdateTime = setupComp.lastUpdated;

            function checkTimeLastUpdated(data) {
                // Decode the date, which might be null
                const updateTime = data == null ? null : UtilService.decodeDatetime(data['last_updated']);

                if (setupComp.refreshChecks >= setupComp.maxRefreshChecks) {
                    // Stop checking after 100 attempts
                    setupComp.updating = false;
                    setupComp.refreshChecks = 0;
                } else if (updateTime === null || updateTime <= oldUpdateTime) {
                    // Check again in 3 seconds
                    setupComp.refreshChecks += 1;
                } else if (setupComp.refreshChecks < setupComp.maxRefreshChecks) {
                    // Update visual display
                    setupComp.applyVisualData(data);
                    setupComp.updating = false;
                    setupComp.refreshChecks = 0;
                }
            }

            setupComp.api.getVisualData(checkTimeLastUpdated, {
                'visual_type': 'breakout1_setup',
                'symbol': setupComp.selectedSymbol,
                'check_moment': setupComp.constructCheckMoment()
            })
        }

        function startChecking() {
            // Check up to 100 times
            const checkerId = setInterval(peek, 3000, [false]);

            // Cancel the checker task 102 checks later
            setTimeout(() => {
                clearInterval(checkerId);
            }, 3000 * setupComp.maxRefreshChecks + 2)
        }

        if (firstCall) {
            this.updating = true;
            this.api.generateVisual(startChecking, {
                'visual_type': 'breakout1_setup',
                'symbol': setupComp.selectedSymbol,
                'check_moment': setupComp.constructCheckMoment()
            });
        }
    }

    public loadVisual() {
        /**
         * Updates local variables with price graph data.
         */
        this.checkMoment = UtilService.decodeDatetime(this.constructCheckMoment());
        this.lastUpdated = null;
        this.modelData = null;
        this.dayData = [];
        this.createSetupGraph(this.dayData, this.modelData);
        const setupComp = this;

        function callback(data) {
            if (data != null) {
                setupComp.applyVisualData(data);
            }
        }

        this.api.getVisualData(callback, {
            'visual_type': 'breakout1_setup',
            'symbol': setupComp.selectedSymbol,
            'check_moment': setupComp.constructCheckMoment()
        });
    }

    public applyVisualData(data) {
        this.lastUpdated = UtilService.decodeDatetime(data['last_updated']);
        this.modelData = Breakout1ModelOutput.fromJson(data['model_data']);
        this.dayData = [];
        for (let candleJson of data['day_data']) {
            this.dayData.push(MinuteCandle.fromJson(candleJson))
        }
        console.log(data);
        console.log(this.modelData);
        console.log(this.dayData);
        this.createSetupGraph(this.dayData, this.modelData);
    }

    public getSymbolDatesOnFile(symbol: string) {
        this.datesOnFile = this.api.getDatesOnFile(symbol);
    }

    public getMarketHours(): number[] {
        /**
         * Returns a list of hours during which the stock market is open.
         */
        const hours = [];
        for (let i = 9; i <= 15; i++) {
            hours.push(i);
        }
        return hours;
    }

    public getMarketMinutes(hour: number): number[] {
        /**
         * Returns a list of minutes during which the stock market is open for the given hour.
         */
        let start = 0;
        let end = 59;
        if (hour == 9) {
            start = 30;
        }
        if (hour == 15) {
            end = 5;
        }
        const minutes = [];
        for (let i = start; i <= end; i++) {
            minutes.push(i);
        }
        return minutes;
    }

    public constructCheckMoment(): string {
        /**
         * Combines date, hour, minute into a string to be passed to the django API as 'check_moment'.
         */
        const date = UtilService.decodeDate(this.checkMomentDate);
        const moment = new Date(date.getFullYear(), date.getMonth() - 1, date.getDate(), this.checkMomentHour, this.checkMomentMinute);
        return UtilService.encodeDatetime(moment);
    }

    public createSetupGraph(dayData: MinuteCandle[], modelData: Breakout1ModelOutput | null) {
        let maxPrice: number;

        let minDate: Date;
        let maxDate: Date;

        const minPrice = d3.min(dayData, function (candle) {
            return candle.low;
        });
        maxPrice = d3.max(dayData, function (candle) {
            return candle.high;
        });
        minDate = d3.min(dayData, function (candle) {
            return candle.minute;
        });
        maxDate = d3.max(dayData, function (candle) {
            // Add one minute so that 4PM is displayed on the axis
            return new Date(candle.minute.getTime() + 1000 * 60);
        });

        const yScale = d3.scaleLinear()
            .domain([minPrice, maxPrice])
            .range([48, 4]);

        const xScale = d3.scaleTime()
            .domain([minDate, maxDate])
            .range([2, 113]);

        const yAxis = d3.axisLeft(yScale)
            .tickSize(2);

        const xAxis = d3.axisBottom(xScale)
            .tickSize(2);

        const supLineData = [{
            x: 0,
            y: 0
        }, {
            x: 0,
            y: 0
        }];
        if (modelData != null && modelData.sup_line != null) {
            supLineData[0].x = xScale(modelData.sup_line.x_first);
            supLineData[0].y = yScale(modelData.sup_line.y_first);
            supLineData[1].x = xScale(modelData.sup_line.x_last);
            supLineData[1].y = yScale(modelData.sup_line.y_last);
        }

        const resLineData = [{
            x: 0,
            y: 0
        }, {
            x: 0,
            y: 0
        }];
        if (modelData != null && modelData.res_line != null) {
            resLineData[0].x = xScale(modelData.res_line.x_first);
            resLineData[0].y = yScale(modelData.res_line.y_first);
            resLineData[1].x = xScale(modelData.res_line.x_last);
            resLineData[1].y = yScale(modelData.res_line.y_last);
        }

        const line = d3.line()
            .x(function (d) {
                // @ts-ignore
                return d.x;
            })
            .y(function (d) {
                // @ts-ignore
                return d.y;
            });

        const zoom = d3.zoom();

        const svg = d3.select("#svg")
            .style("display", "block");
        svg.call(zoom.on("zoom", function () {
            svg.attr("transform", d3.event.transform)
        }))
            .on("dblclick", resetGraph)
            .on("dblclick.zoom", null);
        const defTransform = "translate(17,2)scale(1.7)";
        const priceGraph = svg.select("#price-graph")
            .attr("transform", defTransform);
        priceGraph.selectAll("*").remove();
        // @ts-ignore
        $("#price-graph").empty();

        // Draw support line
        priceGraph.append("path")
            .attr("class", "support-line")
            .style("fill", "none")
            .style("stroke", "red")
            .style("stroke-width", "0.3%")
            .attr("d", function () {
                // @ts-ignore
                return line(supLineData);
            });

        // Draw resistance line
        priceGraph.append("path")
            .attr("class", "resistance-line")
            .style("fill", "none")
            .style("stroke", "green")
            .style("stroke-width", "0.3%")
            .attr("d", function () {
                // @ts-ignore
                return line(resLineData);
            });

        const tooltip = svg.select("#tooltip")
            .style("position", "absolute")
            .style("z-index", "10")
            .style("visibility", "hidden")
            .style("background-color", "hsla(0, 0%, 20%, 0.9)")
            .style("color", "#fff")
            .style("padding-right", "0.1em")
            .style("padding-left", "0.1em")
            .style("padding-top", "0.05em")
            .style("padding-bottom", "0.05em")
            .style("border-radius", "0.07em")
            .style("font", "arial")
            .style("pointer-events", "none")
            .text("a simple tooltip");

        priceGraph.selectAll("line-circle")
            .data(dayData)
            .enter().append("circle")
            .attr("class", "data-circle")
            .attr("r", '0.25%')
            .attr("cx", function (candle) {
                return xScale(candle.minute);
            })
            .attr("cy", function (candle, i) {
                if (candle.open < 0)
                    return yScale(dayData[Math.max(0, i - 1)].open);
                return yScale(candle.open);
            })
            .attr("fill", function (candle) {
                if (candle.open <= 0) {
                    return "red";
                }
                if (modelData == null || modelData.sup_line == null || modelData.res_line == null) {
                    return "black";
                }
                if (Math.abs(candle.minute.getTime() - modelData.sup_line.x_0.getTime()) < 3000 ||
                    Math.abs(candle.minute.getTime() - modelData.sup_line.x_1.getTime()) < 3000) {
                    return "red";
                }
                if (Math.abs(candle.minute.getTime() - modelData.res_line.x_0.getTime()) < 3000 ||
                    Math.abs(candle.minute.getTime() - modelData.res_line.x_1.getTime()) < 3000) {
                    return "green";
                }
                return "black";
            })
            .style("cursor", "crosshair")
            .on("mouseenter", function (candle) {
                // Show the tooltip
                if (candle.open < 0)
                    tooltip.text("Missing data during " + (candle.minute.getHours()) + ":" + candle.minute.getMinutes());
                else tooltip.text("$" + candle.open.toFixed(2) + " at " + (candle.minute.getHours()) + ":" + candle.minute.getMinutes());
                tooltip.style("visibility", "visible");
            })
            .on("mousemove", function () {
                // @ts-ignore
                // noinspection JSDeprecatedSymbols
                return tooltip.style("top", (event.pageY - 10) + "px").style("left", (event.pageX + 10) + "px");
            })
            .on("mouseout", function () {
                tooltip.style("visibility", "hidden");
            })
            .on("mousedown", function (candle) {
                // Zoom to the dot
                const x = xScale(candle.minute),
                    y = yScale(candle.open);
                const scale = 5;
                const translate = [(50 - (scale * x)), (50 - (scale * y))];

                priceGraph.transition()
                    .duration(750)
                    .attr("transform", "translate(" + translate + ")scale(" + scale + ")");
            });


        priceGraph.append("g")
            .attr("class", "axis-x")
            .attr("transform", "translate(0, 48)")
            .style("stroke-width", "0.2%")
            .style("font-size", "10%")
            .call(xAxis);

        priceGraph.append("g")
            .attr("class", "axis-y")
            .style("stroke-width", "0.2%")
            .style("font-size", "12%")
            .call(yAxis);

        function resetGraph() {
            priceGraph.transition()
                .duration(750)
                .attr("transform", defTransform);
        }
    }
}
