import {Component, OnInit} from '@angular/core';
import {TabService, TabSubType, TabSuperType} from "../../shared_service/tab.service";
import {ApiService} from "../../shared_service/api/api.service";


@Component({
    selector: 'app-tabarea-sub',
    templateUrl: './tabarea-sub.component.html',
    styleUrls: ['./tabarea-sub.component.less'],
})

/**
 * The content box itself. This component is merely a box that positions and frames the content.
 */
export class TabareaSubComponent implements OnInit {
    tabSuperType = TabSuperType;
    tabSubType = TabSubType;
    apiService = ApiService;

    constructor(private tabs: TabService, private api: ApiService) {

    }

    ngOnInit(): void {
    }

}
