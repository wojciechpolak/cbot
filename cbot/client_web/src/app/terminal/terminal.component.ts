/**
 * terminal.component
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

import { AfterViewInit, Component, OnDestroy, OnInit } from '@angular/core';
import { UntypedFormControl } from '@angular/forms';
import { MatCheckboxChange } from '@angular/material/checkbox';
import { Observable, Subscription } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { StreamEvent, StreamService, StreamType } from '../services/stream.service';
import { TaskList } from '../task/list/task-list.component';

@Component({
    selector: 'app-terminal',
    templateUrl: './terminal.component.html',
})
export class AppTerminalComponent implements AfterViewInit, OnDestroy, OnInit {

    cmd_options: string[] = TaskList;
    filteredOptions!: Observable<string[]>;
    inputControl = new UntypedFormControl();
    is_debug: boolean = false;
    streamSub!: Subscription;

    constructor(private streamService: StreamService) {
    }

    ngOnInit() {
        this.log('Welcome!');
        this.filteredOptions = this.inputControl.valueChanges
            .pipe(
                startWith(''),
                map(value => this._filter(value))
            );
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

    onEnter($event: Event) {
        $event.preventDefault();
        let dom_input = (document.querySelector('#input') as HTMLInputElement);
        if (!dom_input) {
            return;
        }
        let input = dom_input.value;
        if (!input) {
            return;
        }
        this.log('$ ' + input);
        if (input.toLowerCase() === 'reset') {
            this.resetTerminal()
            return;
        }
        let d = {
            raw_input: input
        }
        let payload = JSON.stringify(d);
        if (this.is_debug) {
            this.log('SEND ' + payload);
        }
        this.streamService.send(d);
        dom_input.value = '';
    }

    log(msg: string) {
        let message = document.createElement('li');
        let content = document.createTextNode(msg);
        message.appendChild(content);
        let output = document.querySelector('#output') as HTMLDivElement;
        if (output) {
            output.appendChild(message);
            output.scrollTop = output.scrollHeight;
        }
    }

    onStream(event: StreamEvent) {
        if (event.type === StreamType.LOGGER) {
            this.log(event.data);
        }
    }

    onDebugCheck(event: MatCheckboxChange) {
       this.is_debug = event.checked;
    }

    resetTerminal() {
        let output = document.querySelector('#output') as HTMLDivElement;
        if (output) {
            output.innerHTML = '';
        }
    }

    private _filter(value: string): string[] {
        const filterValue = value.toLowerCase();
        return this.cmd_options
            .filter((option: string) => option.toLowerCase().includes(filterValue));
    }
}
