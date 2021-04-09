import {AbstractEndpoint} from "./abstract-endpoint";
import {HttpHeaders} from "@angular/common/http";
import {UtilService} from "../util.service";

export class ApiHealthChecksEndpoint extends AbstractEndpoint {
    /**
     * Class containing functionality to interact with the /api/health_checks endpoint.
     */

    public performHealthCheck(callback, params: { [p: string]: string }) {
        return this.http.get<String>(`${this.apiUrl}/perform/?${UtilService.stringifyParams(params)}`, {
            headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
        }).subscribe(
            () => {
                callback();
            },
            data => {
                console.error('performing health check received error response:');
                console.log(data)
            }
        );
    }

    public getHealthCheckData(callback, params: { [p: string]: string }) {
        return this.http.get<String>(`${this.apiUrl}/get/?${UtilService.stringifyParams(params)}`, {
            headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
        }).subscribe(
            data => {
                callback(data);
            },
            data => {
                console.error('loading health check result received error response:');
                console.log(data)
            }
        );
    }
}
