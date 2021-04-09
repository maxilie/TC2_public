import {AfterContentInit, Component} from '@angular/core';
import {ApiService} from "../shared_service/api/api.service";
import {TabService, TabSubType, TabSuperType} from "../shared_service/tab.service";


@Component({
    selector: 'app-main-content',
    templateUrl: './main-content.component.html',
    styleUrls: ['./main-content.component.less'],
})

/**
 * The content box itself. This component is merely a box that positions and frames the content.
 */
export class MainContentComponent implements AfterContentInit {
    tabSubType = TabSubType;
    apiService = ApiService;

    constructor(private api: ApiService, private tabs: TabService) {
    }

    ngAfterContentInit(): void {
        // Show console if user is already logged in
        if (ApiService.isAuthenticated()) {
            this.tabs.selectSuperTab(TabSuperType.runtime_control, this.api);
        }
    }

}
