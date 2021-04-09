import {AbstractEndpoint} from "./abstract-endpoint";
import {Observable} from "rxjs";
import {HttpHeaders} from "@angular/common/http";
import {UtilService} from "../util.service";

export class ApiDataEndpoint extends AbstractEndpoint {
    /**
     * Class containing functionality to interact with the /api/data endpoint.
     */

    public getSymbols(): Observable<String[]> {
        /**
         * Returns a list of symbols managed by the program.
         */
        return this.http.get<String[]>(`${this.apiUrl}/symbols`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public getWarmupDays(symbol: string, date: Date): Observable<number[]> {
        /**
         * Returns a list of numbers of days of continuous data before the given date.
         */
        const params = {
            symbol: symbol,
            date: UtilService.encodeDate(date)
        };
        return this.http.get<number[]>(`${this.apiUrl}/warmup_day_options/?${UtilService.stringifyParams(params)}`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public getDatesOnFile(symbol: string): Observable<String[]> {
        /**
         * Returns a list of dates for which the symbol has data.
         */
        return this.http.get<String[]>(`${this.apiUrl}/dates/${symbol}`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public healData(): void {
        /**
         * Tells the program to run the data healing task.
         */
        this.http.get<String>(`${this.apiUrl}/heal`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            }).subscribe(() => {
        });
    }

    public resetCollectionAttempts(): void {
        /**
         * Tells the program to erase its record of which days had failed attempts at data collection.
         */
        this.http.get<String>(`${this.apiUrl}/reset_collection_attempts`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            }).subscribe(() => {
        });
    }

    public patchData(symbols: string, startDate: Date): void {
        /**
         * Tells the program to patch its stock market data.
         * @param symbols: can be one symbol or multiple comma-separated symbols
         */
        const params = {
            symbols: symbols,
            start_date: UtilService.encodeDate(startDate)
        };
        this.http.get<String>(`${this.apiUrl}/patch/?${UtilService.stringifyParams(params)}`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            }).subscribe(() => {
        });
    }

    public getDataStatus(): Observable<String> {
        /**
         * Returns the data status ("Busy" or "Not in use").
         */
        return this.http.get<String>(`${this.apiUrl}/status`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public isDataHealing(): Observable<String> {
        /**
         * Returns 'true' or 'false' depending on whether the data healing task is being run.
         */
        return this.http.get<String>(`${this.apiUrl}/is_healing`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public isDataPatching(): Observable<String> {
        /**
         * Returns 'true' or 'false' depending on whether the data patching task is being run.
         */
        return this.http.get<String>(`${this.apiUrl}/is_patching`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public getSimulationOutput(): Observable<String> {
        /**
         * Returns an empty string or a string containing the json output of the last simulation.
         */
        return this.http.get<String>(`${this.apiUrl}/get_simulation_output`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }
}
