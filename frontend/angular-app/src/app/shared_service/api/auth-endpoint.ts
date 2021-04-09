import {AbstractEndpoint} from "./abstract-endpoint";
import {HttpHeaders} from "@angular/common/http";

export class ApiAuthEndpoint extends AbstractEndpoint {
    /**
     * Class containing functionality to interact with the /api/token endpoint.
     */

        // Duration the auth token is valid for; must match with the corresponding Django setting
    TOKEN_VALID_FOR = 60 * 60 * 24;

    // Username variable linked to the username box
    username = '';

    // Password variable linked to the password box
    password = '';

    // Error messages received from the login attempt
    public errorText: string;

    public static getTokenExpiration(): Date {
        /**
         * Returns the moment when the user's authentication token will expire.
         */
        const tokenExpiration = localStorage.getItem('tokenExpiration');
        return new Date(JSON.parse(tokenExpiration));
    }

    public static isAuthenticated(): boolean {
        /**
         * Returns true if the user has a valid, unexpired authentication token.
         */
        return localStorage.getItem('token') != null
            && ApiAuthEndpoint.getTokenExpiration().getTime() > new Date(new Date().getTime() - (5 * 1000)).getTime();
    }

    public login(successCallback) {
        /**
         * Gets an auth token from django and calls successCallback() upon completion.
         */
        this.http.post(`${this.apiUrl}/new`, JSON.stringify({
            username: this.username,
            password: this.password
        }), {
            headers: new HttpHeaders()
                .append('Authorization', `Bearer ${localStorage.getItem('token')}`)
                .append('Content-Type', 'application/json')
        }).subscribe(
            data => {
                this.password = '';
                this.updateData(data['access']);
                this.errorText = null;

                successCallback();
            },
            data => {
                this.password = '';
                console.log('auth token request received error response:');
                this.errorText = data['statusText']
            }
        );
    }

    public static logout() {
        localStorage.setItem('token', null);
        localStorage.setItem('tokenExpiration', null);
    }

    private updateData(token) {
        localStorage.setItem('token', token);
        localStorage.setItem('tokenExpiration', JSON.stringify(
            new Date(new Date().getTime() + (1000 * this.TOKEN_VALID_FOR)).getTime()));
    }
}
