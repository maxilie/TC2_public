import {Component} from '@angular/core';
import {ApiService} from "../../shared_service/api/api.service";
import {TabService, TabSuperType} from "../../shared_service/tab.service";

@Component({
    selector: 'app-login-content',
    templateUrl: './login-content.component.html',
    styleUrls: ['./login-content.component.less']
})
export class LoginContentComponent {
    constructor(private api: ApiService, private tabs: TabService) {
    }

    login() {
        const loginComp = this;

        function onLoginSuccess() {
            loginComp.tabs.selectSuperTab(TabSuperType.runtime_control, loginComp.api);
        }

        this.api.login(onLoginSuccess);
    }
}
