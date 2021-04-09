(window["webpackJsonp"] = window["webpackJsonp"] || []).push([["main"],{

/***/ "./$$_lazy_route_resource lazy recursive":
/*!******************************************************!*\
  !*** ./$$_lazy_route_resource lazy namespace object ***!
  \******************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

function webpackEmptyAsyncContext(req) {
	// Here Promise.resolve().then() is used instead of new Promise() to prevent
	// uncaught exception popping up in devtools
	return Promise.resolve().then(function() {
		var e = new Error("Cannot find module '" + req + "'");
		e.code = 'MODULE_NOT_FOUND';
		throw e;
	});
}
webpackEmptyAsyncContext.keys = function() { return []; };
webpackEmptyAsyncContext.resolve = webpackEmptyAsyncContext;
module.exports = webpackEmptyAsyncContext;
webpackEmptyAsyncContext.id = "./$$_lazy_route_resource lazy recursive";

/***/ }),

/***/ "./node_modules/raw-loader/index.js!./src/app/app.component.html":
/*!**************************************************************!*\
  !*** ./node_modules/raw-loader!./src/app/app.component.html ***!
  \**************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<app-tabarea-super></app-tabarea-super>\n<app-tabarea-sub></app-tabarea-sub>\n<app-main-content></app-main-content>\n"

/***/ }),

/***/ "./node_modules/raw-loader/index.js!./src/app/content/console-content/console-content.component.html":
/*!**************************************************************************************************!*\
  !*** ./node_modules/raw-loader!./src/app/content/logs-content/mongo-check-content.component.html ***!
  \**************************************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div use_type=\"console-div\" style=\"position: relative;\">\n    <p style=\"text-align: center\">Console output goes here.</p>\n    <div class=\"row\" *ngIf=\"!api.token\">\n        <ul>\n            <li *ngFor=\"let line of lines$ | async\" class=\"console-line\">\n                line\n            </li>\n        </ul>\n    </div>\n    <div class=\"row\" *ngIf=\"api.token\">\n        <p>Not authenticated</p>\n    </div>\n</div>\n"

/***/ }),

/***/ "./node_modules/raw-loader/index.js!./src/app/content/login-content/login-content.component.html":
/*!**********************************************************************************************!*\
  !*** ./node_modules/raw-loader!./src/app/content/login-content/login-content.component.html ***!
  \**********************************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div use_type=\"login-container\" *ngIf=\"!api.token\">\n\n    <div use_type=\"username-container\">\n        <label use_type=\"username-label\">Username:</label><br/>\n        <input type=\"text\" name=\"login-username\" [(ngModel)]=\"api.username\">\n        <span *ngFor=\"let error of api.errors.username\"><br/>\n            {{ error }}</span></div>\n\n    <div use_type=\"password-container\">\n        <label use_type=\"password-label\">Password:</label><br/>\n        <input type=\"password\" name=\"login-password\" [(ngModel)]=\"api.password\">\n        <span *ngFor=\"let error of api.errors.password\"><br/>\n            {{ error }}</span>\n    </div>\n    <br>\n\n    <div use_type=\"login-button-container\">\n        <button use_type=\"login-button\" (click)=\"this.login()\">Log In</button>\n    </div>\n    <div>\n        <span *ngFor=\"let error of api.errors.non_field_errors\">{{ error }}<br/></span>\n    </div>\n</div>\n<div *ngIf=\"api.token\">\n    <div>You are logged in as {{ api.username }}.<br/>\n        Token Expires: {{ api.token_expires }}<br/>\n    </div>\n    <!-- TODO Emit event to trigger console content -->\n</div>\n"

/***/ }),

/***/ "./node_modules/raw-loader/index.js!./src/app/content/main-content.component.html":
/*!*******************************************************************************!*\
  !*** ./node_modules/raw-loader!./src/app/content/main-content.component.html ***!
  \*******************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div [ngSwitch]=\"tabs.getSelectedSubTab()\" use_type=\"main-content-box\">\n    <!-- Filler div so that content box maintains its height -->\n    <div></div>\n\n    <app-login-content *ngSwitchCase=\"tabSubType.login\"></app-login-content>\n    <app-logs-content *ngSwitchCase=\"tabSubType.console\"></app-logs-content>\n    <!-- TODO Add other content-xxx for other tabSubTypes -->\n\n</div>\n"

/***/ }),

/***/ "./node_modules/raw-loader/index.js!./src/app/tab/tabarea-sub/tabarea-sub.component.html":
/*!**************************************************************************************!*\
  !*** ./node_modules/raw-loader!./src/app/tab/tabarea-sub/tabarea-sub.component.html ***!
  \**************************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div [ngSwitch]=\"tabs.getSelectedSuperTab()\" use_type=\"tabarea-sub-container\">\n\n    <!-- Default to the login sub-tab if no super-tab is selected -->\n    <div *ngSwitchDefault\n         [ngClass]=\"tabs.getSelectedSubTab() == tabSubType.login ? 'tab-sub-selected' : 'tab-sub'\">\n        <span class=\"tab-sub__text\">Admin Login</span>\n    </div>\n\n    <!-- Sub-tabs for runtime control -->\n    <div *ngSwitchCase=\"tabSuperType.runtime_control\"\n         [ngClass]=\"tabs.getSelectedSubTab() == tabSubType.console ? 'tab-sub-selected' : 'tab-sub'\"\n         (click)=\"tabs.selectSubTab(tabSubType.console)\">\n        <span class=\"tab-sub__text\">Console</span></div>\n    <div *ngSwitchCase=\"tabSuperType.runtime_control\"\n         [ngClass]=\"tabs.getSelectedSubTab() == tabSubType.updates ? 'tab-sub-selected' : 'tab-sub'\"\n         (click)=\"tabs.selectSubTab(tabSubType.updates)\">\n        <span class=\"tab-sub__text\">Updates</span></div>\n    <div *ngSwitchCase=\"tabSuperType.runtime_control\"\n         [ngClass]=\"tabs.getSelectedSubTab() == tabSubType.settings ? 'tab-sub-selected' : 'tab-sub'\"\n         (click)=\"tabs.selectSubTab(tabSubType.settings)\">\n        <span class=\"tab-sub__text\">Settings</span></div>\n\n    <!-- TODO Sub-tabs for strategy control -->\n\n    <!-- TODO Sub-tabs for log control -->\n\n    <!-- TODO Sub-tabs for system checks -->\n\n</div>\n"

/***/ }),

/***/ "./node_modules/raw-loader/index.js!./src/app/tab/tabarea-super/tabarea-super.component.html":
/*!******************************************************************************************!*\
  !*** ./node_modules/raw-loader!./src/app/tab/tabarea-super/tabarea-super.component.html ***!
  \******************************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "<div use_type=\"tabarea-super-container\">\n    <div [ngClass]=\"tabs.getSelectedSuperTab() == tabSuperType.runtime_control ? 'tab-super-selected' : 'tab-super'\">\n        <span class=\"tab-super__text\">Runtime Control</span></div>\n\n    <div [ngClass]=\"tabs.getSelectedSuperTab() == tabSuperType.strategy_control ? 'tab-super-selected' : 'tab-super'\">\n        <span class=\"tab-super__text\">Strategy Control</span></div>\n\n    <div [ngClass]=\"tabs.getSelectedSuperTab() == tabSuperType.log_control ? 'tab-super-selected' : 'tab-super'\">\n        <span class=\"tab-super__text\">Log Control</span></div>\n\n    <div [ngClass]=\"tabs.getSelectedSuperTab() == tabSuperType.system_checks ? 'tab-super-selected' : 'tab-super'\">\n        <span class=\"tab-super__text\">System Checks</span></div>\n</div>\n"

/***/ }),

/***/ "./src/app/app.component.less":
/*!************************************!*\
  !*** ./src/app/app.component.less ***!
  \************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "html,\nbody {\n  margin: 0;\n  height: 100%;\n  overflow: hidden;\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi9Vc2Vycy9tYXh3ZWxsaWxpZS9QeWNoYXJtUHJvamVjdHMvVEMyL2Zyb250ZW5kL2FuZ3VsYXItYXBwL3NyYy9hcHAvYXBwLmNvbXBvbmVudC5sZXNzIiwic3JjL2FwcC9hcHAuY29tcG9uZW50Lmxlc3MiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7O0VBQ0UsU0FBQTtFQUNBLFlBQUE7RUFDQSxnQkFBQTtBQ0VGIiwiZmlsZSI6InNyYy9hcHAvYXBwLmNvbXBvbmVudC5sZXNzIiwic291cmNlc0NvbnRlbnQiOlsiaHRtbCwgYm9keSB7XG4gIG1hcmdpbjogMDtcbiAgaGVpZ2h0OiAxMDAlO1xuICBvdmVyZmxvdzogaGlkZGVuXG59XG4iLCJodG1sLFxuYm9keSB7XG4gIG1hcmdpbjogMDtcbiAgaGVpZ2h0OiAxMDAlO1xuICBvdmVyZmxvdzogaGlkZGVuO1xufVxuIl19 */"

/***/ }),

/***/ "./src/app/app.component.ts":
/*!**********************************!*\
  !*** ./src/app/app.component.ts ***!
  \**********************************/
/*! exports provided: AppComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppComponent", function() { return AppComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");


let AppComponent = class AppComponent {
    constructor() {
        this.title = 'TC2-Panel';
        this.contentBoxWidth = 90;
    }
};
AppComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-root',
        template: __webpack_require__(/*! raw-loader!./app.component.html */ "./node_modules/raw-loader/index.js!./src/app/app.component.html"),
        styles: [__webpack_require__(/*! ./app.component.less */ "./src/app/app.component.less")]
    })
], AppComponent);



/***/ }),

/***/ "./src/app/app.module.ts":
/*!*******************************!*\
  !*** ./src/app/app.module.ts ***!
  \*******************************/
/*! exports provided: AppModule */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "AppModule", function() { return AppModule; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_platform_browser__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/platform-browser */ "./node_modules/@angular/platform-browser/fesm2015/platform-browser.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _app_component__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./app.component */ "./src/app/app.component.ts");
/* harmony import */ var _content_main_content_component__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./content/main-content.component */ "./src/app/content/main-content.component.ts");
/* harmony import */ var _content_console_content_console_content_component__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./content/logs-content/logs-content.component */ "./src/app/content/console-content/console-content.component.ts");
/* harmony import */ var _tab_tabarea_super_tabarea_super_component__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./tab/tabarea-super/tabarea-super.component */ "./src/app/tab/tabarea-super/tabarea-super.component.ts");
/* harmony import */ var _tab_tabarea_sub_tabarea_sub_component__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./tab/tabarea-sub/tabarea-sub.component */ "./src/app/tab/tabarea-sub/tabarea-sub.component.ts");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm2015/http.js");
/* harmony import */ var _content_login_content_login_content_component__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./content/login-content/login-content.component */ "./src/app/content/login-content/login-content.component.ts");
/* harmony import */ var _angular_forms__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! @angular/forms */ "./node_modules/@angular/forms/fesm2015/forms.js");
/* harmony import */ var _shared_service_api_service__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ./shared_service/api.service */ "./src/app/shared_service/api.service.ts");
/* harmony import */ var _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_12__ = __webpack_require__(/*! ./shared_service/tab.service */ "./src/app/shared_service/tab.service.ts");













let AppModule = class AppModule {
};
AppModule = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_2__["NgModule"])({
        declarations: [
            _app_component__WEBPACK_IMPORTED_MODULE_3__["AppComponent"],
            _content_main_content_component__WEBPACK_IMPORTED_MODULE_4__["MainContentComponent"],
            _content_login_content_login_content_component__WEBPACK_IMPORTED_MODULE_9__["LoginContentComponent"],
            _tab_tabarea_super_tabarea_super_component__WEBPACK_IMPORTED_MODULE_6__["TabareaSuperComponent"],
            _tab_tabarea_sub_tabarea_sub_component__WEBPACK_IMPORTED_MODULE_7__["TabareaSubComponent"],
            _content_console_content_console_content_component__WEBPACK_IMPORTED_MODULE_5__["ConsoleContentComponent"]
        ],
        imports: [
            _angular_platform_browser__WEBPACK_IMPORTED_MODULE_1__["BrowserModule"],
            _angular_common_http__WEBPACK_IMPORTED_MODULE_8__["HttpClientModule"],
            _angular_forms__WEBPACK_IMPORTED_MODULE_10__["FormsModule"]
        ],
        providers: [_shared_service_api_service__WEBPACK_IMPORTED_MODULE_11__["ApiService"], _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_12__["TabService"]],
        bootstrap: [_app_component__WEBPACK_IMPORTED_MODULE_3__["AppComponent"]]
    })
], AppModule);



/***/ }),

/***/ "./src/app/content/console-content/console-content.component.less":
/*!************************************************************************!*\
  !*** ./src/app/content/logs-content/mongo-check-content.component.less ***!
  \************************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = ".console-line {\n  font-size: 0.7em;\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi9Vc2Vycy9tYXh3ZWxsaWxpZS9QeWNoYXJtUHJvamVjdHMvVEMyL2Zyb250ZW5kL2FuZ3VsYXItYXBwL3NyYy9hcHAvY29udGVudC9jb25zb2xlLWNvbnRlbnQvY29uc29sZS1jb250ZW50LmNvbXBvbmVudC5sZXNzIiwic3JjL2FwcC9jb250ZW50L2NvbnNvbGUtY29udGVudC9jb25zb2xlLWNvbnRlbnQuY29tcG9uZW50Lmxlc3MiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7RUFDRSxnQkFBQTtBQ0NGIiwiZmlsZSI6InNyYy9hcHAvY29udGVudC9jb25zb2xlLWNvbnRlbnQvY29uc29sZS1jb250ZW50LmNvbXBvbmVudC5sZXNzIiwic291cmNlc0NvbnRlbnQiOlsiLmNvbnNvbGUtbGluZSB7XG4gIGZvbnQtc2l6ZTogMC43ZW07XG59XG4iLCIuY29uc29sZS1saW5lIHtcbiAgZm9udC1zaXplOiAwLjdlbTtcbn1cbiJdfQ== */"

/***/ }),

/***/ "./src/app/content/console-content/console-content.component.ts":
/*!**********************************************************************!*\
  !*** ./src/app/content/logs-content/mongo-check-content.component.ts ***!
  \**********************************************************************/
/*! exports provided: MongoCheckContentComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ConsoleContentComponent", function() { return ConsoleContentComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _shared_service_api_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../shared_service/api.service */ "./src/app/shared_service/api.service.ts");



let ConsoleContentComponent = class ConsoleContentComponent {
    constructor(api) {
        this.api = api;
    }
    ngOnInit() {
    }
    getTasks() {
        this.lines$ = this.api.getTradingLogs();
    }
};
ConsoleContentComponent.ctorParameters = () => [
    { type: _shared_service_api_service__WEBPACK_IMPORTED_MODULE_2__["ApiService"] }
];
ConsoleContentComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-logs-content',
        template: __webpack_require__(/*! raw-loader!./mongo-check-content.component.html */ "./node_modules/raw-loader/index.js!./src/app/content/console-content/console-content.component.html"),
        styles: [__webpack_require__(/*! ./mongo-check-content.component.less */ "./src/app/content/console-content/console-content.component.less")]
    })
], ConsoleContentComponent);



/***/ }),

/***/ "./src/app/content/login-content/login-content.component.less":
/*!********************************************************************!*\
  !*** ./src/app/content/login-content/login-content.component.less ***!
  \********************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "#login-container {\n  text-align: center;\n}\n#username-container {\n  display: inline-block;\n}\n#username-label {\n  display: inline-block;\n}\n#password-container {\n  display: inline-block;\n}\n#password-label {\n  display: inline-block;\n}\n#login-button-container {\n  display: inline-block;\n}\n#login-button {\n  display: inline-block;\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi9Vc2Vycy9tYXh3ZWxsaWxpZS9QeWNoYXJtUHJvamVjdHMvVEMyL2Zyb250ZW5kL2FuZ3VsYXItYXBwL3NyYy9hcHAvY29udGVudC9sb2dpbi1jb250ZW50L2xvZ2luLWNvbnRlbnQuY29tcG9uZW50Lmxlc3MiLCJzcmMvYXBwL2NvbnRlbnQvbG9naW4tY29udGVudC9sb2dpbi1jb250ZW50LmNvbXBvbmVudC5sZXNzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBO0VBQ0Usa0JBQUE7QUNDRjtBREVBO0VBQ0UscUJBQUE7QUNBRjtBREdBO0VBQ0UscUJBQUE7QUNERjtBRElBO0VBQ0UscUJBQUE7QUNGRjtBREtBO0VBQ0UscUJBQUE7QUNIRjtBRE1BO0VBQ0UscUJBQUE7QUNKRjtBRE9BO0VBQ0UscUJBQUE7QUNMRiIsImZpbGUiOiJzcmMvYXBwL2NvbnRlbnQvbG9naW4tY29udGVudC9sb2dpbi1jb250ZW50LmNvbXBvbmVudC5sZXNzIiwic291cmNlc0NvbnRlbnQiOlsiI2xvZ2luLWNvbnRhaW5lciB7XG4gIHRleHQtYWxpZ246IGNlbnRlcjtcbn1cblxuI3VzZXJuYW1lLWNvbnRhaW5lciB7XG4gIGRpc3BsYXk6IGlubGluZS1ibG9jaztcbn1cblxuI3VzZXJuYW1lLWxhYmVsIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xufVxuXG4jcGFzc3dvcmQtY29udGFpbmVyIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xufVxuXG4jcGFzc3dvcmQtbGFiZWwge1xuICBkaXNwbGF5OiBpbmxpbmUtYmxvY2s7XG59XG5cbiNsb2dpbi1idXR0b24tY29udGFpbmVyIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xufVxuXG4jbG9naW4tYnV0dG9uIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xufVxuIiwiI2xvZ2luLWNvbnRhaW5lciB7XG4gIHRleHQtYWxpZ246IGNlbnRlcjtcbn1cbiN1c2VybmFtZS1jb250YWluZXIge1xuICBkaXNwbGF5OiBpbmxpbmUtYmxvY2s7XG59XG4jdXNlcm5hbWUtbGFiZWwge1xuICBkaXNwbGF5OiBpbmxpbmUtYmxvY2s7XG59XG4jcGFzc3dvcmQtY29udGFpbmVyIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xufVxuI3Bhc3N3b3JkLWxhYmVsIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xufVxuI2xvZ2luLWJ1dHRvbi1jb250YWluZXIge1xuICBkaXNwbGF5OiBpbmxpbmUtYmxvY2s7XG59XG4jbG9naW4tYnV0dG9uIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xufVxuIl19 */"

/***/ }),

/***/ "./src/app/content/login-content/login-content.component.ts":
/*!******************************************************************!*\
  !*** ./src/app/content/login-content/login-content.component.ts ***!
  \******************************************************************/
/*! exports provided: LoginContentComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "LoginContentComponent", function() { return LoginContentComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _shared_service_api_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../shared_service/api.service */ "./src/app/shared_service/api.service.ts");
/* harmony import */ var _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../shared_service/tab.service */ "./src/app/shared_service/tab.service.ts");




let LoginContentComponent = class LoginContentComponent {
    constructor(api, tabs) {
        this.api = api;
        this.tabs = tabs;
    }
    ngOnInit() {
    }
    login() {
        this.api.login();
        this.tabs.selectSubTab(_shared_service_tab_service__WEBPACK_IMPORTED_MODULE_3__["TabSubType"].console);
    }
    getTradingLogs() {
        let logs = this.api.getTradingLogs();
        console.log(logs);
    }
};
LoginContentComponent.ctorParameters = () => [
    { type: _shared_service_api_service__WEBPACK_IMPORTED_MODULE_2__["ApiService"] },
    { type: _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_3__["TabService"] }
];
LoginContentComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-login-content',
        template: __webpack_require__(/*! raw-loader!./login-content.component.html */ "./node_modules/raw-loader/index.js!./src/app/content/login-content/login-content.component.html"),
        styles: [__webpack_require__(/*! ./login-content.component.less */ "./src/app/content/login-content/login-content.component.less")]
    })
], LoginContentComponent);



/***/ }),

/***/ "./src/app/content/main-content.component.less":
/*!*****************************************************!*\
  !*** ./src/app/content/main-content.component.less ***!
  \*****************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "#main-content-box {\n  width: 90%;\n  height: 65%;\n  position: absolute;\n  display: block;\n  margin-left: 4%;\n  border: 4px solid cornflowerblue;\n  border-radius: 3px;\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi9Vc2Vycy9tYXh3ZWxsaWxpZS9QeWNoYXJtUHJvamVjdHMvVEMyL2Zyb250ZW5kL2FuZ3VsYXItYXBwL3NyYy9hcHAvY29udGVudC9tYWluLWNvbnRlbnQuY29tcG9uZW50Lmxlc3MiLCJzcmMvYXBwL2NvbnRlbnQvbWFpbi1jb250ZW50LmNvbXBvbmVudC5sZXNzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUlBO0VBQ0UsVUFBQTtFQUNBLFdBQUE7RUFDQSxrQkFBQTtFQUNBLGNBQUE7RUFDQSxlQUFBO0VBQ0EsZ0NBQUE7RUFDQSxrQkFBQTtBQ0hGIiwiZmlsZSI6InNyYy9hcHAvY29udGVudC9tYWluLWNvbnRlbnQuY29tcG9uZW50Lmxlc3MiLCJzb3VyY2VzQ29udGVudCI6WyJAYm94V2lkdGg6IDkwJTtcbkBtYXJnaW5MZWZ0OiA0JTtcbkBib3hIZWlnaHQ6IDY1JTtcblxuI21haW4tY29udGVudC1ib3gge1xuICB3aWR0aDogQGJveFdpZHRoO1xuICBoZWlnaHQ6IEBib3hIZWlnaHQ7XG4gIHBvc2l0aW9uOiBhYnNvbHV0ZTtcbiAgZGlzcGxheTogYmxvY2s7XG4gIG1hcmdpbi1sZWZ0OiBAbWFyZ2luTGVmdDtcbiAgYm9yZGVyOiA0cHggc29saWQgY29ybmZsb3dlcmJsdWU7XG4gIGJvcmRlci1yYWRpdXM6IDNweDtcbn1cbiIsIiNtYWluLWNvbnRlbnQtYm94IHtcbiAgd2lkdGg6IDkwJTtcbiAgaGVpZ2h0OiA2NSU7XG4gIHBvc2l0aW9uOiBhYnNvbHV0ZTtcbiAgZGlzcGxheTogYmxvY2s7XG4gIG1hcmdpbi1sZWZ0OiA0JTtcbiAgYm9yZGVyOiA0cHggc29saWQgY29ybmZsb3dlcmJsdWU7XG4gIGJvcmRlci1yYWRpdXM6IDNweDtcbn1cbiJdfQ== */"

/***/ }),

/***/ "./src/app/content/main-content.component.ts":
/*!***************************************************!*\
  !*** ./src/app/content/main-content.component.ts ***!
  \***************************************************/
/*! exports provided: MainContentComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "MainContentComponent", function() { return MainContentComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _shared_service_api_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../shared_service/api.service */ "./src/app/shared_service/api.service.ts");
/* harmony import */ var _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../shared_service/tab.service */ "./src/app/shared_service/tab.service.ts");




let MainContentComponent = 
/**
 * The content box itself. This component is merely a box that positions and frames the content.
 */
class MainContentComponent {
    constructor(api, tabs) {
        this.api = api;
        this.tabs = tabs;
        this.tabSubType = _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_3__["TabSubType"];
    }
    ngAfterContentInit() {
        // TODO Check cookies.
        //      If logged in, get an API key and set tabs.selectSubTab(TabSubType.console)
        this.tabs.selectSuperTab(_shared_service_tab_service__WEBPACK_IMPORTED_MODULE_3__["TabSuperType"].runtime_control);
        if (!this.api.token) {
            this.tabs.selectSubTab(_shared_service_tab_service__WEBPACK_IMPORTED_MODULE_3__["TabSubType"].login);
        }
        else {
            this.tabs.selectSubTab(_shared_service_tab_service__WEBPACK_IMPORTED_MODULE_3__["TabSubType"].console);
        }
    }
};
MainContentComponent.ctorParameters = () => [
    { type: _shared_service_api_service__WEBPACK_IMPORTED_MODULE_2__["ApiService"] },
    { type: _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_3__["TabService"] }
];
MainContentComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-main-content',
        template: __webpack_require__(/*! raw-loader!./main-content.component.html */ "./node_modules/raw-loader/index.js!./src/app/content/main-content.component.html"),
        styles: [__webpack_require__(/*! ./main-content.component.less */ "./src/app/content/main-content.component.less")]
    })
    /**
     * The content box itself. This component is merely a box that positions and frames the content.
     */
], MainContentComponent);



/***/ }),

/***/ "./src/app/shared_service/api.service.ts":
/*!***********************************************!*\
  !*** ./src/app/shared_service/api.service.ts ***!
  \***********************************************/
/*! exports provided: ApiService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "ApiService", function() { return ApiService; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _angular_common_http__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @angular/common/http */ "./node_modules/@angular/common/fesm2015/http.js");
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../../environments/environment */ "./src/environments/environment.ts");




let ApiService = class ApiService {
    constructor(http) {
        this.http = http;
        /**
         * A shared service to manage the client's authentication and connection to the backend API.
         */
        this.API_BASE_URL = _environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].apiUrl;
        this.TOKEN_VALID_FOR = 60 * 60 * 24;
        // Pre-fill the username box
        this.username = 'admin';
        this.password = '';
        // error messages received from the login attempt
        this.errors = [];
        this.httpOptions = {
            headers: new _angular_common_http__WEBPACK_IMPORTED_MODULE_2__["HttpHeaders"]({ 'Content-Type': 'application/json' })
        };
    }
    // Functions using /logs endpoint
    getTradingLogs() {
        this.ensureValidToken();
        try {
            return this._getTradingLogs();
        }
        catch (e) {
            this.refreshToken();
            return this._getTradingLogs();
        }
    }
    _getTradingLogs() {
        return this.http.get(`${this.API_URL}/logs/trading`, {
            headers: new _angular_common_http__WEBPACK_IMPORTED_MODULE_2__["HttpHeaders"]().set('Authorization', `Bearer ${this.token}`)
        });
    }
    // Authentication functions
    ensureValidToken() {
        if (this.token == null
            || this.token_expires.getTime() <= new Date(new Date().getTime() - 5 * 1000).getTime()) {
            this.refreshToken();
        }
    }
    login() {
        /**
         * Gets an auth token from django.
         */
        console.log(this.http.post(`${this.API_URL}/token/new`, JSON.stringify({
            username: this.username,
            password: this.password
        }), this.httpOptions).subscribe(data => {
            this.updateData(data['token']);
        }, err => {
            console.log('auth token request received error response:');
            console.log(err);
        }));
    }
    // Refreshes the JWT token, to extend the time the user is logged in
    refreshToken() {
        this.http.post(`${this.API_URL}/token/refresh`, JSON.stringify({ token: this.token }), this.httpOptions).subscribe(data => {
            this.updateData(data['access']);
        }, err => {
            this.errors = err['error'];
        });
    }
    logout() {
        this.token = null;
        this.token_expires = null;
    }
    updateData(token) {
        this.token = token;
        this.token_expires = new Date(new Date().getTime() + (1000 * this.TOKEN_VALID_FOR));
    }
};
ApiService.ctorParameters = () => [
    { type: _angular_common_http__WEBPACK_IMPORTED_MODULE_2__["HttpClient"] }
];
ApiService = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Injectable"])({
        providedIn: 'root'
    })
], ApiService);



/***/ }),

/***/ "./src/app/shared_service/tab.service.ts":
/*!***********************************************!*\
  !*** ./src/app/shared_service/tab.service.ts ***!
  \***********************************************/
/*! exports provided: TabSuperType, TabSubType, TabService */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TabSuperType", function() { return TabSuperType; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TabSubType", function() { return TabSubType; });
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TabService", function() { return TabService; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");


var TabSuperType;
(function (TabSuperType) {
    TabSuperType["runtime_control"] = "supertab-runtime-control";
    TabSuperType["strategy_control"] = "supertab-strategy-control";
    TabSuperType["log_control"] = "supertab-log-control";
    TabSuperType["system_checks"] = "supertab-system-checks";
})(TabSuperType || (TabSuperType = {}));
var TabSubType;
(function (TabSubType) {
    // Login tab
    TabSubType["login"] = "subtab-login";
    // Sub-tabs for runtime control
    TabSubType["console"] = "subtab-console";
    TabSubType["updates"] = "subtab-updates";
    TabSubType["settings"] = "subtab-settings";
    // TODO Sub-tabs for strategy control
    // TODO Sub-tabs for log control
    // TODO Sub-tabs for system checks
})(TabSubType || (TabSubType = {}));
let TabService = class TabService {
    constructor() {
        /**
         * A shared service to manage page selection.
         */
        this.selectedSuperTab = TabSuperType.runtime_control;
        this.selectedSubTab = TabSubType.login;
    }
    selectSuperTab(tab) {
        this.selectedSuperTab = tab;
    }
    selectSubTab(tab) {
        this.selectedSubTab = tab;
    }
    getSelectedSuperTab() {
        return this.selectedSuperTab;
    }
    getSelectedSubTab() {
        return this.selectedSubTab;
    }
};
TabService = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Injectable"])({
        providedIn: 'root'
    })
], TabService);



/***/ }),

/***/ "./src/app/tab/tabarea-sub/tabarea-sub.component.less":
/*!************************************************************!*\
  !*** ./src/app/tab/tabarea-sub/tabarea-sub.component.less ***!
  \************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "#tabarea-sub-container {\n  width: 95%;\n  height: 10%;\n  text-align: center;\n  display: flex;\n  margin: auto;\n}\n.tab-sub,\n.tab-sub-selected {\n  font-size: 1.6em;\n  font-weight: bold;\n  font-family: sans-serif;\n  color: black;\n  text-decoration: underline;\n  margin-left: 1vw;\n  float: bottom;\n}\n.tab-sub__text:hover {\n  color: blue;\n  cursor: pointer;\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi9Vc2Vycy9tYXh3ZWxsaWxpZS9QeWNoYXJtUHJvamVjdHMvVEMyL2Zyb250ZW5kL2FuZ3VsYXItYXBwL3NyYy9hcHAvdGFiL3RhYmFyZWEtc3ViL3RhYmFyZWEtc3ViLmNvbXBvbmVudC5sZXNzIiwic3JjL2FwcC90YWIvdGFiYXJlYS1zdWIvdGFiYXJlYS1zdWIuY29tcG9uZW50Lmxlc3MiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBSUE7RUFDRSxVQUFBO0VBQ0EsV0FBQTtFQUNBLGtCQUFBO0VBQ0EsYUFBQTtFQUNBLFlBQUE7QUNIRjtBRE1BOztFQUNFLGdCQUFBO0VBQ0EsaUJBQUE7RUFDQSx1QkFBQTtFQUNBLFlBQUE7RUFDQSwwQkFBQTtFQUNBLGdCQUFBO0VBQ0EsYUFBQTtBQ0hGO0FETUE7RUFDRSxXQUFBO0VBQ0EsZUFBQTtBQ0pGIiwiZmlsZSI6InNyYy9hcHAvdGFiL3RhYmFyZWEtc3ViL3RhYmFyZWEtc3ViLmNvbXBvbmVudC5sZXNzIiwic291cmNlc0NvbnRlbnQiOlsiQHRhYkFyZWFXaWR0aDogOTUlO1xuQHRhYldpZHRoOiAyMCU7XG5AdGFiSGVpZ2h0OiAxMCU7XG5cbiN0YWJhcmVhLXN1Yi1jb250YWluZXIge1xuICB3aWR0aDogQHRhYkFyZWFXaWR0aDtcbiAgaGVpZ2h0OiBAdGFiSGVpZ2h0O1xuICB0ZXh0LWFsaWduOiBjZW50ZXI7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIG1hcmdpbjogYXV0bztcbn1cblxuLnRhYi1zdWIsIC50YWItc3ViLXNlbGVjdGVkIHtcbiAgZm9udC1zaXplOiAxLjZlbTtcbiAgZm9udC13ZWlnaHQ6IGJvbGQ7XG4gIGZvbnQtZmFtaWx5OiBzYW5zLXNlcmlmO1xuICBjb2xvcjogYmxhY2s7XG4gIHRleHQtZGVjb3JhdGlvbjogdW5kZXJsaW5lO1xuICBtYXJnaW4tbGVmdDogMXZ3O1xuICBmbG9hdDogYm90dG9tO1xufVxuXG4udGFiLXN1Yl9fdGV4dDpob3ZlciB7XG4gIGNvbG9yOiBibHVlO1xuICBjdXJzb3I6IHBvaW50ZXI7XG59XG4iLCIjdGFiYXJlYS1zdWItY29udGFpbmVyIHtcbiAgd2lkdGg6IDk1JTtcbiAgaGVpZ2h0OiAxMCU7XG4gIHRleHQtYWxpZ246IGNlbnRlcjtcbiAgZGlzcGxheTogZmxleDtcbiAgbWFyZ2luOiBhdXRvO1xufVxuLnRhYi1zdWIsXG4udGFiLXN1Yi1zZWxlY3RlZCB7XG4gIGZvbnQtc2l6ZTogMS42ZW07XG4gIGZvbnQtd2VpZ2h0OiBib2xkO1xuICBmb250LWZhbWlseTogc2Fucy1zZXJpZjtcbiAgY29sb3I6IGJsYWNrO1xuICB0ZXh0LWRlY29yYXRpb246IHVuZGVybGluZTtcbiAgbWFyZ2luLWxlZnQ6IDF2dztcbiAgZmxvYXQ6IGJvdHRvbTtcbn1cbi50YWItc3ViX190ZXh0OmhvdmVyIHtcbiAgY29sb3I6IGJsdWU7XG4gIGN1cnNvcjogcG9pbnRlcjtcbn1cbiJdfQ== */"

/***/ }),

/***/ "./src/app/tab/tabarea-sub/tabarea-sub.component.ts":
/*!**********************************************************!*\
  !*** ./src/app/tab/tabarea-sub/tabarea-sub.component.ts ***!
  \**********************************************************/
/*! exports provided: TabareaSubComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TabareaSubComponent", function() { return TabareaSubComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../shared_service/tab.service */ "./src/app/shared_service/tab.service.ts");



let TabareaSubComponent = 
/**
 * The content box itself. This component is merely a box that positions and frames the content.
 */
class TabareaSubComponent {
    constructor(tabs) {
        this.tabs = tabs;
        this.tabSuperType = _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_2__["TabSuperType"];
        this.tabSubType = _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_2__["TabSubType"];
    }
    ngOnInit() {
    }
};
TabareaSubComponent.ctorParameters = () => [
    { type: _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_2__["TabService"] }
];
TabareaSubComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-tabarea-sub',
        template: __webpack_require__(/*! raw-loader!./tabarea-sub.component.html */ "./node_modules/raw-loader/index.js!./src/app/tab/tabarea-sub/tabarea-sub.component.html"),
        styles: [__webpack_require__(/*! ./tabarea-sub.component.less */ "./src/app/tab/tabarea-sub/tabarea-sub.component.less")]
    })
    /**
     * The content box itself. This component is merely a box that positions and frames the content.
     */
], TabareaSubComponent);



/***/ }),

/***/ "./src/app/tab/tabarea-super/tabarea-super.component.less":
/*!****************************************************************!*\
  !*** ./src/app/tab/tabarea-super/tabarea-super.component.less ***!
  \****************************************************************/
/*! no static exports found */
/***/ (function(module, exports) {

module.exports = "#tabarea-super-container {\n  display: flex;\n  margin: auto;\n  width: 95%;\n  height: 10%;\n}\n.tab-super,\n.tab-super-selected {\n  width: 20%;\n  font-size: 1.3em;\n  font-family: sans-serif;\n  color: black;\n  border: 3.5px solid black;\n  border-radius: 3.5px;\n  margin-left: 3%;\n  margin-right: 3%;\n  background: white;\n}\n.tab-super__text,\n.tab-super-selected__text {\n  margin: 0;\n  padding-left: 1%;\n  padding-right: 1%;\n}\n.tab-super-selected,\n.tab-super:hover,\n.tab-super.p:hover {\n  color: white !important;\n  cursor: pointer !important;\n  background: mediumspringgreen !important;\n}\n.selected-super-tab,\n.selected-super-tab.p {\n  color: white;\n  background: mediumspringgreen;\n}\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi9Vc2Vycy9tYXh3ZWxsaWxpZS9QeWNoYXJtUHJvamVjdHMvVEMyL2Zyb250ZW5kL2FuZ3VsYXItYXBwL3NyYy9hcHAvdGFiL3RhYmFyZWEtc3VwZXIvdGFiYXJlYS1zdXBlci5jb21wb25lbnQubGVzcyIsInNyYy9hcHAvdGFiL3RhYmFyZWEtc3VwZXIvdGFiYXJlYS1zdXBlci5jb21wb25lbnQubGVzcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFJQTtFQUNFLGFBQUE7RUFDQSxZQUFBO0VBQ0EsVUFBQTtFQUNBLFdBQUE7QUNIRjtBRE1BOztFQUNFLFVBQUE7RUFDQSxnQkFBQTtFQUNBLHVCQUFBO0VBQ0EsWUFBQTtFQUNBLHlCQUFBO0VBQ0Esb0JBQUE7RUFDQSxlQUFBO0VBQ0EsZ0JBQUE7RUFDQSxpQkFBQTtBQ0hGO0FETUE7O0VBQ0UsU0FBQTtFQUNBLGdCQUFBO0VBQ0EsaUJBQUE7QUNIRjtBRE1BOzs7RUFDRSx1QkFBQTtFQUNBLDBCQUFBO0VBQ0Esd0NBQUE7QUNGRjtBREtBOztFQUNFLFlBQUE7RUFDQSw2QkFBQTtBQ0ZGIiwiZmlsZSI6InNyYy9hcHAvdGFiL3RhYmFyZWEtc3VwZXIvdGFiYXJlYS1zdXBlci5jb21wb25lbnQubGVzcyIsInNvdXJjZXNDb250ZW50IjpbIkB0YWJBcmVhV2lkdGg6IDk1JTtcbkB0YWJXaWR0aDogMjAlO1xuQHRhYkhlaWdodDogMTAlO1xuXG4jdGFiYXJlYS1zdXBlci1jb250YWluZXIge1xuICBkaXNwbGF5OiBmbGV4O1xuICBtYXJnaW46IGF1dG87XG4gIHdpZHRoOiBAdGFiQXJlYVdpZHRoO1xuICBoZWlnaHQ6IEB0YWJIZWlnaHQ7XG59XG5cbi50YWItc3VwZXIsIC50YWItc3VwZXItc2VsZWN0ZWQge1xuICB3aWR0aDogQHRhYldpZHRoO1xuICBmb250LXNpemU6IDEuM2VtO1xuICBmb250LWZhbWlseTogc2Fucy1zZXJpZjtcbiAgY29sb3I6IGJsYWNrO1xuICBib3JkZXI6IDMuNXB4IHNvbGlkIGJsYWNrO1xuICBib3JkZXItcmFkaXVzOiAzLjVweDtcbiAgbWFyZ2luLWxlZnQ6IDMlO1xuICBtYXJnaW4tcmlnaHQ6IDMlO1xuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcbn1cblxuLnRhYi1zdXBlcl9fdGV4dCwgLnRhYi1zdXBlci1zZWxlY3RlZF9fdGV4dCB7XG4gIG1hcmdpbjogMDtcbiAgcGFkZGluZy1sZWZ0OiAxJTtcbiAgcGFkZGluZy1yaWdodDogMSU7XG59XG5cbi50YWItc3VwZXItc2VsZWN0ZWQsIC50YWItc3VwZXI6aG92ZXIsIC50YWItc3VwZXIucDpob3ZlciB7XG4gIGNvbG9yOiB3aGl0ZSAhaW1wb3J0YW50O1xuICBjdXJzb3I6IHBvaW50ZXIgIWltcG9ydGFudDtcbiAgYmFja2dyb3VuZDogbWVkaXVtc3ByaW5nZ3JlZW4gIWltcG9ydGFudDtcbn1cblxuLnNlbGVjdGVkLXN1cGVyLXRhYiwgLnNlbGVjdGVkLXN1cGVyLXRhYi5wIHtcbiAgY29sb3I6IHdoaXRlO1xuICBiYWNrZ3JvdW5kOiBtZWRpdW1zcHJpbmdncmVlbjtcbn1cbiIsIiN0YWJhcmVhLXN1cGVyLWNvbnRhaW5lciB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIG1hcmdpbjogYXV0bztcbiAgd2lkdGg6IDk1JTtcbiAgaGVpZ2h0OiAxMCU7XG59XG4udGFiLXN1cGVyLFxuLnRhYi1zdXBlci1zZWxlY3RlZCB7XG4gIHdpZHRoOiAyMCU7XG4gIGZvbnQtc2l6ZTogMS4zZW07XG4gIGZvbnQtZmFtaWx5OiBzYW5zLXNlcmlmO1xuICBjb2xvcjogYmxhY2s7XG4gIGJvcmRlcjogMy41cHggc29saWQgYmxhY2s7XG4gIGJvcmRlci1yYWRpdXM6IDMuNXB4O1xuICBtYXJnaW4tbGVmdDogMyU7XG4gIG1hcmdpbi1yaWdodDogMyU7XG4gIGJhY2tncm91bmQ6IHdoaXRlO1xufVxuLnRhYi1zdXBlcl9fdGV4dCxcbi50YWItc3VwZXItc2VsZWN0ZWRfX3RleHQge1xuICBtYXJnaW46IDA7XG4gIHBhZGRpbmctbGVmdDogMSU7XG4gIHBhZGRpbmctcmlnaHQ6IDElO1xufVxuLnRhYi1zdXBlci1zZWxlY3RlZCxcbi50YWItc3VwZXI6aG92ZXIsXG4udGFiLXN1cGVyLnA6aG92ZXIge1xuICBjb2xvcjogd2hpdGUgIWltcG9ydGFudDtcbiAgY3Vyc29yOiBwb2ludGVyICFpbXBvcnRhbnQ7XG4gIGJhY2tncm91bmQ6IG1lZGl1bXNwcmluZ2dyZWVuICFpbXBvcnRhbnQ7XG59XG4uc2VsZWN0ZWQtc3VwZXItdGFiLFxuLnNlbGVjdGVkLXN1cGVyLXRhYi5wIHtcbiAgY29sb3I6IHdoaXRlO1xuICBiYWNrZ3JvdW5kOiBtZWRpdW1zcHJpbmdncmVlbjtcbn1cbiJdfQ== */"

/***/ }),

/***/ "./src/app/tab/tabarea-super/tabarea-super.component.ts":
/*!**************************************************************!*\
  !*** ./src/app/tab/tabarea-super/tabarea-super.component.ts ***!
  \**************************************************************/
/*! exports provided: TabareaSuperComponent */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "TabareaSuperComponent", function() { return TabareaSuperComponent; });
/* harmony import */ var tslib__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! tslib */ "./node_modules/tslib/tslib.es6.js");
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../../shared_service/tab.service */ "./src/app/shared_service/tab.service.ts");



let TabareaSuperComponent = 
/**
 * The content box itself. This component is merely a box that positions and frames the content.
 */
class TabareaSuperComponent {
    constructor(tabs) {
        this.tabs = tabs;
        this.tabSuperType = _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_2__["TabSuperType"];
    }
    ngOnInit() {
    }
};
TabareaSuperComponent.ctorParameters = () => [
    { type: _shared_service_tab_service__WEBPACK_IMPORTED_MODULE_2__["TabService"] }
];
TabareaSuperComponent = tslib__WEBPACK_IMPORTED_MODULE_0__["__decorate"]([
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_1__["Component"])({
        selector: 'app-tabarea-super',
        template: __webpack_require__(/*! raw-loader!./tabarea-super.component.html */ "./node_modules/raw-loader/index.js!./src/app/tab/tabarea-super/tabarea-super.component.html"),
        styles: [__webpack_require__(/*! ./tabarea-super.component.less */ "./src/app/tab/tabarea-super/tabarea-super.component.less")]
    })
    /**
     * The content box itself. This component is merely a box that positions and frames the content.
     */
], TabareaSuperComponent);



/***/ }),

/***/ "./src/environments/environment.ts":
/*!*****************************************!*\
  !*** ./src/environments/environment.ts ***!
  \*****************************************/
/*! exports provided: environment */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "environment", function() { return environment; });
// This file can be replaced during build by using the `fileReplacements` array.
// `ng build --prod` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.
const environment = {
    production: false,
    apiUrl: 'http://stocks.maxilie.com:9100/api',
};
/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/dist/zone-error';  // Included with Angular CLI.


/***/ }),

/***/ "./src/main.ts":
/*!*********************!*\
  !*** ./src/main.ts ***!
  \*********************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _angular_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @angular/core */ "./node_modules/@angular/core/fesm2015/core.js");
/* harmony import */ var _angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @angular/platform-browser-dynamic */ "./node_modules/@angular/platform-browser-dynamic/fesm2015/platform-browser-dynamic.js");
/* harmony import */ var _app_app_module__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./app/app.module */ "./src/app/app.module.ts");
/* harmony import */ var _environments_environment__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./environments/environment */ "./src/environments/environment.ts");




if (_environments_environment__WEBPACK_IMPORTED_MODULE_3__["environment"].production) {
    Object(_angular_core__WEBPACK_IMPORTED_MODULE_0__["enableProdMode"])();
}
Object(_angular_platform_browser_dynamic__WEBPACK_IMPORTED_MODULE_1__["platformBrowserDynamic"])().bootstrapModule(_app_app_module__WEBPACK_IMPORTED_MODULE_2__["AppModule"])
    .catch(err => console.error(err));


/***/ }),

/***/ 0:
/*!***************************!*\
  !*** multi ./src/main.ts ***!
  \***************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(/*! /Users/maxwellilie/PycharmProjects/TC2/frontend/angular-app/src/main.ts */"./src/main.ts");


/***/ })

},[[0,"runtime","vendor"]]]);
//# sourceMappingURL=main-es2015.js.map
