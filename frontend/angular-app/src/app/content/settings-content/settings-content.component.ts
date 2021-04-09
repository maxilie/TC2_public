import {Component, OnInit} from '@angular/core';
import {ApiService} from "../../shared_service/api/api.service";
import {Observable} from "rxjs";

@Component({
    selector: 'app-settings-content',
    templateUrl: './settings-content.component.html',
    styleUrls: ['./settings-content.component.less'],
})

export class SettingsContentComponent implements OnInit {
    newSymbol = 'input symbol';
    symbols: Observable<String[]>;

    constructor(private api: ApiService) {
    }

    ngOnInit() {
        // TODO Load endpoint

        // Load symbols
        this.symbols = this.api.getSymbols();
    }
}
