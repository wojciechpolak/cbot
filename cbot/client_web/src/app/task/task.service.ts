/**
 * task.service
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

import { Injectable } from '@angular/core';
import { StreamService } from '../services/stream.service';

@Injectable({
    providedIn: 'root'
})
export class TaskService {

    constructor(private streamService: StreamService) {
    }

    getInfo(id: number) {
        this.streamService.callCmd('info', ['' + id]);
    }

    getOutput(id: number) {
        this.streamService.callCmdRaw(`get ${id}`);
    }

    pause(id: number) {
        this.streamService.callCmd('pause', ['' + id]);
    }

    kill(id: number) {
        this.streamService.callCmd('kill', ['' + id]);
    }

    clean() {
        this.streamService.callCmd('clean');
    }
}
