import {Injectable} from "@angular/core";
import {ApiService} from "./api/api.service";

export enum TabSuperType {
    runtime_control = 'supertab-runtime-control',
    strategy_control = 'supertab-strategy-control',
    system_checks = 'supertab-system-checks'
}

export enum TabSubType {
    // Login tab
    login = 'subtab-login',

    // Sub-tabs for runtime control
    console = 'subtab-console',
    data = 'subtab-data',
    settings = 'subtab-settings',

    // Sub-tabs for strategy control
    strategies = 'subtab-strategies',
    simulations = 'subtab-simulations',

    // Sub-tabs for system checks
    health_checks = 'subtab-health-checks',
    visuals = 'subtab-visuals'
}

@Injectable({
    providedIn: 'root'
})
export class TabService {
    /**
     * A shared service to manage page selection.
     */

    private selectedSuperTab: TabSuperType = TabSuperType.runtime_control;
    private selectedSubTab: TabSubType = TabSubType.login;

    constructor() {
    }

    public selectSuperTab(tab: TabSuperType, api: ApiService) {
        /**
         * Selects the super-tab and the default sub-tab under it.
         */
        this.selectedSuperTab = tab;

        if (!ApiService.isAuthenticated()) {
            this.selectedSubTab = TabSubType.login;
            return;
        }

        switch (this.selectedSuperTab) {
            // Log Control super-tab defaults to console sub-tab
            case TabSuperType.runtime_control:
                this.selectedSubTab = TabSubType.console;
                return;
            case TabSuperType.strategy_control:
                this.selectedSubTab = TabSubType.strategies;
                return;
            case TabSuperType.system_checks:
                this.selectedSubTab = TabSubType.health_checks;
                return;
        }
    }

    public selectSubTab(tab: TabSubType, api: ApiService) {
        /**
         * Selects the sub-tab only if the user is authenticated.
         */
        if (!ApiService.isAuthenticated()) {
            return;
        }
        this.selectedSubTab = tab;
    }

    public getSelectedSuperTab(): TabSuperType {
        return this.selectedSuperTab;
    }

    public getSelectedSubTab(): TabSubType {
        return this.selectedSubTab;
    }

}
