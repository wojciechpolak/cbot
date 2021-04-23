"""
# job_crypto_order.py
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

import pprint
from decimal import Decimal
from typing import Any

from cbot.server import exchange
from cbot.server.event_bus import event_bus, Event
from cbot.server.exchange import ExchangeError
from cbot.server.logger import logger
from cbot.server.mail import send_mail
from cbot.server.task import Task
from cbot.server.tasks.data import TaskData
from cbot.server.utils import parse_bool

ORDER_SIDE_BUY = 'BUY'
ORDER_SIDE_SELL = 'SELL'

ORDER_TYPE_LIMIT = 'LIMIT'
ORDER_TYPE_MARKET = 'MARKET'
ORDER_TYPE_STOP_LOSS = 'STOP_LOSS'
ORDER_TYPE_STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
ORDER_TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
ORDER_TYPE_TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'

TIME_IN_FORCE_GTC = 'GTC'  # Good Til Canceled
TIME_IN_FORCE_IOC = 'IOC'  # Immediate Or Cancel
TIME_IN_FORCE_FOK = 'FOK'  # Fill Or Kill

# Type              Additional mandatory parameters
# LIMIT             timeInForce, quantity, price
# MARKET            quantity or quoteOrderQty
# STOP_LOSS         quantity, stopPrice
# STOP_LOSS_LIMIT   timeInForce, quantity, price, stopPrice
# TAKE_PROFIT       quantity, stopPrice
# TAKE_PROFIT_LIMIT timeInForce, quantity, price, stopPrice
# LIMIT_MAKER       quantity, price


class Data(TaskData):
    exchange: str = None
    order_completed: bool = False
    order_side: str = ''
    order_status: Any = None
    order_type: str = ORDER_TYPE_MARKET
    price: Decimal = Decimal('0')
    quantity: Decimal = Decimal('0')
    quoteOrderQty: Decimal = None
    simulate: bool = False
    stopPrice: Decimal = Decimal('0')
    symbol: str
    timeInForce: str = TIME_IN_FORCE_GTC

    def map_options(self, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        for arg in args:
            if arg in ('simulate', 'dry'):
                self.simulate = True
            elif arg == 'buy':
                self.order_side = ORDER_SIDE_BUY
            elif arg == 'sell':
                self.order_side = ORDER_SIDE_SELL
            elif arg == 'orderTypeLimit':
                self.order_type = ORDER_TYPE_LIMIT
            elif arg == 'orderTypeMarket':
                self.order_type = ORDER_TYPE_MARKET
            elif arg == 'orderTypeStopLoss':
                self.order_type = ORDER_TYPE_STOP_LOSS
            elif arg == 'orderTypeStopLossLimit':
                self.order_type = ORDER_TYPE_STOP_LOSS_LIMIT
            elif arg == 'orderTypeTakeProfit':
                self.order_type = ORDER_TYPE_TAKE_PROFIT
            elif arg == 'orderTypeTakeProfitLimit':
                self.order_type = ORDER_TYPE_TAKE_PROFIT_LIMIT
            else:
                logger.error('Invalid call argument: %s', arg)

        for k, v in kwargs.items():
            if k in ('simulate', 'dry'):
                self.simulate = parse_bool(v)
            elif k == 'exchange':
                self.exchange = v
            elif k == 'symbol':
                self.symbol = v
            elif k == 'quantity':
                self.quantity = Decimal(v)
            elif k == 'price':
                self.price = Decimal(v)
            elif k == 'quoteOrderQty':
                self.quoteOrderQty = Decimal(v)
            elif k == 'stopPrice':
                self.stopPrice = Decimal(v)
            elif k == 'desc':
                pass
            else:
                logger.error('Invalid call argument: %s', k)


async def job_crypto_order(task: Task):
    printer = task.printer
    printer_error = task.printer_error
    printer(f'Launching task #{task.id} {task.name}')

    if task.data is None:
        task.data = Data()
        task.data.map_options(task.op.args, task.op.kwargs)
    data = task.data

    if not data.order_side:
        printer_error('Order side BUY or SELL is required!')
        task.set_finished()
        return -1

    if data.order_type in (ORDER_TYPE_STOP_LOSS,
                           ORDER_TYPE_STOP_LOSS_LIMIT,
                           ORDER_TYPE_TAKE_PROFIT,
                           ORDER_TYPE_TAKE_PROFIT_LIMIT) and not data.stopPrice:
        printer_error('stopPrice is required for this order type')
        task.set_finished()
        return -1

    if data.order_type in (ORDER_TYPE_LIMIT,
                           ORDER_TYPE_STOP_LOSS_LIMIT,
                           ORDER_TYPE_TAKE_PROFIT_LIMIT) and not data.price:
        printer_error('price is required for this order type')
        task.set_finished()
        return -1

    try:
        exch = await exchange.get_or_create(data.exchange)
        data.exchange = exch.exchange_id
    except ExchangeError as exc:
        task.printer_error('ExchangeError:', exc)
        task.set_finished()
        return -1

    if data.simulate:
        printer('Simulate = Yes')

    printer('Exchange =', data.exchange)
    printer('Symbol =', data.symbol)
    printer('Order side =', data.order_side)
    printer('Order type =', data.order_type)

    if data.price:
        printer('Price =', data.price)
    if data.stopPrice:
        printer('StopPrice =', data.stopPrice)
    if data.quoteOrderQty:
        printer('QuoteOrderQty =', data.quoteOrderQty)

    if not data.order_completed:
        try:
            amount = data.quantity
            price = None
            params = {}
            if data.simulate:
                params['test'] = data.simulate
            if data.order_type not in (ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET):
                params['type'] = data.order_type
            if data.order_type in (ORDER_TYPE_LIMIT,
                                   ORDER_TYPE_STOP_LOSS_LIMIT,
                                   ORDER_TYPE_TAKE_PROFIT_LIMIT):
                price = data.price
            if data.stopPrice:
                params['stopPrice'] = float(data.stopPrice)
            if data.quoteOrderQty:
                amount = None
                price = None
                params['quoteOrderQty'] = float(data.quoteOrderQty)

            res_order_status = await exch.instance.create_order(
                data.symbol, data.order_type, data.order_side, amount, price, params)

            data.order_completed = True
            data.order_status = res_order_status
            data.price = Decimal(str(res_order_status.get('price') or 1))
            data.quantity = Decimal(str(res_order_status.get('amount') or 0))

            et = printer(f'Order status: {pprint.pformat(res_order_status, indent=2, width=1)}') + '\n'
            send_mail(body=et)
        except Exception as exc:
            task.printer_error('Order error:', exc)
            task.printer_error('Limits:', exch.instance.markets[data.symbol]['limits'])
            task.set_finished()
            return 1

    printer('Quantity =', data.quantity)
    printer('Price =', data.price)

    event_bus.emit(Event.CRYPTO_ORDER, data.__dict__)
    task.set_finished()
