/**
 * task-card.component
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

import { AfterViewInit, Component, EventEmitter, Inject, Input, OnDestroy, Output } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { TaskService } from '../task.service';
import { StreamEvent, StreamService, StreamType } from '../../services/stream.service';
import { Task } from '../task';
import { UtilsService } from '../../services/utils.service';

@Component({
    selector: 'app-task-card',
    templateUrl: './task-card.component.html',
})
export class AppTaskCardComponent implements AfterViewInit, OnDestroy {

    @Input() task!: Task;
    @Output() switchToTerminal = new EventEmitter();

    private cloningTask: boolean = false;
    private modifyingTask: boolean = false;
    showTaskData = false;
    streamSub!: Subscription;
    UtilsService: typeof UtilsService = UtilsService;

    constructor(public dialog: MatDialog,
                private streamService: StreamService,
                private taskService: TaskService) {
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
        if (event.type === StreamType.TASK_INFO) {
            if (this.task.id === event.taskId) {
                this.task.data = event.data?.info;
                if (this.cloningTask) {
                    this.streamService.emitCloneTask(this.task);
                    this.cloningTask = false;
                }
                else if (this.modifyingTask) {
                    this.streamService.emitModifyTask(this.task);
                    this.modifyingTask = false;
                }
                else {
                    this.showTaskData = true;
                }
            }
        }
    }

    toggleTaskInfo() {
        this.showTaskData = !this.showTaskData;
        if (this.showTaskData) {
            this.taskService.getInfo(this.task.id);
        }
    }

    getTaskOutput() {
        this.taskService.getOutput(this.task.id);
        this.switchToTerminal.emit();
    }

    pauseTask() {
        this.taskService.pause(this.task.id);
    }

    killTask() {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            data: {taskId: this.task.id}
        });
        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.taskService.kill(this.task.id);
            }
        });
    }

    cloneTask() {
        this.cloningTask = true;
        this.taskService.getInfo(this.task.id);
    }

    modifyTask() {
        this.modifyingTask = true;
        this.taskService.getInfo(this.task.id);
    }

    formatData(): string {
        return JSON.stringify(this.task.data, undefined, 4);
    }

    formatOutput(): string {
        if (this.task.name === 'crypto_tsl') {
            let cols = this.task.output?.split(';');
            if (cols?.length > 1) {
                let d_iter = cols[0];
                let d_state = cols[1];
                let d_symbol = cols[2];
                let d_qty = cols[3];
                let d_high = cols[4].replace('H ', 'HIGHEST ');
                let d_cur = cols[5]
                    .replace('CUR ', 'CURRENT ')
                    .replace('PD:', 'PriceDiff: ');
                let d_stop = cols[6].replace('GAP:', 'GAP: ');
                let d_limit = cols[7];
                return `${d_iter}; ${d_state}; ${d_symbol}; ${d_qty}<br>
${d_high}<br>${d_cur}<br>${d_stop}; ${d_limit}`;
            }
        }
        return this.task.output;
    }
}

@Component({
  selector: 'app-confirm-dialog',
  template: `
      <h2 mat-dialog-title>Confirm</h2>
      <mat-dialog-content class="mat-typography">
          <h3>Do you want to kill process #{{ data.taskId }}?</h3>
      </mat-dialog-content>
      <mat-dialog-actions align="end">
          <button mat-button mat-dialog-close>Cancel</button>
          <button mat-button [mat-dialog-close]="true" cdkFocusInitial>Yes!</button>
      </mat-dialog-actions>`
})
export class ConfirmDialogComponent {
    constructor(@Inject(MAT_DIALOG_DATA) public data: any) {
    }
}
