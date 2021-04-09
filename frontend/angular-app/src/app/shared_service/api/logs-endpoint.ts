import {AbstractEndpoint} from "./abstract-endpoint";
import {Observable} from "rxjs";
import {HttpHeaders} from "@angular/common/http";
import {LogFeed} from "../../models/models";

export class ApiLogsEndpoint extends AbstractEndpoint {
    /**
     * Class containing functionality to interact with the /api/logs endpoint.
     */

    public getFileLines(logfeed: LogFeed, filename: string): Observable<String[]> {
        /**
         * Returns log messages from the given logfile.
         */
        filename = logfeed + '/' + filename;
        return this.http.get<String[]>(`${this.apiUrl}/logfile/?filename=${filename}`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public getFeedLatestLines(logfeed: LogFeed): Observable<String[]> {
        /**
         * Returns log messages from the most recent file in the given logfeed.
         */
        return this.http.get<String[]>(`${this.apiUrl}/latest/?logfeed=${logfeed.toString()}`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public getFeedFiles(logfeed: LogFeed): Observable<String[]> {
        /**
         * Returns a list of filenames saved by the logfeed.
         */
        return this.http.get<String[]>(`${this.apiUrl}/logfeed_filenames/?logfeed=${logfeed.toString()}`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            });
    }

    public clearLogs(): void {
        /**
         * Deletes all logs on all logfeeds.
         */
        this.http.get<String[]>(`${this.apiUrl}/delete`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            }).subscribe(() => {
        });
    }
}
