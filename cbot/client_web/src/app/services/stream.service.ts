/**
 * stream.service
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

export interface StreamResult {
    type: StreamType.RESULT;
    data: {
        cmd: string;
        data: {
            taskId: number;
            msg: string;
        }[];
    };
}

export interface StreamLogger {
    type: StreamType.LOGGER;
    taskId: number;
    data: string;
}

export interface StreamTaskInfo {
    type: StreamType.TASK_INFO;
    taskId: number;
    data: {
        info: string;
    }
}

export interface StreamTaskManager {
    type: StreamType.TASK_MANAGER;
    data: {
        tasks: Task[];
    }
}

export interface StreamCloneTask {
    type: StreamType.CLONE_TASK;
    data: Task;
}

export interface StreamModifyTask {
    type: StreamType.MODIFY_TASK;
    data: Task;
}

export interface StreamCryptoTslUpdate {
    type: StreamType.CRYPTO_TSL_UPDATE;
    taskId: number;
    data: string;
}

export interface BinLive {
    s: string;
    '1m': string;
    '3m': string;
    '5m': string;
    '10m': string;
    '15m': string;
}

export interface StreamBinLiveUpdate {
    type: StreamType.BIN_LIVE_UPDATE;
    data: BinLive[];
}

export interface BinLiveTicker {
    s: string;
    c: string;
    P: string;
}

export interface StreamTickers {
    type: StreamType.STREAM_TICKERS;
    data: BinLiveTicker[];
}

export type StreamEvent =
    StreamBinLiveUpdate |
    StreamCloneTask |
    StreamCryptoTslUpdate |
    StreamLogger |
    StreamModifyTask |
    StreamResult |
    StreamTaskInfo |
    StreamTaskManager |
    StreamTickers;

type AllowedStreamTypes = StreamEvent['type'];

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

    enable(onReady: () => void = () => {}) {
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
                    const ws2 = new WebSocket(this.endpoint);
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

    send(data: unknown) {
        const payload = JSON.stringify(data);
        this.ws.send(payload);
    }

    callCmd(cmd: string, args: string[] = [], kwargs: object = {}) {
        this.send({
            cmd: cmd,
            args: args,
            kwargs: kwargs,
        });
    }

    callCmdRaw(cmd: string) {
        this.send({raw_input: cmd})
    }

    processResponse(payload: string) {
        const d = JSON.parse(payload);
        const stream = d.stream;
        const data = d.data;
        switch (stream) {
            case StreamType.LOGGER:
                const ts = data.ts;
                const time = parseInt(ts.toString().split('.')[0], 10);
                const taskId = data.taskId;
                const msg = data.msg;
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
                    for (const entry of d.output) {
                        this.emitLogger(entry);
                    }
                }
                else if (d.data && Array.isArray(d.data) && d.cmd !== 'ps') {
                    for (const entry of d.data) {
                        if (typeof entry === 'string') {
                            this.emitLogger(entry);
                        }
                        else {
                            const ts = entry.ts;
                            const time = parseInt(ts.toString().split('.')[0], 10);
                            const taskId = entry.taskId;
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

    // eslint-disable-next-line
    emit(streamType: AllowedStreamTypes, data: any, taskId: number = 0) {
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
