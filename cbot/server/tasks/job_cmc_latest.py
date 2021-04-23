"""
# job_cmc_latest.py
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

from requests import Session
from requests.exceptions import ConnectionError as RConError, Timeout, TooManyRedirects

from cbot.server import config
from cbot.server.event_bus import event_bus, Event
from cbot.server.logger import logger
from cbot.server.memstore import memstore
from cbot.server.task import Task
from cbot.server.tasks.data import TaskData

API_ENDPOINT = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'


class Data(TaskData):
    exchange: str = 'coinmarketcap'
    num: int = 50
    quote: str = 'BTC'
    sortby: str = 'percent_change_1h'

    def map_options(self, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        for _arg in args:
            pass

        for k, v in kwargs.items():
            if k == 'num':
                self.num = int(v)
            elif k == 'quote':
                self.quote = v
            elif k == 'sortby':
                self.sortby = v
            elif k == 'desc':
                pass
            else:
                logger.error('Invalid call argument: %s', k)


async def job_cmc_latest(task: Task):
    printer = task.printer
    printer(f'Launching task #{task.id} {task.name}')

    if task.data is None:
        task.data = Data()
        task.data.map_options(task.op.args, task.op.kwargs)
    data = task.data

    assert config.conf.sections[data.exchange] is not None,\
        'Missing %s config!' % data.exchange

    exch_info = config.conf.sections[data.exchange]

    printer('Exchange =', data.exchange)
    printer('Quote =', data.quote)
    printer('Sort by =', data.sortby)

    parameters = {
        'start': '1',
        'limit': '200',
        'convert': 'USD',
        'sort': 'market_cap',
        'sort_dir': 'desc',
        'aux': 'platform',
        'cryptocurrency_type': 'coins',
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': exch_info.get('key'),
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(API_ENDPOINT, params=parameters)
        resp = response.json()
        logger.debug('job_cmc_latest: %s', resp)

        items = resp['data']
        if data.sortby:
            items.sort(key=lambda x: x['quote']['USD'][data.sortby], reverse=True)

        symbols = memstore.get('symbols')
        if len(symbols) > 0:
            filtered_items = filter(lambda x: len(symbols.get(x['symbol'], [])) > 0, items)
            items = list(filtered_items)
        else:
            task.printer_warning('job_cmc_latest: memstore symbols are empty')

        out = ['TOP 1h%']

        internal = []
        for idx, item in enumerate(items[:data.num], start=1):
            markets_arr = []
            markets = symbols.get(item['symbol'], set())

            for market in markets:
                ess = memstore.get(f'{market}:symbols')
                quotes = ess.get(item['symbol'], set())
                markets_arr.append(f'{market}: {",".join(quotes)}')
                if market == 'binance':
                    qt = data.quote
                    if qt not in quotes:
                        if 'BTC' in quotes:
                            qt = 'BTC'
                        elif 'USDT' in quotes:
                            qt = 'USDT'
                        elif 'BUSD' in quotes:
                            qt = 'BUSD'
                    internal.append(f"{item['symbol']}/{qt}")

            out.append(f'{idx:2d}) {item["symbol"]:5s} ({item["name"]}) '
                       f'{item["quote"]["USD"]["percent_change_1h"]:.2f}%, '
                       f'{item["quote"]["USD"]["percent_change_24h"]:.2f}%  '
                       f'{", ".join(markets_arr)}')

        if len(internal) > 0:
            out.append('\n' + ','.join(internal))

        printer('job_cmc_latest:', '\n'.join(out))

        memstore.add('cmc_latest_symbols', internal)
        event_bus.emit(Event.CMC_LATEST_UPDATE, internal)

    except (RConError, Timeout, TooManyRedirects) as exc:
        logger.error('job_cmc_latest: %s', exc)
    finally:
        task.set_finished()
