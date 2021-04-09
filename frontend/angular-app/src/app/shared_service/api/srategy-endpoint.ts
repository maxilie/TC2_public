import {AbstractEndpoint} from "./abstract-endpoint";
import {Observable} from "rxjs";
import {HttpHeaders} from "@angular/common/http";
import {UtilService} from "../util.service";

export class ApiStrategyEndpoint extends AbstractEndpoint {
    /**
     * Class containing functionality to interact with the /api/strategy endpoint.
     */

    public getDayStrategies(): Observable<String[]> {
        /**
         * Returns a list of day-trading strategies available to the program.
         */
        return this.http.get<String[]>(`${this.apiUrl}/get_day_strategies`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public isRunningSimulation(): Observable<String> {
        /**
         * Returns 'true' or 'false' depending on whether the program is running a user-initiated simulation.
         */
        return this.http.get<String>(`${this.apiUrl}/is_running_simulation`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public simulateDayStrategy(symbol: string, strategyId: string, moment: string, warmup_days: number): void {
        /**
         * Signals the program to simulate a day trading strategy.
         */
        const params = {
            symbol: symbol,
            strategy_id: strategyId,
            moment: moment,
            warmup_days: '' + warmup_days
        };
        this.http.get<String[]>(`${this.apiUrl}/simulate_day_strategy/?${UtilService.stringifyParams(params)}`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            }).subscribe(() => {
        });
    }
}
