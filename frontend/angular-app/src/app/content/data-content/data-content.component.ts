import {Component} from '@angular/core';
import {ApiService} from "../../shared_service/api/api.service";
import {Observable} from "rxjs";


@Component({
    selector: 'app-data-content',
    templateUrl: './data-content.component.html',
    styleUrls: ['./data-content.component.less'],
})

export class DataContentComponent {
    symbolToPatch = 'TXN';
    startDate = new Date(new Date().getTime() - (1000 * 60 * 60 * 24 * 400));
    symbols$: Observable<String[]>;
    dataStatus = 'Fetching status...';
    dataHealing = true;
    dataPatching = true;
    saveTime = true;
    dateOptions = [this.startDate];

    constructor(private api: ApiService) {
        this.dateOptions = this.getDates();
    }

    ngOnInit(): void {
        // Fetch symbols available
        this.symbols$ = this.api.getSymbols();
        this.updateStatus();

        // Update the data status text every 3 seconds
        const dataComp = this;
        setInterval(() => {
            dataComp.updateStatus();
        }, 3000);
    }

    public getDates(): Date[] {
        /**
         * Returns a list of dates from 1-1-2017 to yesterday.
         */
        let dates = [];

        const oneDay = 1000 * 60 * 60 * 24;
        const oneMonth = oneDay * 30;
        const currentTime = new Date();
        let dayDate = new Date(2017, 0, 1);

        try {
            let tmp = 0;
            while (dayDate.getTime() <= currentTime.getTime() - oneDay && tmp < 499) {
                dates.push(dayDate);
                if (currentTime.getTime() - dayDate.getTime() < oneMonth) {
                    dayDate = new Date(dayDate.getTime() + oneDay)
                } else {
                    dayDate = new Date(dayDate.getTime() + oneMonth)
                }
                tmp += 1;
            }
        } catch (e) {
            console.error(e);
        }
        return dates;
    }

    public healData(): void {
        /**
         * Tells the program to run its data healing operation.
         */
        if (!this.dataHealing) {
            if (!this.saveTime) {
                this.api.resetCollectionAttempts()
            }
            this.api.healData();
        }
    }

    public patchData(): void {
        /**
         * Uses this class's symbol and date variables to request that the API patch price data.
         */
        if (!this.dataPatching) {
            this.api.patchData(this.symbolToPatch, this.startDate);
        }
    }

    private updateStatus(): void {
        /**
         * Updates the dataStatus, dataHealing, and dataPatching variables with latest API response.
         */
        this.api.getDataStatus().subscribe((result) => {
            this.dataStatus = <string>result;
        });

        this.api.isDataHealing().subscribe((result) => {
            this.dataHealing = result.toLowerCase() == 'true';
        });

        this.api.isDataPatching().subscribe((result) => {
            this.dataPatching = result.toLowerCase() == 'true';
        });
    }
}
