"""
# job_crypto_tsl.py (Trailing Stop Loss)
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
import pprint
from decimal import Decimal
from typing import cast, Dict

from cbot.server import exchange
from cbot.server.event_bus import event_bus, Event
from cbot.server.exchange import Exchange, ExchangeError
from cbot.server.logger import logger
from cbot.server.mail import send_mail
from cbot.server.memstore import memstore
from cbot.server.periodic import Periodic, PeriodicRunStatus
from cbot.server.task import Task
from cbot.server.tasks.data import TaskData
from cbot.server.utils import parse_bool


class Data(TaskData):
    aboveInitialPrice: bool = False
    aboveInitialPriceOffset: Decimal = Decimal('0')
    aboveInitialPriceOffsetPct: Decimal = Decimal('0')
    algo: str = 'std1'
    available_quantity = Decimal('0')
    buy: bool = False
    buy_completed: bool = False
    buy_symbol: str = None
    currentPrice = Decimal('0')
    exchange: str = None
    initialPrice: Decimal = Decimal('0')
    initialValue: Decimal
    interval: int = 60
    iteration = 0
    lastHigh: Decimal = None
    lastHighByUser: Decimal = None
    limitOffsetPrice: Decimal = Decimal('0')
    limitPrice: Decimal = Decimal('0')
    mode = '-'
    offsetPctRaisedBy: Decimal = Decimal('0')
    quantity: Decimal = Decimal('0')
    quoteOrderQty: Decimal = None
    reboundRate: Decimal
    reduceStopOffsetPriceBy: Decimal = Decimal('0.5')
    reduceStopOffsetPriceByMax: Decimal = Decimal('80.0')
    sell_symbol: str = None
    simulate: bool = False
    simulate_done_iter: int = 0
    simulate_endless: bool = False
    stopLoss: bool = False
    stopOffsetPrice: Decimal = Decimal('0')
    stopOffsetPricePct: Decimal = Decimal('0')
    stopPrice: Decimal = None
    stopPriceChange: Decimal
    stopPriceChangePct: Decimal
    stopPriceChangePctStr: str
    symbol: str
    takeProfit: Decimal = Decimal('0')
    takeProfitPct: Decimal = Decimal('0')
    totalPriceDiff: Decimal
    totalPriceDiffPct: Decimal
    totalPriceDiffPctStr: str
    totalPriceDiffStr: str

    def map_options(self, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        for arg in args:
            if arg in ('simulate', 'dry'):
                self.simulate = True
            elif arg == 'endless':
                self.simulate_endless = True
            elif arg == 'aboveInitialPrice':
                self.aboveInitialPrice = True
            elif arg == 'buy':
                self.buy = True
            elif arg == 'stopLoss':
                self.stopLoss = True

        for k, v in kwargs.items():
            if k in ('simulate', 'dry'):
                self.simulate = parse_bool(v)
            elif k == 'endless':
                self.simulate_endless = parse_bool(v)
            elif k == 'buy':
                self.buy = parse_bool(v)
            elif k == 'stopLoss':
                self.stopLoss = parse_bool(v)
            elif k == 'aboveInitialPrice':
                self.aboveInitialPrice = parse_bool(v)
            elif k == 'aboveInitialPriceOffset':
                self.aboveInitialPrice = True
                self.aboveInitialPriceOffset = Decimal(str(v))
            elif k == 'aboveInitialPriceOffsetPct':
                self.aboveInitialPrice = True
                self.aboveInitialPriceOffsetPct = Decimal(str(v))
            elif k == 'algo':
                self.algo = v
            elif k == 'exchange':
                self.exchange = v
            elif k == 'interval':
                self.interval = int(v)
            elif k == 'symbol':
                self.symbol = v
            elif k == 'quantity':
                self.quantity = Decimal(str(v))
            elif k == 'initialPrice':
                self.initialPrice = Decimal(str(v))
            elif k == 'lastHigh':
                self.lastHighByUser = Decimal(str(v))
            elif k == 'stopOffsetPrice':
                self.stopOffsetPrice = Decimal(str(v))
            elif k == 'stopOffsetPricePct':
                self.stopOffsetPricePct = Decimal(str(v))
            elif k == 'takeProfit':
                self.takeProfit = Decimal(str(v))
            elif k == 'takeProfitPct':
                self.takeProfitPct = Decimal(str(v))
            elif k == 'quoteOrderQty':
                self.quoteOrderQty = Decimal(str(v))
            elif k == 'desc':
                pass
            else:
                logger.error('Invalid call argument: %s', k)


async def job_crypto_tsl(task: Task):
    printer = task.printer
    printer(f'Launching task #{task.id} {task.name}')

    if task.data is None:
        task.data = Data()
        task.data.map_options(task.op.args, task.op.kwargs)
    data = task.data

    if not data.stopOffsetPrice and not data.stopOffsetPricePct:
        task.printer_error('stopOffsetPrice(Pct) must be > 0')
        task.set_finished()
        return -1

    try:
        exch = await exchange.get_or_create(data.exchange)
        data.exchange = exch.exchange_id
    except ExchangeError as exc:
        task.printer_error('ExchangeError:', exc)
        task.set_finished()
        return -1

    printer('Algorithm =', data.algo)
    printer('Exchange =', data.exchange)
    printer('Interval =', data.interval)

    if data.quoteOrderQty and not data.buy:
        task.printer_error('quoteOrderQty provided without buy!')
        task.set_finished()
        return

    if data.buy and not data.buy_completed:
        try:
            amount = data.quantity
            price = None
            params = {}
            if data.simulate:
                params['test'] = data.simulate
            if data.quoteOrderQty:
                amount = None
                price = None
                params['quoteOrderQty'] = float(data.quoteOrderQty)

            res_order_buy = await exch.instance.create_order(
                data.symbol, 'market', 'buy', amount, price, params)

            data.buy_completed = True
            data.initialPrice = Decimal(str(res_order_buy.get('price') or 1))
            data.quantity = Decimal(str(res_order_buy.get('amount') or 0))

            et = printer(f'BUY status: {pprint.pformat(res_order_buy, indent=2, width=1)}') + '\n'
            send_mail(body=et)
        except Exception as exc:
            logger.exception('Exception')
            task.printer_error('BUY error:', exc)
            task.printer_error('Limits:', exch.instance.markets[data.symbol]['limits'])
            task.set_finished()
            return 1

    if not data.initialPrice:
        try:
            ticker = await exch.instance.fetch_ticker(data.symbol)
            data.initialPrice = Decimal(str(ticker.get('last')))
        except Exception as exc:
            logger.exception('fetch_ticker')
            task.printer_error('Problem with getting ticker:', exc)

    data.sell_symbol, data.buy_symbol = data.symbol.split('/')
    available_quantity = await exch.instance.fetch_balance()
    data.available_quantity = Decimal(str(available_quantity[data.sell_symbol]['free']))

    if data.quantity:
        if not data.simulate and data.quantity > data.available_quantity:
            printer('Insufficient quantity for trading')
            printer(f'Available: {data.available_quantity}')
            printer(f'Specified: {data.quantity}')
            task.set_finished()
            return -1
    else:
        data.quantity = data.available_quantity

    if data.quantity != data.available_quantity:
        printer(f'Quantity = {data.quantity}/{data.available_quantity}')
    else:
        printer(f'Quantity = {data.quantity}')
    printer('initialPrice =', data.initialPrice)

    calc_above_offset_price(data)
    calc_stop_offset_price(data)

    if data.aboveInitialPrice:
        if data.aboveInitialPriceOffsetPct:
            printer(f'aboveInitialPrice = {data.initialPrice + data.aboveInitialPriceOffset} '
                    f'({data.aboveInitialPriceOffsetPct}%)')
        else:
            printer(f'aboveInitialPrice = {data.initialPrice + data.aboveInitialPriceOffset}')

    if data.stopOffsetPricePct and data.initialPrice:
        printer(f'stopOffsetPrice = {data.stopOffsetPrice} ({data.stopOffsetPricePct}%)')
    elif data.stopOffsetPricePct:
        printer(f'stopOffsetPricePct = {data.stopOffsetPricePct}%')
    else:
        printer('stopOffsetPrice =', data.stopOffsetPrice)

    if data.takeProfitPct:
        printer(f'takeProfit = {data.takeProfitPct}%')
    elif data.takeProfit:
        printer(f'takeProfit = {data.takeProfit}')

    async def on_task_modified(event: Dict):
        if event['taskId'] == task.id:
            printer(f'crypto_tsl: Updating task #{task.id} data after task modification')
            calc_above_offset_price(data)
            calc_stop_offset_price(data, data.currentPrice)
            data.stopPrice = data.lastHigh - data.stopOffsetPrice
            data.limitPrice = data.stopPrice - data.limitOffsetPrice

    event_bus.add_listener(Event.TASK_MODIFIED, on_task_modified)

    t1 = Periodic(job_crypto_tsl_run, task=task)
    await t1.start(task, exch)
    try:
        while t1.is_running:
            await asyncio.sleep(1)
        logger.info('Finishing task')
        task.set_finished()
    finally:
        event_bus.remove_listener(Event.TASK_MODIFIED, on_task_modified)
        await t1.stop()


async def job_crypto_tsl_run(task: Task, exch: Exchange):
    printer = task.printer
    data = cast(Data, task.data)

    try:
        ticker = await exch.instance.fetch_ticker(data.symbol)
    except Exception as exc:
        logger.exception('fetch_ticker')
        task.printer_error('Problem with getting ticker:', exc)
        return PeriodicRunStatus.ERROR_SOFT

    logger.debug('Ticker = %s', ticker)
    memstore.add_ticker(data.exchange, ticker)

    data.iteration += 1

    if data.algo == 'std2':
        is_done = calc_long_tsl_2(data, ticker)
    else:
        is_done = calc_long_tsl_1(data, ticker)

    out = f'#{str(data.iteration):3s}'

    if data.simulate:
        out += '; S' + data.mode
    else:
        out += '; P' + data.mode

    if data.totalPriceDiff >= 0:
        data.totalPriceDiffStr = f'+{exch.price2prec(data.symbol, data.totalPriceDiff)}'
    else:
        data.totalPriceDiffStr = f'{exch.price2prec(data.symbol, data.totalPriceDiff)}'

    if data.totalPriceDiffPct >= 0:
        data.totalPriceDiffPctStr = f'+{data.totalPriceDiffPct:.2f}%'
    else:
        data.totalPriceDiffPctStr = f'{data.totalPriceDiffPct:.2f}%'

    if data.stopPriceChangePct >= 0:
        data.stopPriceChangePctStr = f'+{data.stopPriceChangePct:.2f}%'
    else:
        data.stopPriceChangePctStr = f'{data.stopPriceChangePct:.2f}%'

    out += f';{data.symbol}'

    if data.quantity == data.available_quantity:
        out += ';QTY ' + exch.amount2prec(data.symbol, data.quantity)
    else:
        out += ';QTY ' + \
               exch.amount2prec(data.symbol, data.quantity) + \
               '/' + \
               exch.amount2prec(data.symbol, data.available_quantity)

    out += f';H {exch.price2prec(data.symbol, data.lastHigh)}'
    out += f';CUR {exch.price2prec(data.symbol, data.currentPrice)}' + \
           f' ({exch.cost2prec(data.symbol, data.currentPrice * data.quantity)} {data.buy_symbol})' + \
           f' (PD:{data.totalPriceDiffStr}/{data.totalPriceDiffPctStr})'
    out += f';STOP {exch.price2prec(data.symbol, data.stopPrice)}' + \
           f' (GAP:{exch.price2prec(data.symbol, data.stopPriceChange)}/{data.stopPriceChangePctStr})'
    if data.algo == 'std2':
        out += f';GR%:{data.offsetPctRaisedBy:.2f}/{data.reduceStopOffsetPriceByMax}'
    out += f';LIMIT {exch.price2prec(data.symbol, data.limitPrice)}'

    printer(out)

    if data.simulate_endless and data.simulate_done_iter > 0:
        is_done = False

    if is_done:
        fee = exch.instance.calculate_fee(
            data.symbol, None, 'sell', float(data.quantity), float(data.limitPrice), 'maker')
        end_value = data.currentPrice * data.quantity

        res_order_sell = None
        if data.quantity:
            try:
                params = {
                    'test': bool(data.simulate)
                }
                if data.stopLoss:  # Stop Loss Sell
                    res_order_sell = await exch.instance.create_order(
                        data.symbol, 'market', 'sell', data.quantity, None, params)
                else:  # Stop Limit Sell
                    res_order_sell = await exch.instance.create_order(
                        data.symbol, 'limit', 'sell', data.quantity, data.limitPrice, params)
            except Exception as exc:
                logger.exception('Exception')
                task.printer_error('SELL error:', exc)
                task.printer_error('Limits:', exch.instance.markets[data.symbol]['limits'])

        et = f'Task ID: {task.id}\n'
        if task.op.kwargs.get('desc'):
            et += 'Description: ' + task.op.kwargs.get('desc') + '\n'

        et += printer(f'Stop price triggered: CUR {exch.price2prec(data.symbol, data.currentPrice)}' +
                      f' <= STOP {exch.price2prec(data.symbol, data.stopPrice)}') + '\n'
        if data.stopLoss:
            et += printer('Executing sell market order') + '\n'
        else:
            et += printer(f'Executing sell limit order @ {exch.price2prec(data.symbol, data.limitPrice)}') + '\n'
        et += printer(f'Quantity: {exch.amount2prec(data.symbol, data.quantity)} {data.sell_symbol}') + '\n'
        et += printer(f'Start price: {exch.price2prec(data.symbol, data.initialPrice)} {data.buy_symbol}') + '\n'
        et += printer(f'Start value: {exch.cost2prec(data.symbol, data.initialValue)} {data.buy_symbol}') + '\n'
        et += printer(f'End value: {exch.cost2prec(data.symbol, end_value)} {data.buy_symbol}') + '\n'
        et += printer(f'Profit: {exch.cost2prec(data.symbol, end_value - data.initialValue)} ' +
                      f'{data.buy_symbol}') + '\n'
        et += printer(f'Fee: {exch.fee2prec(data.symbol, fee["cost"])} {fee["currency"]}') + '\n'
        et += '\n' + printer(f'Sell status: {pprint.pformat(res_order_sell, indent=2, width=1)}') + '\n'

        send_mail(body=et)
        if not data.simulate_endless:
            return PeriodicRunStatus.DONE
        data.simulate_done_iter += 1

    event_bus.emit(Event.CRYPTO_TSL_UPDATE, {
        'taskId': task.id,
        'data': data.__dict__,
    })
    return PeriodicRunStatus.CONTINUE


def calc_above_offset_price(data: Data):
    if data.aboveInitialPriceOffsetPct:
        data.aboveInitialPriceOffset = data.aboveInitialPriceOffsetPct / Decimal('100') * data.initialPrice


def calc_stop_offset_price(data: Data, price: Decimal = None):
    if price is None:
        price = data.initialPrice
    if data.stopOffsetPricePct and price:
        data.stopOffsetPrice = data.stopOffsetPricePct / Decimal('100') * price


def calc_long_tsl_1(data: Data, ticker) -> bool:
    try:
        data.currentPrice = Decimal(str(ticker.get('last')))
    except Exception:
        logger.exception('Exception: %s', ticker)

    if data.lastHigh is None:
        data.mode = 'S'
        calc_stop_offset_price(data, data.currentPrice)

        if data.initialPrice:
            data.initialValue = data.quantity * data.initialPrice
        else:
            data.initialPrice = data.currentPrice
            data.initialValue = data.quantity * data.initialPrice

        data.lastHigh = data.lastHighByUser or data.currentPrice
        data.stopPrice = data.lastHigh - data.stopOffsetPrice
        data.limitPrice = data.stopPrice - data.limitOffsetPrice

    elif data.currentPrice > data.lastHigh:
        data.mode = '+'
        calc_stop_offset_price(data, data.currentPrice)
        data.lastHigh = data.currentPrice
        data.stopPrice = data.lastHigh - data.stopOffsetPrice
        data.limitPrice = data.stopPrice - data.limitOffsetPrice

    else:
        data.mode = ' '

    data.totalPriceDiff = data.currentPrice - data.initialPrice
    data.totalPriceDiffPct = (data.currentPrice - data.initialPrice) / data.initialPrice * Decimal('100')
    data.stopPriceChange = data.currentPrice - data.stopPrice
    data.stopPriceChangePct = data.currentPrice / data.lastHigh * Decimal('100') - Decimal('100')
    data.reboundRate = (data.lastHigh - data.currentPrice) / data.lastHigh

    if data.aboveInitialPrice:
        above_price = data.initialPrice + data.aboveInitialPriceOffset
        if data.currentPrice <= above_price:
            return False

    if data.takeProfitPct and data.mode == ' ' and data.totalPriceDiffPct >= data.takeProfitPct:
        return True
    if data.takeProfit and data.mode == ' ' and data.totalPriceDiff >= data.takeProfit:
        return True

    return data.currentPrice <= data.stopPrice and \
           data.limitPrice < data.lastHigh


def calc_long_tsl_2(data: Data, ticker) -> bool:
    try:
        data.currentPrice = Decimal(str(ticker.get('last')))
    except Exception:
        logger.exception('Exception: %s', ticker)

    if data.lastHigh is None:
        data.mode = 'S'

        if data.initialPrice:
            data.initialValue = data.quantity * data.initialPrice
        else:
            data.initialPrice = data.currentPrice
            data.initialValue = data.quantity * data.initialPrice

        data.lastHigh = data.currentPrice
        data.stopPrice = data.lastHigh - data.stopOffsetPrice
        data.limitPrice = data.stopPrice - data.limitOffsetPrice

    elif data.currentPrice > data.lastHigh:
        data.mode = '+'

        if data.reduceStopOffsetPriceBy and \
                (data.offsetPctRaisedBy + data.reduceStopOffsetPriceBy) <= data.reduceStopOffsetPriceByMax:
            data.offsetPctRaisedBy += data.reduceStopOffsetPriceBy

        data.lastHigh = data.currentPrice
        magic_raise = data.stopOffsetPrice * data.offsetPctRaisedBy / Decimal('100')
        data.stopPrice = data.lastHigh - data.stopOffsetPrice + magic_raise
        data.limitPrice = data.stopPrice - data.limitOffsetPrice

    else:
        data.mode = ' '

    data.totalPriceDiff = data.currentPrice - data.initialPrice
    data.totalPriceDiffPct = (data.currentPrice - data.initialPrice) / data.initialPrice * Decimal('100')
    data.stopPriceChange = data.currentPrice - data.stopPrice
    data.stopPriceChangePct = data.currentPrice / data.lastHigh * Decimal('100') - Decimal('100')
    data.reboundRate = (data.lastHigh - data.currentPrice) / data.lastHigh

    if data.aboveInitialPrice:
        above_price = data.initialPrice + data.aboveInitialPriceOffset
        if data.currentPrice <= above_price:
            return False

    if data.takeProfitPct and data.mode == ' ' and data.totalPriceDiffPct >= data.takeProfitPct:
        return True
    if data.takeProfit and data.mode == ' ' and data.totalPriceDiff >= data.takeProfit:
        return True

    return data.currentPrice <= data.stopPrice
