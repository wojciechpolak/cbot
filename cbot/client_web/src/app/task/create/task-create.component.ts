/**
 * task-create.component
 *
 * CBot Copyright (C) 2022-2025 Wojciech Polak
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

import { Component, OnInit, inject, input, output } from '@angular/core';
import { UntypedFormControl, UntypedFormGroup, Validators, ReactiveFormsModule } from '@angular/forms';

import { AppMaterialModules } from '../../app-modules';
import { StreamService } from '../../services/stream.service';
import { Task, TaskInput, TaskMap } from '../task';
import { UtilsService } from '../../services/utils.service';

const TaskCommonInputs: TaskInput[] = [
    {name: 'cron'},
    {name: 'desc'},
    {name: 'ifttt'},
    {name: 'args'},
]

export const TaskCreateMap: TaskMap = {
    'ping': [
        ...TaskCommonInputs,
        {name: 'max_iter', type: 'number'},
        {name: 'interval', type: 'number'},
    ],
    'crypto_order': [
        ...TaskCommonInputs,
        {name: 'simulate', type: 'checkbox', default: true},
        {name: 'buy', type: 'checkbox'},
        {name: 'sell', type: 'checkbox'},
        {name: 'orderTypeLimit', type: 'checkbox'},
        {name: 'orderTypeMarket', type: 'checkbox'},
        {name: 'orderTypeStopLoss', type: 'checkbox'},
        {name: 'orderTypeStopLossLimit', type: 'checkbox'},
        {name: 'orderTypeTakeProfit', type: 'checkbox'},
        {name: 'orderTypeTakeProfitLimit', type: 'checkbox'},
        {name: 'exchange'},
        {name: 'symbol'},
        {name: 'price', type: 'float'},
        {name: 'quantity', type: 'float'},
        {name: 'quoteOrderQty', type: 'float'},
        {name: 'stopPrice', type: 'float'},
    ],
    'crypto_pf': [
        ...TaskCommonInputs,
        {name: 'exchange'},
        {name: 'symbol'},
    ],
    'crypto_tsl': [
        ...TaskCommonInputs,
        {name: 'simulate', type: 'checkbox', default: true},
        {name: 'endless', type: 'checkbox'},
        {name: 'buy', type: 'checkbox'},
        {name: 'exchange'},
        {name: 'symbol', required: true},
        {name: 'algo', default: 'std1'},
        {name: 'quantity', type: 'float'},
        {name: 'aboveInitialPrice', type: 'checkbox'},
        {name: 'aboveInitialPriceOffset', type: 'float'},
        {name: 'aboveInitialPriceOffsetPct', type: 'float'},
        {name: 'initialPrice', type: 'float'},
        {name: 'interval', type: 'number'},
        {name: 'lastHigh', type: 'float'},
        {name: 'quoteOrderQty', type: 'float'},
        {name: 'stopLoss', type: 'checkbox'},
        {name: 'stopOffsetPrice', type: 'float'},
        {name: 'stopOffsetPricePct', type: 'float'},
        {name: 'takeProfit', type: 'float'},
        {name: 'takeProfitPct', type: 'float'},
    ],
    'crypto_stats': [
        ...TaskCommonInputs,
        {name: 'exchange'},
        {name: 'limit', type: 'number'},
        {name: 'symbol'},
        {name: 'timeframe'},
    ],
    'crypto_ticker': [
        ...TaskCommonInputs,
        {name: 'exchange'},
        {name: 'symbol'},
    ],
    'cmc_latest': [
        ...TaskCommonInputs,
        {name: 'num', type: 'number'},
        {name: 'quote'},
        {name: 'sortby'},
    ],
    'bin_live': [
        ...TaskCommonInputs,
        {name: 'streams'},
        {name: 'streamAllTickers', type: 'checkbox'},
        {name: 'sortby'},
        {name: 'symbol'},
        {name: 'symbolsTrackAdd', type: 'checkbox'},
        {name: 'trackCmcLatest', type: 'checkbox'}
    ],
    'memstore': [
        {name: 'args'},
        {name: 'get'},
        {name: 'raw', type: 'checkbox'},
    ],
};

@Component({
    selector: 'app-task-create',
    templateUrl: './task-create.component.html',
    imports: [
        ...AppMaterialModules,
        ReactiveFormsModule,
    ]
})
export class AppTaskCreateComponent implements OnInit {
    private streamService = inject(StreamService);

    readonly cloneTask = input<Task | null>(null);
    readonly modifyTask = input<Task | null>(null);
    readonly closeCreate = output();

    form = new UntypedFormGroup({});
    formFields: TaskInput[] = [];
    refTask: Task | null = null;
    taskList = [
        'bin_live',
        'cmc_latest',
        'cron',
        'crypto_order',
        'crypto_stats',
        'crypto_ticker',
        'crypto_tsl',
        'ifttt',
        'memstore',
        'ping',
        'savegame',
    ];
    taskRunCmd = [
        'bin_live',
        'cmc_latest',
        'crypto_order',
        'crypto_stats',
        'crypto_ticker',
        'crypto_tsl',
        'ping',
    ];

    ngOnInit() {
        this.buildForm();
    }

    create() {
        let args: string[] = [];
        if (!this.form.valid) {
            return;
        }
        if ('args' in this.form.controls) {
            args = this.form.controls['args'].value?.split(' ') ?? [];
            if (args.length === 1 && args[0].trim() === '') {
                args = [];
            }
        }
        const kwargs: Record<string, string> = {};
        const formValues = this.form.value;
        for (const k in formValues) {
            if (formValues.hasOwnProperty(k)) {
                if (formValues[k] !== null) {
                    if (k !== 'cmd' && k !== 'args') {
                        kwargs[k] = formValues[k];
                    }
                }
            }
        }
        const payload = {
            cmd: this.modifyTask() ? 'MODIFY' : this.form.controls['cmd'].value,
            args: this.modifyTask() ? [this.refTask?.id] : args,
            kwargs: kwargs,
        }
        if (this.taskRunCmd.includes(payload.cmd)) {
            payload.args = [payload.cmd, ...payload.args];
            payload.cmd = 'RUN';
        }
        console.log('PAYLOAD', payload);
        this.streamService.send(payload);
        this.closeCreate.emit();
    }

    cancel() {
        this.closeCreate.emit();
    }

    buildForm(taskName: string = '') {
        const modifyTask = this.modifyTask();
        const cloneTask = this.cloneTask();
        if (cloneTask) {
            this.refTask = cloneTask;
        }
        else if (modifyTask) {
            this.refTask = modifyTask;
        }

        if (this.refTask && UtilsService.taskDataIsOp(this.refTask.data)) {
            taskName = this.refTask.data.op.cmd;
        }

        if (modifyTask) {
            this.form = new UntypedFormGroup({});
        }
        else {
            this.form = new UntypedFormGroup({
                cmd: new UntypedFormControl(),
            });
        }

        const taskDef = TaskCreateMap[taskName] ?? [];
        this.formFields = taskDef;
        for (const d of taskDef) {
            this.form.addControl(d.name, new UntypedFormControl(d.default,
                d.required ? Validators.required : null));
        }
        if (this.refTask && UtilsService.taskDataIsOp(this.refTask.data)) {
            const op = this.refTask.data.op;
            const args = [];
            for (const arg of op.args) {
                if (arg in this.form.controls) {
                    this.form.controls[arg].setValue(true);
                }
                else {
                    args.push(arg);
                }
            }
            this.form.controls['args'].setValue(args.join(' '));
            for (const k in op.kwargs) {
                if (op.kwargs.hasOwnProperty(k)) {
                    this.form.controls[k].setValue(op.kwargs[k]);
                }
            }
        }
        if (!modifyTask) {
            this.form.controls['cmd'].setValue(taskName);
        }
    }

    changeTaskType() {
        this.buildForm(this.form.controls['cmd'].value);
    }
}
