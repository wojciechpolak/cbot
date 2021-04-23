/**
 * app.component
 *
 * CBot Copyright (C) 2022 Wojciech Polak
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation; either version 3 of the License, or (at your
 * option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

import { AfterViewInit, ApplicationRef, Component, OnDestroy, OnInit } from '@angular/core';
import { SwUpdate } from '@angular/service-worker';
import { MatSnackBar } from '@angular/material/snack-bar';
import { concat, interval, Subscription } from 'rxjs';
import { first } from 'rxjs/operators';

import { StreamEvent, StreamService, StreamType } from './services/stream.service';

enum Tabs {
    TERMINAL = 0,
    TASKS = 1,
    BIN_LIVE = 2,
    TICKERS = 3,
    STATUS = 4,
}

@Component({
    selector: 'app-root',
    templateUrl: './app.component.html',
})
export class AppComponent implements AfterViewInit, OnDestroy, OnInit {

    binLiveLastUpdate: Date = new Date();
    binLiveNotification: boolean = false;
    binLiveTickers = [];
    currentTab: Tabs = Tabs.TASKS;
    selectedTabIndex: number = 1;
    streamSub!: Subscription;
    Tabs: typeof Tabs = Tabs;

    constructor(private appRef: ApplicationRef,
                private swUpdate: SwUpdate,
                private snackBar: MatSnackBar,
                private streamService: StreamService) {
    }

    ngOnInit() {
        this.streamService.isOnline$.subscribe((isOnline: boolean) => {
            if (isOnline) {
                this.streamService.enable(() => {
                    this.streamService.callCmd('ps');
                });
            }
            else {
                this.streamService.disable();
            }
        });

        this.swUpdate.versionUpdates.subscribe(evt => {
            switch (evt.type) {
                case 'VERSION_DETECTED':
                    this.streamService.emitLogger(`Downloading new app version: ${evt.version.hash}`);
                    break;
                case 'VERSION_READY':
                    this.streamService.emitLogger(`Current app version: ${evt.currentVersion.hash}`);
                    this.streamService.emitLogger(`New app version ready for use: ${evt.latestVersion.hash}`);
                    let snack = this.snackBar.open('New app version is available.', 'Reload');
                    snack.onAction().subscribe(() => {
                        this.swUpdate.activateUpdate()
                            .then(() => document.location.reload());
                    });
                    break;
                case 'VERSION_INSTALLATION_FAILED':
                    this.streamService.emitLogger(`Failed to install app version '${evt.version.hash}': ${evt.error}`);
                    break;
            }
        });

        this.swUpdate.unrecoverable.subscribe(event => {
            let snack = this.snackBar.open(
                `An error occurred that we cannot recover from: ${event.reason}`, 'Reload');
            snack.onAction().subscribe(() => {
                document.location.reload();
            });
        });

        if (this.swUpdate.isEnabled) {
            const appIsStable$ = this.appRef.isStable.pipe(first(isStable => isStable));
            const updateHourInterval = 6;
            const updateInterval$ = interval(updateHourInterval * 60 * 60 * 1000);
            const updateChecker = concat(appIsStable$, updateInterval$);
            updateChecker.subscribe(() => this.swUpdate.checkForUpdate());
        }
    }

    ngAfterViewInit() {
        this.streamSub = this.streamService.event.subscribe((data: StreamEvent) => {
            this.onStream(data);
        });
    }

    ngOnDestroy() {
        if (this.streamSub) {
            this.streamSub.unsubscribe();
        }
        this.streamService.disable();
    }

    get isConnected() {
        return this.streamService.isConnected;
    }

    onStream(event: StreamEvent) {
        if (event.type === StreamType.BIN_LIVE_UPDATE) {
            let newDate = new Date();
            this.binLiveNotification = newDate > this.binLiveLastUpdate;
        }
        else if (event.type === StreamType.STREAM_TICKERS) {
            this.binLiveTickers = event.data;
        }
    }

    onTabChange(tabIndex: number) {
        this.currentTab = tabIndex;
        if (this.currentTab !== Tabs.BIN_LIVE) {
            this.binLiveNotification = false;
        }
        if (this.currentTab === Tabs.STATUS) {
            this.streamService.callCmd('stats');
        }
    }

    switchToTerminalTab() {
        this.currentTab = Tabs.TERMINAL;
        this.selectedTabIndex = 0;
    }
}
