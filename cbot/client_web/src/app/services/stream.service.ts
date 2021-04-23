/**
 * stream.service
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

import { EventEmitter, Inject, Injectable } from '@angular/core';
import { APP_BASE_HREF } from '@angular/common';
import { BehaviorSubject } from 'rxjs';
import { Task } from '../task/task';

export enum StreamType {
    BIN_LIVE_UPDATE = 'BIN_LIVE_UPDATE',
    CLONE_TASK = 'CLONE_TASK',
    CMC_LATEST_UPDATE = 'CMC_LATEST_UPDATE',
    CRYPTO_STATS = 'CRYPTO_STATS',
    CRYPTO_TSL_UPDATE = 'CRYPTO_TSL_UPDATE',
    LOGGER = 'LOGGER',
    MODIFY_TASK = 'MODIFY_TASK',
    RESULT = 'RESULT',
    STREAM_TICKERS = 'STREAM_TICKERS',
    TASK_FINISHED = 'TASK_FINISHED',
    TASK_INFO = 'TASK_INFO',
    TASK_MANAGER = 'TASK_MANAGER',
    TASK_MODIFIED = 'TASK_MODIFIED',
    TICKER_UPDATE = 'TICKER_UPDATE',
}

export interface StreamEvent {
    type: StreamType,
    taskId?: number;
    data: any;
}

@Injectable({
    providedIn: 'root'
})
export class StreamService {

    endpoint: string;
    event: EventEmitter<StreamEvent> = new EventEmitter();
    isConnected: boolean = false;
    isOnline: boolean = window.navigator.onLine;
    isOnline$ = new BehaviorSubject<boolean>(window.navigator.onLine);
    ws!: WebSocket;

    constructor(@Inject(APP_BASE_HREF) private baseHref: string) {
        const loc = window.location;
        const host = (!loc || loc.hostname === 'localhost') ?
            'localhost:2269' : `${loc.hostname}:${loc.port}`;
        this.endpoint = (loc.protocol === 'https:' ? 'wss://' : 'ws://') +
            host + baseHref + 'stream';
        this.listenToOnlineStatus();
    }

    enable(onReady: Function = () => {}) {
        this.ws = new WebSocket(this.endpoint);
        this.ws.onopen = () => {
            this.isConnected = true;
            onReady();
        };
        this.ws.onmessage = (event: MessageEvent) => {
            this.processResponse(event.data);
        };
        this.ws.onclose = (event: CloseEvent) => {
            this.isConnected = false;
            if (event.code !== 1000 && this.isOnline) {
                setTimeout(() => {
                    let ws2 = new WebSocket(this.endpoint);
                    ws2.onopen = this.ws.onopen;
                    ws2.onmessage = this.ws.onmessage;
                    ws2.onclose = this.ws.onclose;
                    this.ws = ws2;
                }, 5000);
            }
        };
    }

    disable() {
        if (this.ws) {
            this.ws.close(1000);
        }
    }

    listenToOnlineStatus() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.isOnline$.next(true);
        });
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.isOnline$.next(false);
        });
    }

    send(data: any) {
        let payload = JSON.stringify(data);
        this.ws.send(payload);
    }

    callCmd(cmd: string, args: string[] = [], kwargs: any = {}) {
        this.send({
            cmd: cmd,
            args: args,
            kwargs: kwargs,
        });
    }

    callCmdRaw(cmd: string) {
        this.send({raw_input: cmd})
    }

    processResponse(payload: any) {
        let d = JSON.parse(payload);
        let stream = d.stream;
        let data = d.data;
        switch (stream) {
            case StreamType.LOGGER:
                let ts = data.ts;
                let time = parseInt(ts.toString().split('.')[0], 10);
                let taskId = data.taskId;
                let msg = data.msg;
                this.emitLogger(new Date(time * 1000).toISOString() +
                    ` ${taskId} - ${msg}`, taskId);
                break;
            case StreamType.BIN_LIVE_UPDATE:
            case StreamType.CMC_LATEST_UPDATE:
            case StreamType.CRYPTO_STATS:
            case StreamType.CRYPTO_TSL_UPDATE:
            case StreamType.STREAM_TICKERS:
            case StreamType.TASK_FINISHED:
            case StreamType.TASK_INFO:
            case StreamType.TASK_MANAGER:
            case StreamType.TASK_MODIFIED:
            case StreamType.TICKER_UPDATE:
                this.emit(stream, data, data.taskId);
                break;
            case StreamType.CLONE_TASK:
            case StreamType.MODIFY_TASK:
                break;
            default:
                const d = data;
                if (d.output && typeof d.output === 'string') {
                    this.emitLogger(d.output);
                }
                else if (d.output && Array.isArray(d.output)) {
                    for (let entry of d.output) {
                        this.emitLogger(entry);
                    }
                }
                else if (d.data && Array.isArray(d.data) && d.cmd !== 'ps') {
                    for (let entry of d.data) {
                        if (typeof entry === 'string') {
                            this.emitLogger(entry);
                        }
                        else {
                            let ts = entry.ts;
                            let time = parseInt(ts.toString().split('.')[0], 10);
                            let taskId = entry.taskId;
                            this.emitLogger(new Date(time * 1000).toISOString() +
                                ` ${taskId} - ${entry.msg}`);
                        }
                    }
                }
                else if (!('resp_code' in d)) {
                    this.emitLogger('Unknown: ' + payload);
                }
                this.emit(stream, data, data.taskId);
                break;
        }
    }

    emit(streamType: StreamType, data: any, taskId: number = 0) {
        this.event.emit({
            type: streamType,
            taskId: taskId,
            data: data,
        });
    }

    emitLogger(msg: string, taskId: number = 0) {
        this.event.emit({
            type: StreamType.LOGGER,
            taskId: taskId,
            data: msg,
        });
    }

    emitCloneTask(task: Task) {
        this.emit(StreamType.CLONE_TASK, task);
    }

    emitModifyTask(task: Task) {
        this.emit(StreamType.MODIFY_TASK, task);
    }
}
