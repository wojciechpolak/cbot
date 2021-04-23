"""
# job_crypto_pf.py
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
from cbot.server.task import Task
from cbot.server.tasks.data import TaskData


class Data(TaskData):
    exchange: str = None
    symbol: str = None

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


async def job_crypto_pf(task: Task):
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

    if not exch.instance.has['fetchMyTrades'] or not exch.instance.has['fetchBalance']:
        task.set_finished()
        return -1

    balance = await exch.instance.fetch_balance()
    for symbol in balance['total']:
        tot = balance['total'][symbol]
        if tot:
            printer(f'{symbol}: {tot}')

    # from_id = '0'
    # params = {'fromId': from_id}
    # previous_from_id = from_id
    # all_trades = []
    #
    # while True:
    #     print('------------------------------------------------------------------')
    #     print('Fetching with params', params)
    #     trades = await exch.instance.fetch_my_trades(data.symbol, None, None, params)
    #     print('Fetched', len(trades), 'trades')
    #     if len(trades):
    #         # for i in range(0, len(trades)):
    #         #     trade = trades[i]
    #         #     print (i, trade['id'], trade['datetime'], trade['amount'])
    #         last_trade = trades[len(trades) - 1]
    #         if last_trade['id'] == previous_from_id:
    #             break
    #         else:
    #             previous_from_id = last_trade['id']
    #             params['fromId'] = last_trade['id']
    #             all_trades = all_trades + trades
    #     else:
    #         break
    #
    # print('Fetched', len(all_trades), 'trades')
    # for i in range(0, len(all_trades)):
    #     trade = all_trades[i]
    #     print(i, trade['id'], trade['datetime'], trade['amount'])

    task.set_finished()
