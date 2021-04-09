import {AbstractEndpoint} from "./abstract-endpoint";
import {HttpHeaders, HttpParams} from "@angular/common/http";
import {UtilService} from "../util.service";

export class ApiVisualsEndpoint extends AbstractEndpoint {
    /**
     * Class containing functionality to interact with the /api/visuals/show endpoint.
     */

    public getVisualData(callback, params: {[p: string]: string}) {
        return this.http.get<String>(`${this.apiUrl}/get/?${UtilService.stringifyParams(params)}`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            }).subscribe(
            data => {
                callback(data);
            },
            data => {
                console.error('loading visual data received error response:');
                console.log(data)
            }
        );
    }

    public generateVisual(callback, params: {[p: string]: string}) {
        return this.http.get<String>(`${this.apiUrl}/generate/?${UtilService.stringifyParams(params)}`,
            {
                headers: new HttpHeaders().append('Authorization', `Bearer ${localStorage.getItem('token')}`)
            }).subscribe(
            () => {
                callback();
            },
            data => {
                console.error('generating visual data received error response:');
                console.log(data)
            }
        );
    }
}
