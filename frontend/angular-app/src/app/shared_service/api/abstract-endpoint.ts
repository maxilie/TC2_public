import {HttpClient} from "@angular/common/http";

export class AbstractEndpoint {
    http: HttpClient;
    apiUrl: string;

    public constructor(http: HttpClient, apiUrl: string) {
        this.http = http;
        this.apiUrl = apiUrl;
    }

}
