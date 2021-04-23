/**
 * task-list.component
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

import { AfterViewInit, ChangeDetectorRef, Component, EventEmitter, OnDestroy, Output } from '@angular/core';
import { Subscription } from 'rxjs';
import { StreamEvent, StreamService, StreamType } from '../../services/stream.service';
import { TaskService } from '../task.service';
import { Task } from '../task';

export const TaskList = [
    'bin_live',
    'clean',
    'cmc_latest',
    'cron',
    'crypto_order',
    'crypto_pf',
    'crypto_stats',
    'crypto_ticker',
    'crypto_tsl',
    'get',
    'ifttt',
    'info',
    'kill',
    'ls',
    'memstore',
    'modify',
    'pause',
    'ping',
    'ps',
    'reload',
    'savegame',
    'sendmail',
    'stats',
];

@Component({
    selector: 'app-task-list',
    templateUrl: './task-list.component.html',
})
export class AppTaskListComponent implements AfterViewInit, OnDestroy {

    cloneTask: Task | null = null;
    modifyTask: Task | null = null;
    createMode: boolean = false;
    streamSub!: Subscription;
    tasksFinished: Task[] = [];
    tasksRunning: Task[] = [];

    @Output() switchToTerminal = new EventEmitter();

    constructor(private cd: ChangeDetectorRef,
                private taskService: TaskService,
                private streamService: StreamService) {
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
        if (event.type === StreamType.LOGGER) {
            let task = this.tasksRunning.find(item => item.id === event.taskId)
            if (task && ('' + event.data).length < 200) {
                task.output = event.data;
            }
        }
        else if (event.type === StreamType.RESULT && event.data.cmd === 'get') {
            const data = event.data.data;
            for (let entry of data) {
                let task = this.tasksRunning.find(item => item.id === entry.taskId);
                if (task && ('' + entry.msg).length < 200) {
                    task.output = entry.msg;
                }
            }
        }
        else if (event.type === StreamType.TASK_MANAGER) {
            const tasks = event.data.tasks as Task[];
            if (!this.tasksRunning.length) {
                this.streamService.callCmd('get', ['-1', '1']);
            }
            this.tasksRunning = tasks.filter(item => !item.is_finished);
            this.tasksFinished = tasks.filter(item => item.is_finished);
        }
        else if (event.type === StreamType.CRYPTO_TSL_UPDATE) {
            let task = this.tasksRunning.find(item => item.id === event.taskId)
            if (task && event.taskId) {
                task.data = event.data;
            }
        }
        else if (event.type === StreamType.CLONE_TASK) {
            this.closeCreateTask();
            this.cd.detectChanges();
            this.cloneTask = event.data as Task;
            this.modifyTask = null;
            this.openCreateTask();
        }
        else if (event.type === StreamType.MODIFY_TASK) {
            this.closeCreateTask();
            this.cd.detectChanges();
            this.modifyTask = event.data as Task;
            this.cloneTask = null;
            this.openCreateTask();
        }
    }

    cleanTasks() {
        this.taskService.clean();
    }

    openCreateTask(clean: boolean = false) {
        if (clean) {
            this.cloneTask = null;
            this.modifyTask = null;
        }
        this.createMode = true;
    }

    closeCreateTask() {
        this.createMode = false;
    }
}
