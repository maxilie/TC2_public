import {Component, OnInit} from '@angular/core';
import {TabService, TabSuperType} from "../../shared_service/tab.service";
import {ApiService} from "../../shared_service/api/api.service";


@Component({
    selector: 'app-tabarea-super',
    templateUrl: './tabarea-super.component.html',
    styleUrls: ['./tabarea-super.component.less'],
})

/**
 * The content box itself. This component is merely a box that positions and frames the content.
 */
export class TabareaSuperComponent implements OnInit {
    tabSuperType = TabSuperType;

    constructor(private tabs: TabService, private api: ApiService) {
    }

    ngOnInit(): void {
    }

}
