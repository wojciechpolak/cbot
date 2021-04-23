/**
 * status.component
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
import { Subscription } from 'rxjs';
import { StreamEvent, StreamService, StreamType } from '../services/stream.service';
import { environment } from '../../environments/environment';

@Component({
    selector: 'app-status',
    templateUrl: './status.component.html',
})
export class AppStatusComponent implements AfterViewInit, OnDestroy {

    streamSub!: Subscription;
    stats: any;
    version: any = environment.version;

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
        if (event.type === StreamType.RESULT && event.data.cmd === 'stats') {
            this.stats = event.data.data;
            this.stats = JSON.stringify(this.stats, undefined, 4);
        }
    }
}
