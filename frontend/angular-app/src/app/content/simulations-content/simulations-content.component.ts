import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../shared_service/api/api.service";
import {Observable} from "rxjs";
import {UtilService} from "../../shared_service/util.service";


@Component({
    selector: 'app-simulations-content',
    templateUrl: './simulations-content.component.html',
    styleUrls: ['./simulations-content.component.less'],
})

export class SimulationsContentComponent implements OnInit {
    // List of available strategies
    strategies$: Observable<String[]>;
    // Strategy id selected from the dropdown
    selectedStrategy = 'CycleStrategy';
    // List of available symbols
    symbols$: Observable<String[]>;
    // Symbol selected from the dropdown
    selectedSymbol = 'TXN';
    // List of available dates
    dates: Date[];
    // Date selected from the dropdown
    selectedDate = new Date(new Date().getTime() - (1000 * 60 * 60 * 24 * 2));
    // Hour selected from the dropdown
    selectedHour = 11;
    // Minute selected from the dropdown
    selectedMinute = 15;
    // List of available warm-up period lengths
    warmupDays = [0];
    // Warm-up period length selected from the dropdown
    warmupSelected = 30;
    // Whether or not the program is busy running a simulation
    simulationRunning = true;
    // Output of the most recent simulation
    outputWaitingMsg = 'Waiting for simulation results...';
    simulationOutput = this.outputWaitingMsg;
    // Util reference for use in HTML
    utilService = UtilService;

    constructor(private api: ApiService) {
    }

    ngOnInit(): void {
        // Fetch strategies
        this.strategies$ = this.api.getDayStrategies();

        // Fetch symbols available
        this.symbols$ = this.api.getSymbols();

        // Fetch dates and select the earliest one
        this.fetchDates(this.selectedSymbol);

        // Update the simulation status and output text every 3 seconds
        const comp = this;
        setInterval(() => {
            comp.updateStatus();
            comp.updateOutput();
        }, 3000);
    }

    private selectDate(selectedDate: Date | null) {
        /**
         * Selects the date from the dropdown and refreshes warmup day options.
         */
        try {
            this.selectedDate = selectedDate;
            this.warmupDays = [0];
            this.warmupSelected = 0;
            this.api.getWarmupDays(this.selectedSymbol, this.selectedDate)
                .subscribe((warmupDayOptions: number[]) => {
                    this.warmupDays = warmupDayOptions;
                });
        } catch (e) {
            if (selectedDate != null) {
                console.error(e);
            }
        }
    }

    private fetchDates(symbol: string) {
        this.dates = [];

        // Fetch list of string dates
        this.api.getDatesOnFile(symbol).subscribe((dateStrs) => {
            // Convert date strings to Date objects
            this.dates = [];
            for (let dateStr of dateStrs) {
                try {
                    this.dates.push(UtilService.decodeDate(<string>dateStr));
                } catch (e) {
                    console.error('Error parsing symbol\'s date on file:');
                    console.error(dateStr);
                    console.error(e);
                }
            }

            // Select a date in the middle
            if (this.dates.length >= 2) {
                this.selectDate(this.dates[this.dates.length / 2]);
            }
            this.selectedDate = this.dates.length < 2 ? null : this.dates[this.dates.length / 2]
        });


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

    public constructMomentString(): string {
        /**
         * Combines date, hour, minute into a string to be passed to the django API as 'check_moment'.
         */
        const date = this.selectedDate;
        const moment = new Date(date.getFullYear(), date.getMonth() - 1, date.getDate(), this.selectedHour, this.selectedMinute);
        return UtilService.encodeDatetime(moment);
    }

    private runSimulation(): void {
        /**
         * Runs a simulation using the selectedStrategy, selectedSymbol, etc. variables.
         * When simulation completes, updates the results displayed on the webpage.
         */
        this.api.simulateDayStrategy(this.selectedSymbol, this.selectedStrategy, this.constructMomentString(), this.warmupSelected)
    }

    private updateStatus(): void {
        /**
         * Updates the simulationRunning variable with latest API response.
         */
        this.api.isRunningSimulation().subscribe((result) => {
            this.simulationRunning = result.toLowerCase() == 'true';
        });
    }

    private updateOutput(): void {
        /**
         * Updates the output text with the json output of the simulation.
         */
        this.api.getSimulationOutput().subscribe((result) => {
            this.simulationOutput = result.length > 5 ? <string>result : this.outputWaitingMsg;
        });
    }
}
