/**
 * utils.service
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

import type { Operation } from '../task/task';

// eslint-disable-next-line @typescript-eslint/no-extraneous-class
export class UtilsService {

    static toDate(ts: number): string {
        const time = parseInt(ts.toString().split('.')[0], 10);
        return new Date(time * 1000)
            .toISOString()
            .replace('T', ' ')
            .replace('Z', ' ');
    }

    static formatFromNow(value: number, lang: string = 'en') {
        if (Intl && Intl.RelativeTimeFormat) {
            const rtf = new Intl.RelativeTimeFormat(lang, {
                style: 'long',
                numeric: 'always'
            });
            const secDiff = Math.floor((new Date().getTime() - value * 1000) / 1000);
            let ret;
            if (secDiff < 60) {
                ret = rtf.format(-secDiff, 'second');
            }
            else if (secDiff < 3600) {
                ret = rtf.format(-Math.floor(secDiff / 60), 'minute');
            }
            else if (secDiff < 86400) {
                ret = rtf.format(-Math.floor(secDiff / 3600), 'hour');
            }
            else {
                ret = rtf.format(-Math.floor(secDiff / 86400), 'day');
            }
            return ret;
        }
        return '';
    }

    static taskDataIsOp(data: unknown): data is {op: Operation} {
        return !!(typeof data === 'object' && data && 'op' in data);
    }
}
