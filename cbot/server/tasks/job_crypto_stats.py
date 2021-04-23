"""
# job_crypto_stats.py
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

import json

import pandas
from stockstats import StockDataFrame

from cbot.server import exchange
from cbot.server.event_bus import Event, event_bus
from cbot.server.exchange import ExchangeError
from cbot.server.logger import logger
from cbot.server.memstore import memstore
from cbot.server.task import Task
from cbot.server.tasks.data import TaskData


class Data(TaskData):
    exchange: str = None
    symbol: str = 'BTC/USDT'
    timeframe: str = '1h'
    limit: int = None

    def map_options(self, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        for _arg in args:
            pass

        for k, v in kwargs.items():
            if k == 'exchange':
                self.exchange = v
            elif k == 'symbol':
                self.symbol = v
            elif k == 'timeframe':
                self.timeframe = v or '1h'
            elif k == 'limit':
                self.limit = int(v)
            elif k == 'desc':
                pass
            else:
                logger.error('Invalid call argument: %s', k)


async def job_crypto_stats(task: Task):
    printer = task.printer
    printer(f'Launching task #{task.id} {task.name}')

    if task.data is None:
        task.data = Data()
        task.data.map_options(task.op.args, task.op.kwargs)
    data = task.data

    try:
        exch = await exchange.get_or_create(data.exchange)
        data.exchange = exch.exchange_id
    except ExchangeError as exc:
        task.printer_error('ExchangeError:', exc)
        task.set_finished()
        return -1

    printer('Exchange =', data.exchange)
    printer('Symbol =', data.symbol)
    printer('Timeframe =', data.timeframe)

    if not exch.instance.has['fetchOHLCV']:
        task.printer_error(f'{data.exchange} does not support fetchOHLCV')
        task.set_finished()
        return

    ohlcv_data = await exch.instance.fetch_ohlcv(data.symbol, data.timeframe, limit=data.limit)
    memstore.add_ohlcv(data.exchange, data.symbol, ohlcv_data)
    logger.debug('fetch_ohlcv: %s', ohlcv_data)

    # update timestamp to human readable timestamp
    ohlcv_data = [[exch.instance.iso8601(candle[0])] + candle[1:] for candle in ohlcv_data]
    header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    df = pandas.DataFrame(ohlcv_data, columns=header)
    stock_data = StockDataFrame.retype(df)

    printer(f'\n{stock_data}')

    last_rsi = stock_data['rsi_14'].iloc[-1]
    printer(f'RSI = {last_rsi}')

    signal = stock_data['macds']  # Your signal line
    macd = stock_data['macd']  # The MACD that need to cross the signal line
    advice = ['No data']  # Since you need at least two hours in the for loop

    for i in range(1, len(signal)):
        # If the MACD crosses the signal line upward
        if macd[i] > signal[i] and macd[i - 1] <= signal[i - 1]:
            advice.append('BUY')
        elif macd[i] < signal[i] and macd[i - 1] >= signal[i - 1]:
            advice.append('SELL')
        else:
            advice.append('HOLD')

    stock_data['advice'] = advice
    printer(f'{stock_data["advice"]}')

    event_bus.emit(Event.CRYPTO_STATS, {
        'data': data.__dict__,
        'stock_data': json.loads(stock_data.to_json()),  # to_dict doesn't work
    })
    task.set_finished()
