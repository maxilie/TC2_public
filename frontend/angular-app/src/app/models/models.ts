import {UtilService} from "../shared_service/util.service";

export enum LogFeed {
    PROGRAM = 'program',
    DATA = 'data',
    LIVE_TRADING = 'live_trading',
    OPTIMIZATION = 'optimization',
    API = 'api',
    VISUALS = 'visuals'
}

export enum HealthCheckResultStatus {
    PASSED,
    FAILED
}

export class HealthCheckResult {
    /**
     * Represents the output of a health check, which includes a pass/fail status and detailed output messages.
     */

        // The status of the health check (pass or fail)
    status: HealthCheckResultStatus;

    // The debug output that gives insight into what happened while performing the health check
    msgs: string[];


    constructor(status: HealthCheckResultStatus, msgs: string[]) {
        this.status = status;
        this.msgs = msgs;
    }
}

export class PriceLine {
    /**
     * A line drawn on a price graph between two points.
     */
    public x_0: Date;
    public y_0: number;
    public x_1: Date;
    public y_1: number;
    public x_first: Date;
    public y_first: number;
    public x_last: Date;
    public y_last: number;

    constructor(x_0: Date, y_0: number, x_1: Date, y_1: number, x_first: Date, y_first: number, x_last: Date, y_last: number,) {
        this.x_0 = x_0;
        this.y_0 = y_0;
        this.x_1 = x_1;
        this.y_1 = y_1;
        this.x_first = x_first;
        this.y_first = y_first;
        this.x_last = x_last;
        this.y_last = y_last;
    }

    public static fromJson(data: {}): PriceLine | null {
        let x_0 = null;
        let y_0 = null;
        let x_1 = null;
        let y_1 = null;
        let x_first = null;
        let y_first = null;
        let x_last = null;
        let y_last = null;
        try {
            x_0 = UtilService.decodeDatetime(data['x_0']);
            if (x_0 == null) {
                throw Error();
            }
            y_0 = +data['y_0'];
            x_1 = UtilService.decodeDatetime(data['x_1']);
            if (x_1 == null) {
                throw Error();
            }
            y_1 = +data['y_1'];
            x_first = UtilService.decodeDatetime(data['x_first']);
            if (x_first == null) {
                throw Error();
            }
            y_first = +data['y_first'];
            x_last = UtilService.decodeDatetime(data['x_last']);
            if (x_last == null) {
                throw Error();
            }
            y_last = +data['y_last'];
        } catch (e) {
            return null;
        }
        return new PriceLine(x_0, y_0, x_1, y_1, x_first, y_first, x_last, y_last);
    }
}

export class MinuteCandle {
    /**
     * Contains a minute's candle data: open, high, low, close, and volume.
     */
    public minute: Date;
    public open: number;
    public high: number;
    public low: number;
    public close: number;
    public volume: number;

    constructor(minute: Date, open: number, high: number, low: number, close: number, volume: number) {
        this.minute = minute;
        this.open = open;
        this.high = high;
        this.low = low;
        this.close = close;
        this.volume = volume;
    }

    public static fromJson(data: {}): MinuteCandle | null {
        let minute = null;
        let open = null;
        let high = null;
        let low = null;
        let close = null;
        let volume = null;

        try {
            minute = UtilService.decodeDatetime(data['minute']);
            if (minute == null) {
                throw Error();
            }
            open = +data['open'];
            high = +data['high'];
            low = +data['low'];
            close = +data['close'];
            volume = +data['volume'];
        } catch (e) {
            return null;
        }
        return new MinuteCandle(minute, open, high, low, close, volume)
    }
}

export class DailyCandle {
    /**
     * Contains a day's candle data: open, high, low, close, and volume.
     */
    public day_date: Date;
    public open: number;
    public high: number;
    public low: number;
    public close: number;
    public volume: number;

    constructor(day_date: Date, open: number, high: number, low: number, close: number, volume: number) {
        this.day_date = day_date;
        this.open = open;
        this.high = high;
        this.low = low;
        this.close = close;
        this.volume = volume;
    }

    public static fromJson(data: {}): DailyCandle | null {
        let day_date = null;
        let open = null;
        let high = null;
        let low = null;
        let close = null;
        let volume = null;

        try {
            day_date = UtilService.decodeDate(data['day_date']);
            if (day_date == null) {
                throw Error();
            }
            open = +data['open'];
            high = +data['high'];
            low = +data['low'];
            close = +data['close'];
            volume = +data['volume'];
        } catch (e) {
            return null;
        }
        return new DailyCandle(day_date, open, high, low, close, volume)
    }
}

export class ModelStep {
    passed: boolean;
    value: string;
    label: string;
    info: string;

    constructor(passed: boolean, value: string, label: string, info: string) {
        this.passed = passed;
        this.value = value;
        this.label = label;
        this.info = info;
    }

    public static fromJson(data: { string: string }): ModelStep {
        return new ModelStep(data['passed'] == 'PASSED', data['value'], data['label'], data['info']);
    }
}

export class AbstractModelOutput {
    steps: ModelStep[];

    constructor(steps: ModelStep[]) {
        this.steps = steps;
    }

    public static getSteps(data: { string: string }[]): ModelStep[] | null {
        /**
         * Returns a list of ModelSteps encoded in a model output's 'steps' field.
         */
        const steps = [];
        try {
            for (const stepData of data) {
                steps.push(ModelStep.fromJson(stepData));
            }
            return steps;
        } catch (e) {
            return null;
        }
    }
}

export class Breakout1ModelOutput extends AbstractModelOutput {
    /**
     * Contains the output of Breakout1Model at a moment.
     */

    public day_date: Date;
    public status: string;
    public res_line: PriceLine | null;
    public sup_line: PriceLine | null;
    public midpoint_x: Date | null;
    public midpoint_sup_y: number | null;
    public midpoint_res_y: number | null;


    constructor(steps: ModelStep[], day_date: Date, status: string, res_line: PriceLine | null, sup_line: PriceLine | null, midpoint_x: Date | null, midpoint_sup_y: number | null, midpoint_res_y: number | null) {
        super(steps);
        this.day_date = day_date;
        this.status = status;
        this.res_line = res_line;
        this.sup_line = sup_line;
    }

    public static fromJson(data: {}): Breakout1ModelOutput | null {
        let day_date = null;
        let status = null;
        let res_line = null;
        let sup_line = null;
        let midpoint_x = null;
        let midpoint_sup_y = null;
        let midpoint_res_y = null;
        try {
            day_date = UtilService.decodeDate(data['day_date']);
            if (day_date == null) {
                throw Error();
            }
            status = data['status'];
            res_line = data['res_line'] != '' ? PriceLine.fromJson(data['res_line']) : null;
            sup_line = data['sup_line'] != '' ? PriceLine.fromJson(data['sup_line']) : null;
            midpoint_x = data['midpoint'] != '' ? UtilService.decodeDatetime(data['midpoint_x']) : null;
            midpoint_sup_y = data['midpoint_sup_y'] != '' ? +data['midpoint_sup_y'] : null;
            midpoint_res_y = data['midpoint_res_y'] != '' ? +data['midpoint_res_y'] : null;
        } catch (e) {
            return null;
        }
        return new Breakout1ModelOutput(AbstractModelOutput.getSteps(data['steps']), day_date, status, res_line, sup_line, midpoint_x, midpoint_sup_y, midpoint_res_y);
    }
}
