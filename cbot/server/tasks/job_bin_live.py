"""
# job_bin_live.py
#
# CBot Copyright (C) 2022 Wojciech Polak
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import asyncio
from decimal import Decimal
from typing import List, cast

from binance import AsyncClient, BinanceSocketManager
from binance.enums import KLINE_INTERVAL_1MINUTE

from cbot.server.event_bus import Event, event_bus
from cbot.server.logger import logger
from cbot.server.memstore import memstore
from cbot.server.task import Task
from cbot.server.tasks.data import TaskData
from cbot.server.utils import parse_bool


class Data(TaskData):
    streams: List[str] = ['klines']
    streamAllTickers: bool = False
    symbols: List[str] = []
    symbols_orig: List[str] = []
    symbols_track_add: bool = False
    sortby: str = '5m'
    track_cmc_latest: bool = True
    is_reloading: bool = False

    def map_options(self, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        for arg in args:
            if arg == 'symbolsTrackAdd':
                self.symbols_track_add = True
            elif arg == 'streamAllTickers':
                self.streamAllTickers = True

        for k, v in kwargs.items():
            if k == 'streams':
                self.streams = v.split(',')
            elif k == 'symbol':
                self.symbols = list(map(lambda x: x.replace('/', ''), v.split(',')))
            elif k == 'sortby':
                self.sortby = v
            elif k == 'symbolsTrackAdd':
                self.symbols_track_add = parse_bool(v)
            elif k == 'streamAllTickers':
                self.streamAllTickers = parse_bool(v)
            elif k == 'trackCmcLatest':
                self.track_cmc_latest = parse_bool(v)
            elif k == 'desc':
                pass
            else:
                logger.error('Invalid call argument: %s', k)


async def job_bin_live(task: Task):
    printer = task.printer
    printer(f'Launching task #{task.id} {task.name}')

    if task.data is None:
        task.data = Data()
        task.data.map_options(task.op.args, task.op.kwargs)
    data = task.data

    async def on_cmc_latest_update(new_symbols):
        printer(f'bin_live: Updating symbols from cmc_latest ({len(new_symbols)})')
        data = cast(Data, task.data)
        data.symbols = list(map(lambda x: x.replace('/', ''), new_symbols))
        if data.symbols_track_add:
            for bds in data.symbols_orig:
                if bds not in data.symbols:
                    data.symbols.append(bds)
        task.data.is_reloading = True

    if len(data.symbols) > 0 and data.symbols_track_add:
        data.symbols_orig = data.symbols
        data.symbols = []

    if len(data.symbols) == 0:
        ms = memstore.get('cmc_latest_symbols')
        if ms:
            data.symbols = list(map(lambda x: x.replace('/', ''), ms))
        if data.symbols_track_add:
            for bds in data.symbols_orig:
                if bds not in data.symbols:
                    data.symbols.append(bds)

    if len(data.symbols) == 0:
        task.printer_error('bin_live: No symbols given!')
        task.set_finished()
        return

    if data.track_cmc_latest:
        event_bus.add_listener(Event.CMC_LATEST_UPDATE, on_cmc_latest_update)

    printer('Streams =', data.streams)
    printer('Symbols =', data.symbols)
    printer('Sort by =', data.sortby)

    client = await AsyncClient.create()
    try:
        while not task.is_finished or task.data.is_reloading:
            task.data.is_reloading = False
            await runner(task, client)
        task.set_finished()
    finally:
        await client.close_connection()
        if data.track_cmc_latest:
            event_bus.remove_listener(Event.CMC_LATEST_UPDATE, on_cmc_latest_update)


async def runner(task: Task, client):
    printer = task.printer
    task_data = cast(Data, task.data)
    symbols = task_data.symbols

    data = {}
    tmp = {}
    output = {}

    if 'klines' in task_data.streams:
        printer('Getting klines...')
        for symbol in symbols:
            logger.debug('bin_live::get_klines: %s', symbol)
            klines = await client.get_klines(symbol=symbol, interval=KLINE_INTERVAL_1MINUTE)
            for kline in klines:
                ts_open = kline[0]
                ts_close = kline[6]
                price_open = kline[1]
                price_close = kline[4]
                last_kline = '%s_%s_%s' % (symbol, ts_open, ts_close)
                tmp[last_kline] = [
                    price_open,
                    price_close,
                    ((Decimal(price_close) - Decimal(price_open)) / Decimal(price_open)) * Decimal('100')
                ]
                if symbol not in data:
                    data[symbol] = []
                data[symbol].append(tmp[last_kline])
                del tmp[last_kline]

            sorted_output = calc_output(data, output, symbol)
            memstore.add('bin_live', sorted_output)
            event_bus.emit(Event.BIN_LIVE_UPDATE, sorted_output)

            await asyncio.sleep(0.2)

    bm = BinanceSocketManager(client)

    streams = []
    if 'klines' in task_data.streams:
        streams.extend(list(map(lambda x: x.lower() + '@kline_1m', symbols)))
    if '!ticker@arr' in task_data.streams or task_data.streamAllTickers:
        streams.append('!ticker@arr')

    ms = bm.multiplex_socket(streams)
    tmp = {}

    printer('Streaming...')

    async with ms as t_scm:
        while not task_data.is_reloading and not task.is_finished:
            try:
                res = await asyncio.wait_for(t_scm.recv(), timeout=10)
            except asyncio.TimeoutError:
                res = None
            if not res:
                break
            r = res['data']

            if isinstance(r, dict) and r['e'] == 'kline':
                kline = r['k']
                symbol = r['s']
                is_finished = kline['x']
                ts_open = kline['t']
                ts_close = kline['T']
                price_open = kline['o']
                price_close = kline['c']

                last_kline = '%s_%s_%s' % (symbol, ts_open, ts_close)
                tmp[last_kline] = [
                    price_open,
                    price_close,
                    ((Decimal(price_close) - Decimal(price_open)) / Decimal(price_open)) * Decimal('100')
                ]
                logger.debug('bin_live: %s %s', last_kline, tmp[last_kline])

                if is_finished:
                    max_klines = 1000
                    if symbol not in data:
                        data[symbol] = []
                    else:
                        if len(data[symbol]) >= max_klines:
                            data[symbol] = data[symbol][-max_klines:]  # n-last elements
                    data[symbol].append(tmp[last_kline])
                    del tmp[last_kline]

                    sorted_output = calc_output(data, output, symbol)
                    memstore.add('bin_live', sorted_output)
                    event_bus.emit(Event.BIN_LIVE_UPDATE, sorted_output)

            elif isinstance(r, list):  # Streaming tickers
                tickers = []
                for tick in r:
                    symbol = tick['s']
                    if 'DOWNUSDT' in symbol or 'UPUSDT' in symbol:
                        continue
                    tickers.append({
                        's': tick['s'],  # symbol
                        'c': tick['c'],  # last price
                        'P': tick['P'],  # price change percent
                    })
                tickers.sort(key=lambda x: float(x['P']), reverse=True)
                event_bus.emit(Event.STREAM_TICKERS, tickers[:100])

            await asyncio.sleep(0.1)


def calc_output(data, output, symbol):
    last_01m = data[symbol][-1]
    last_03m = data[symbol][-3:]
    last_05m = data[symbol][-5:]
    last_10m = data[symbol][-10:]
    last_15m = data[symbol][-15:]
    last_03m_o, last_03m_c = last_03m[0][0], last_03m[-1][1]
    last_05m_o, last_05m_c = last_05m[0][0], last_05m[-1][1]
    last_10m_o, last_10m_c = last_10m[0][0], last_10m[-1][1]
    last_15m_o, last_15m_c = last_15m[0][0], last_15m[-1][1]
    last_03m_pt = ((Decimal(last_03m_c) - Decimal(last_03m_o)) / Decimal(last_03m_o)) * Decimal('100')
    last_05m_pt = ((Decimal(last_05m_c) - Decimal(last_05m_o)) / Decimal(last_05m_o)) * Decimal('100')
    last_10m_pt = ((Decimal(last_10m_c) - Decimal(last_10m_o)) / Decimal(last_10m_o)) * Decimal('100')
    last_15m_pt = ((Decimal(last_15m_c) - Decimal(last_15m_o)) / Decimal(last_15m_o)) * Decimal('100')

    output[symbol] = {
        '1m': round(last_01m[2], 2),
        '3m': round(last_03m_pt, 2),
        '5m': round(last_05m_pt, 2),
        '10m': round(last_10m_pt, 2),
        '15m': round(last_15m_pt, 2),
    }

    sorted_output = []
    for s, v in output.items():
        pts = 0
        pts += 1 if v['1m'] > 0 else 0
        pts += 2 if v['3m'] > 0 else 0
        pts += 3 if v['5m'] > 0 else 0
        pts += 4 if v['10m'] > 0 else 0
        sorted_output.append({
            's': s,
            '1m': v['1m'],
            '3m': v['3m'],
            '5m': v['5m'],
            '10m': v['10m'],
            '15m': v['15m'],
            'pts': pts,
        })
        sorted_output.sort(key=lambda x: x['5m'], reverse=True)

    return sorted_output
