import {BrowserModule} from '@angular/platform-browser';
import {NgModule} from '@angular/core';

import {AppComponent} from './app.component';
import {MainContentComponent} from './content/main-content.component';
import {LogsContentComponent} from './content/logs-content/logs-content.component';
import {TabareaSuperComponent} from './tab/tabarea-super/tabarea-super.component';
import {TabareaSubComponent} from './tab/tabarea-sub/tabarea-sub.component';
import {HttpClientModule} from '@angular/common/http';

import {LoginContentComponent} from "./content/login-content/login-content.component";
import {FormsModule} from "@angular/forms";
import {ApiService} from "./shared_service/api/api.service";
import {TabService} from "./shared_service/tab.service";
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {MatButtonModule, MatSelectModule} from "@angular/material";
import {VisualsContentComponent} from "./content/visuals-content/visuals-content.component";
import {PriceGraphContentComponent} from "./content/visuals-content/price-graph-content/price-graph-content.component";
import {SimulationsContentComponent} from "./content/simulations-content/simulations-content.component";
import {UtilService} from "./shared_service/util.service";
import {ChecksContentComponent} from "./content/checks-content/checks-content.component";
import {DataContentComponent} from "./content/data-content/data-content.component";
import {SwingSetupContentComponent} from "./content/visuals-content/swing-setup-content/swing-setup-content.component";
import {Breakout1SetupContentComponent} from "./content/visuals-content/breakout1-setup-content/breakout1-setup-content.component";
import {SettingsContentComponent} from "./content/settings-content/settings-content.component";

@NgModule({
    declarations: [
        AppComponent,
        MainContentComponent,
        LoginContentComponent,
        TabareaSuperComponent,
        TabareaSubComponent,
        LogsContentComponent,
        SettingsContentComponent,
        SimulationsContentComponent,
        VisualsContentComponent,
        PriceGraphContentComponent,
        ChecksContentComponent,
        DataContentComponent,
        SwingSetupContentComponent,
        Breakout1SetupContentComponent
    ],
    imports: [
        BrowserModule,
        HttpClientModule,
        FormsModule,
        BrowserAnimationsModule,
        MatSelectModule,
        MatButtonModule
    ],
    providers: [ApiService, TabService, UtilService],
    bootstrap: [AppComponent]
})

export class AppModule {
}
