import {Component, OnInit, ViewChild} from '@angular/core';
import {Observable} from "rxjs";
import {ApiService} from "../../shared_service/api/api.service";
import {LogFeed} from "../../models/models";

@Component({
    selector: 'app-logs-content',
    templateUrl: './logs-content.component.html',
    styleUrls: ['./logs-content.component.less'],
})

export class LogsContentComponent implements OnInit {
    logFeed = LogFeed;

    // Current lines to display (changes when different files are selected)
    lines$: Observable<String[]>;

    // Current logfile names to display
    logfiles = [''];

    // Current logfeed selected
    logFeedSelected: LogFeed;

    // Current logfile selected
    logfileSelected: string;

    // Whether the page is waiting for logs to load
    loading = false;

    // Logs container div
    // @ts-ignore
    @ViewChild('logsContainer') logsContainer;

    constructor(private api: ApiService) {
    }

    ngOnInit() {
        // Show latest trading logs by default
        this.selectLogFeed(LogFeed.LIVE_TRADING);
    }

    showLatest() {
        this.loading = true;
        const logfeed = this.logFeedSelected;
        this.api.getFeedFiles(logfeed).subscribe(logfiles => {
            if (!this.loading) {
                return;
            }
            this.logfiles = new Array<string>(logfiles.length);
            let logfile = '';
            for (let logfileIndex in logfiles) {
                logfile = <string>logfiles[logfileIndex];
                this.logfiles[logfileIndex] = logfile;
                this.logfileSelected = logfile;
            }
            if (logfile == '') {
                this.loading = false;
                return;
            } else {
                this.lines$ = this.api.getFileLines(logfeed, logfile);
                this.lines$.subscribe(() => {
                    this.scrollToBottom();
                    this.loading = false;
                })
            }
        });
    }

    selectLogFile(filename: string) {
        /**
         * Called when user selects a logfile from the dropdown.
         */
        this.lines$ = this.api.getFileLines(this.logFeedSelected, filename);
        this.logfileSelected = filename;
        this.scrollToBottom();
    }

    selectLogFeed(feedToSelect: LogFeed) {
        /**
         * Called when user selects a logfeed from the left side of the screen.
         */
        this.logFeedSelected = feedToSelect;
        this.showLatest();
    }

    onLogfileChange($event) {
        /**
         * Called when a logfile is selected.
         */
        this.logfileSelected = $event.value;
    }

    clearLogs() {
        this.logfileSelected = '';
        this.logfiles = [''];
        this.lines$ = new Observable<String[]>();
        this.api.clearLogs();
        setTimeout(() => {
            this.selectLogFeed(LogFeed.PROGRAM)
        }, 1000)
    }

    selectPreviousLogfile() {
        /**
         * Shows lines from the previous logfile.
         */

        // Ignore clicks when the button is inactive (no file selected yet)
        if (this.logfileSelected == null) {
            return;
        }

        // Get the next file
        const index = Math.max(0, this.logfiles.indexOf(this.logfileSelected) - 1);
        this.selectLogFile(this.logfiles[index].toString());
    }

    selectNextLogfile() {
        /**
         * Shows lines from the next logfile.
         */

        // Ignore clicks when the button is inactive (no file selected yet)
        if (this.logfileSelected == null) {
            return;
        }

        // Get the next file
        const index = Math.min(this.logfiles.length - 1, this.logfiles.indexOf(this.logfileSelected) + 1);
        this.selectLogFile(this.logfiles[index].toString());
    }

    scrollToBottom() {
        setTimeout(() => {
            if (this.logsContainer != null) {
                this.logsContainer.scrollTop = this.logsContainer.scrollHeight;
            } else {
                console.log('Tried to scroll to bottom but logsContainer is null')
            }
        }, 500);
    }
}
