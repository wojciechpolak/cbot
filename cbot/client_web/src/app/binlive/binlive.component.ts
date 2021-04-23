/**
 * binlive.component
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

import { AfterViewInit, Component, OnDestroy } from '@angular/core';
import { StreamEvent, StreamService, StreamType } from '../services/stream.service';
import { Subscription } from 'rxjs';

@Component({
    selector: 'app-binlive',
    templateUrl: './binlive.component.html',
})
export class AppBinLiveComponent implements AfterViewInit, OnDestroy {

    binLive = [];
    binLiveLastUpdate: Date = new Date();
    streamSub!: Subscription;

    constructor(private streamService: StreamService) {
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
    }

    onStream(event: StreamEvent) {
        if (event.type === StreamType.BIN_LIVE_UPDATE) {
            this.binLive = event.data;
            this.binLiveLastUpdate = new Date();
        }
    }

    isPositive(num: string) {
        return parseFloat(num) > 0;
    }
}
