import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';

import {environment} from '../../../environments/environment';
import {ApiAuthEndpoint} from "./auth-endpoint";
import {ApiDataEndpoint} from "./data-endpoint";
import {ApiLogsEndpoint} from "./logs-endpoint";
import {ApiVisualsEndpoint} from "./visuals-endpoint";
import {ApiHealthChecksEndpoint} from "./health-checks-endpoint";
import {LogFeed} from "../../models/models";
import {ApiStrategyEndpoint} from "./srategy-endpoint";

@Injectable({
    providedIn: 'root'
})
/**
 * A shared service to manage the client's authentication and connection to the backend API.
 */
export class ApiService {

    // Base url: stocks.maxilie.com/api
    API_BASE_URL = environment.apiUrl;

    // Classes containing functionality for each endpoint
    authEndpoint: ApiAuthEndpoint;
    dataEndpoint: ApiDataEndpoint;
    logsEndpoint: ApiLogsEndpoint;
    visualsEndpoint: ApiVisualsEndpoint;
    healthChecksEndpoint: ApiHealthChecksEndpoint;
    strategyEndpoint: ApiStrategyEndpoint;

    constructor(private http: HttpClient) {
        // Initialize endpoint classes
        this.authEndpoint = new ApiAuthEndpoint(http, this.API_BASE_URL + '/token');
        this.dataEndpoint = new ApiDataEndpoint(http, this.API_BASE_URL + '/data');
        this.logsEndpoint = new ApiLogsEndpoint(http, this.API_BASE_URL + '/logs');
        this.visualsEndpoint = new ApiVisualsEndpoint(http, this.API_BASE_URL + '/visuals');
        this.healthChecksEndpoint = new ApiHealthChecksEndpoint(http, this.API_BASE_URL + '/health_checks');
        this.strategyEndpoint = new ApiStrategyEndpoint(http, this.API_BASE_URL + '/strategy');
    }

    /**
     *
     *
     * Authentication endpoint...
     *
     *
     */

    public static getTokenExpiration(): Date {
        return ApiAuthEndpoint.getTokenExpiration();
    }

    public static isAuthenticated(): boolean {
        return ApiAuthEndpoint.isAuthenticated();
    }

    public login(successCallback) {
        this.authEndpoint.login(successCallback);
    }

    public static logout() {
        ApiAuthEndpoint.logout();
    }

    /**
     *
     *
     * Update endpoint...
     *
     *
     */

    /**
     *
     *
     * Logs endpoint...
     *
     *
     */

    public getFeedFiles(logfeed: LogFeed): Observable<String[]> {
        return this.logsEndpoint.getFeedFiles(logfeed);
    }

    public getFeedLatestLines(logfeed: LogFeed): Observable<String[]> {
        return this.logsEndpoint.getFeedLatestLines(logfeed);
    }

    public getFileLines(logfeed: LogFeed, filename: string): Observable<String[]> {
        return this.logsEndpoint.getFileLines(logfeed, filename);
    }

    public clearLogs(): void {
        this.logsEndpoint.clearLogs();
    }

    /**
     *
     *
     * Visuals  endpoint...
     *
     *
     */

    public getVisualData(callback, params: { [p: string]: string }) {
        return this.visualsEndpoint.getVisualData(callback, params);
    }

    public generateVisual(callback, params: { [p: string]: string }) {
        return this.visualsEndpoint.generateVisual(callback, params);
    }

    /**
     *
     *
     * Health checks  endpoint...
     *
     *
     */

    public getHealthCheckData(callback, params: { [p: string]: string }) {
        return this.healthChecksEndpoint.getHealthCheckData(callback, params);
    }

    public performHealthCheck(callback, params: { [p: string]: string }) {
        return this.healthChecksEndpoint.performHealthCheck(callback, params);
    }

    /**
     *
     *
     * Data endpoint...
     *
     *
     */

    public getSymbols(): Observable<String[]> {
        return this.dataEndpoint.getSymbols();
    }

    public getDatesOnFile(symbol: string): Observable<String[]> {
        return this.dataEndpoint.getDatesOnFile(symbol);
    }

    public getWarmupDays(symbol: string, date: Date): Observable<number[]> {
        return this.dataEndpoint.getWarmupDays(symbol, date);
    }

    public patchData(symbols: string, startDate: Date): void {
        return this.dataEndpoint.patchData(symbols, startDate);
    }

    public getDataStatus(): Observable<String> {
        return this.dataEndpoint.getDataStatus();
    }

    public isDataHealing(): Observable<String> {
        return this.dataEndpoint.isDataHealing();
    }

    public isDataPatching(): Observable<String> {
        return this.dataEndpoint.isDataPatching();
    }

    public getSimulationOutput(): Observable<String> {
        return this.dataEndpoint.getSimulationOutput();
    }

    public resetCollectionAttempts(): void {
        return this.dataEndpoint.resetCollectionAttempts();
    }

    public healData(): void {
        return this.dataEndpoint.healData();
    }

    /**
     *
     *
     * Strategy endpoint...
     *
     *
     */

    public getDayStrategies(): Observable<String[]> {
        return this.strategyEndpoint.getDayStrategies();
    }

    public isRunningSimulation(): Observable<String> {
        return this.strategyEndpoint.isRunningSimulation();
    }

    public simulateDayStrategy(symbol: string, strategyId: string, moment: string, warmup_days: number): void {
        return this.strategyEndpoint.simulateDayStrategy(symbol, strategyId, moment, warmup_days);
    }
}
