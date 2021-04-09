import {Component, OnInit} from '@angular/core';
import {UtilService} from "../../shared_service/util.service";
import {HealthCheckResult, HealthCheckResultStatus} from "../../models/models";
import {ApiService} from "../../shared_service/api/api.service";

enum HealthCheckType {
    // These ids correspond to the check_name's from the README, adjusted to be in standard case
    Mongo,
    Polygon
}

@Component({
    selector: 'app-checks-content',
    templateUrl: './checks-content.component.html',
    styleUrls: ['./checks-content.component.less'],
})

export class ChecksContentComponent implements OnInit {
    // The health check options to show right now
    selectedCheck = HealthCheckType.Mongo;

    // The time when the health check was last performed
    lastUpdated = null;

    // The result of the health check, including a pass/fail status and debug messages
    checkResult = new HealthCheckResult(HealthCheckResultStatus.PASSED, ['Loading...']);

    // The number of times we checked for new data after instructing the program to redo the check
    refreshPeeks = 0;

    // Whether the check is being performed right now
    checking = false;

    // Class references for use in html
    checkType = HealthCheckType;
    healthCheckType = HealthCheckType;
    healthCheckResultStatus = HealthCheckResultStatus;
    utilService = UtilService;


    constructor(public api: ApiService) {
    }

    ngOnInit(): void {
        const checkComponent = this;
        this.api.getHealthCheckData((data) => {
            checkComponent.applyResultData(data);
        }, {
            'check_type': HealthCheckType[checkComponent.selectedCheck].toString()
        })
    }

    public performCheck(firstCall: boolean) {
        /**
         * Calls update and then updates local variables once the new data is available.
         */
        if (firstCall && this.checking) {
            return;
        }

        const checkComponent = this;

        function peek() {
            if (!checkComponent.checking) {
                return;
            }

            const oldUpdateTime = checkComponent.lastUpdated;

            function checkTimeLastUpdated(data) {
                // Decode the date, which might be null
                console.log(data);
                const updateTime = data == null ? null : UtilService.decodeDatetime(data['last_updated']);

                if (checkComponent.refreshPeeks >= 20) {
                    // Stop peeking after 20 attempts
                    checkComponent.checking = false;
                    checkComponent.refreshPeeks = 0;
                } else if (updateTime === null || updateTime <= oldUpdateTime) {
                    // Peek again in 3 seconds
                    checkComponent.refreshPeeks += 1;
                } else if (checkComponent.refreshPeeks < 20) {
                    // Stop peeking after new data becomes available
                    checkComponent.applyResultData(data);
                    checkComponent.checking = false;
                    checkComponent.refreshPeeks = 0;
                }
            }

            checkComponent.api.getHealthCheckData(checkTimeLastUpdated, {
                'check_type': HealthCheckType[checkComponent.selectedCheck].toString()
            })
        }

        function startPeeking() {
            // Peek up to 20 times
            const peekerId = setInterval(peek, 3000, [false]);

            // Cancel the peeker task 22 peeks later
            setTimeout(() => {
                clearInterval(peekerId);
            }, 3000 * 22)
        }

        if (firstCall) {
            this.checking = true;
            this.api.performHealthCheck(startPeeking, {
                'check_type': HealthCheckType[checkComponent.selectedCheck].toString()
            });
        }
    }

    public applyResultData(data) {
        // Decode the result of the check, including a pass/fail status and debug messages
        this.checkResult = data['status'] != null && data['debug_messages'] != null
            ? UtilService.decodeHealthCheckResult(data)
            : new HealthCheckResult(HealthCheckResultStatus.PASSED, ['Loading...']);

        // Decode time when the check was performed
        const lastUpdated = UtilService.decodeDatetime(data['last_updated']);
        this.lastUpdated = lastUpdated != null ? lastUpdated : new Date(2000, 1, 1);
    }

    public checkTypes(): HealthCheckType[] {
        const types = [];
        for (let i = 0; i < Object.keys(HealthCheckType).length / 2; i++) {
            types.push(HealthCheckType[HealthCheckType[i]]);
        }
        return types;
    }

    private selectCheck(checkType: HealthCheckType) {
        this.selectedCheck = checkType;
    }

    private selectPrevCheck() {
        let index = this.selectedCheck;
        if (index > 0) {
            this.selectedCheck = HealthCheckType[HealthCheckType[index - 1]];
        }
    }

    private selectNextCheck() {
        let index = this.selectedCheck;
        if (index < Object.keys(HealthCheckType).length / 2 - 1) {
            this.selectedCheck = HealthCheckType[HealthCheckType[index + 1]];
        }
    }
}
