"""
# job_crypto_ticker.py
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

from cbot.server import exchange
from cbot.server.exchange import ExchangeError
from cbot.server.logger import logger
from cbot.server.memstore import memstore
from cbot.server.task import Task
from cbot.server.tasks.data import TaskData


class Data(TaskData):
    exchange: str = None
    ohlcv: bool = False
    symbol: str = 'BTC/USDT'

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
            elif k == 'desc':
                pass
            else:
                logger.error('Invalid call argument: %s', k)


async def job_crypto_ticker(task: Task):
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

    if ',' in data.symbol:
        task.printer_warning('job_crypto_ticker: Using multiple tickers (weight=40)')
        symbols = data.symbol.split(',')
        tickers = await exch.instance.fetch_tickers(symbols)
        for key in tickers:
            memstore.add_ticker(data.exchange, tickers[key])
            logger.debug('job_crypto_ticker = %s', tickers[key])
    else:
        ticker = await exch.instance.fetch_ticker(data.symbol)
        memstore.add_ticker(data.exchange, ticker)
        logger.debug('job_crypto_ticker = %s', ticker)

    task.set_finished()
