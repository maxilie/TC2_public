import {Injectable} from "@angular/core";
import {HealthCheckResult, HealthCheckResultStatus} from "../models/models";


@Injectable({
    providedIn: 'root'
})
export class UtilService {
    /**
     * A shared service to provide util functions like serialization/deserialization.
     */

    static monthNames = [
        "Jan", "Feb", "Mar",
        "Apr", "May", "Jun", "Jul",
        "Aug", "Sep", "Oct",
        "Nov", "Dec"
    ];

    public static encodeDate(date: Date): string {
        /**
         * Converts a Date object to a string like "2019/12/21".
         */
        return '' + date.getFullYear() + '/' + (date.getMonth() + 1) + '/' + date.getDate();
    }

    public static encodeDatetime(datetime: Date): string {
        /**
         * Converts a Date object to a string like "2019/12/21".
         */
        return '' + datetime.getFullYear() + '/' + (datetime.getMonth() + 1) + '/' + datetime.getDate()
            + '_' + datetime.getHours() + ':' + datetime.getMinutes() + ':' + datetime.getSeconds();
    }

    public static decodeDate(dateStr: string): Date | null {
        /**
         * Converts a string like "2019/12/21" to a Date object.
         */
        const comps = dateStr.split('/');
        if (comps.length != 3) {
            return null;
        }
        return new Date(+comps[0], +comps[1] - 1, +comps[2]);
    }

    public static decodeDatetime(dateStr: string | null): Date | null {
        /**
         * Converts a string like "2019/12/21_9:17:58" to a Date object.
         */
        if (dateStr == null) {
            console.log('NULL: null dateStr');
            return null;
        }

        // Split into "YYYY/MM/DD" and "HH:MM:SS"
        const datetimeComps = dateStr.split('_');
        if (datetimeComps.length != 2) {
            console.log('NULL: not 2 datetimeComps:');
            console.log(datetimeComps);
            return null;
        }

        // Split date into [year, month, day] and time into [hour, minute, second]
        const dateComps = datetimeComps[0].split('/');
        const timeComps = datetimeComps[1].split(':');
        if (dateComps.length != 3 || timeComps.length != 3) {
            console.log('NULL: not 3 dateComps or timeComps:');
            console.log(dateComps);
            console.log(timeComps);
            return null;
        }

        // Put all the components together into a Date object and return it
        return new Date(+dateComps[0], +dateComps[1] - 1, +dateComps[2], +timeComps[0], +timeComps[1], +timeComps[2]);
    }

    public static decodeHealthCheckResult(data) {
        /**
         * Converts a map like {status='PASS', msgs=['started health check...']}.
         */

            // Decode the result's status (pass or fail)
        const status = data['status'] != null && data['status'] === 'PASSED'
            ? HealthCheckResultStatus.PASSED : HealthCheckResultStatus.FAILED;

        // Decode the result's output messages
        let msgs = [];
        if (data['debug_messages'] != null) {
            msgs = data['debug_messages']
        }

        // Return the result
        return new HealthCheckResult(status, msgs);
    }

    public static formatDate(date: Date | null): string {
        /**
         * Returns a nicely-formatted date string, e.g. '___ __, ____' or 'Jan 14, 2020'.
         */
        if (date == null) {
            return '___ __, ____';
        }
        return UtilService.monthNames[date.getMonth()] + ' ' + date.getDate() + ', ' + date.getFullYear();
    }

    public static formatTime(date: Date | null): string {
        /**
         * Returns a nicely-formatted time string, e.g. '__:__' or '5:30PM (New York)'.
         */
        if (date == null) {
            return '__:__';
        }

        const suffix = date.getHours() < 12 ? 'AM (New York)' : 'PM (New York)';
        let hrs = date.getHours() >= 13 ? (date.getHours() - 12).toString() : date.getHours().toString();
        if (date.getHours() == 0) {
            hrs = '12';
        }
        return hrs + ':' + (date.getMinutes() < 10 ? '0' : '') + date.getMinutes().toString() + suffix;
    }

    public static stringifyParams(params: { [p: string]: string }): string {
        /**
         * Converts the map of params to a string like 'key=value&other_key=other_val'
         */
        if (Object.keys(params).length == 0) {
            return '';
        }
        let paramString = '';
        for (const key in params) {
            paramString = paramString + '&' + key + '=' + UtilService.urlEncode(params[key]);
        }
        return paramString.substr(1);
    }

    public static urlEncode(plainStr: string): string {
        /**
         * "Percent escapes" all reserved characters (%/!*[? etc.).
         * Logs an error if special characters (reserved chars plus A-z0-9-_.~) are present.
         */
        if (/[^%!@#$&*()=:/,;?+'A-z0-9\-_.~]/.test(plainStr)) {
            console.error('Tried to url-encode a string that contains problematic characters:');
            console.error(/[^%!@#$&*()=:/,;?+'A-z0-9\-_.~]/.exec(plainStr));
        }
        return plainStr.replace(/[%!@#$&*()=:/,;?+']/g, function (m) {
            return {
                '%': '%25',
                '!': '%21',
                '@': '%40',
                '#': '%23',
                '$': '%24',
                '&': '%26',
                '*': '%2A',
                '(': '%28',
                ')': '%29',
                '=': '%3D',
                ':': '%3A',
                '/': '%2F',
                ',': '%2C',
                ';': '%3B',
                '?': '%3F',
                '+': '%2B',
                "'": '%27',
            }[m];
        });
    }

    public static urlDecode(urlStr: string): string {
        /**
         * Decodes a string that was url encoded by the logic of UtilService.urlEncode().
         * Logs an error if non-encoded characters (not %A-z0-9-_.~) are present.
         */
        if (/[^%A-z0-9\-_.~]/.test(urlStr)) {
            console.error('Tried to url-decode a string that contains problematic characters:');
            console.error(urlStr);
        }
        return urlStr.replace(/%25|%21|%40|%23|%24|%26|%2A|%28|%29|%3D|%3A|%2F|%2C|%3B|%3F|%2B|%27,/g, function (m) {
            return {
                '%25': '%',
                '%21': '!',
                '%40': '@',
                '%23': '#',
                '%24': '$',
                '%26': '&',
                '%2A': '*',
                '%28': '(',
                '%29': ')',
                '%3D': '=',
                '%3A': ':',
                '%2F': '/',
                '%2C': ',',
                '%3B': ';',
                '%3F': '?',
                '%2B': '+',
                '%27': "'",
            }[m];
        });
    }

    getAttr(data: {}, attr: string): any | null {
        /**
         * Returns the JSON data's attribute value, or null if the data does not have the attribute.
         */
        return attr in data ? data[attr] : null;
    }
}
