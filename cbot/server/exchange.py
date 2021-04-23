"""
# exchange.py
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

from typing import Dict
from ccxt import async_support as ccxt, ExchangeNotAvailable

from cbot.server import config
from cbot.server.memstore import memstore


class ExchangeError(Exception):
    def __init__(self, *_args):  # pylint: disable=super-init-not-called
        super()


class Exchange:
    def __init__(self, exchange_id: str, api_key: str, api_secret: str, api_pass: str = None):
        self.exchange_id = exchange_id
        exchange_class = getattr(ccxt, exchange_id)
        opts = {
            'enableRateLimit': True,
            'timeout': 30000,
            'apiKey': api_key,
        }
        if api_secret:
            opts['secret'] = api_secret
        if api_pass:
            opts['password'] = api_pass
        self.instance: ccxt.Exchange = exchange_class(opts)

    async def close(self):
        if self.instance:
            await self.instance.close()

    async def load_markets(self):
        try:
            markets = await self.instance.load_markets()
            symbols = memstore.get('symbols')
            all_symbols_map = {}

            if not symbols:
                symbols = {}
                memstore.add('symbols', symbols)

            for s in self.instance.symbols:
                if self.instance.markets[s]['active'] is False:
                    continue

                base, quote = s.split('/')
                if base not in symbols:
                    symbols[base] = {self.exchange_id}
                else:
                    symbols[base].add(self.exchange_id)
                if quote not in symbols:
                    symbols[quote] = {self.exchange_id}
                else:
                    symbols[quote].add(self.exchange_id)

                if base not in all_symbols_map:
                    all_symbols_map[base] = {quote}
                else:
                    all_symbols_map[base].add(quote)
                memstore.add(f'{self.exchange_id}:symbols',
                             all_symbols_map)
            return markets
        except ExchangeNotAvailable as exc:
            raise ExchangeError(exc) from exc

    def cost2prec(self, symbol, cost):
        return self.instance.decimal_to_precision(
            cost,
            ccxt.TRUNCATE,
            self.instance.markets[symbol]['precision']['price'],
            self.instance.precisionMode,
            ccxt.PAD_WITH_ZERO)

    def price2prec(self, symbol, price):
        return self.instance.decimal_to_precision(
            price,
            ccxt.ROUND,
            self.instance.markets[symbol]['precision']['price'],
            self.instance.precisionMode,
            ccxt.PAD_WITH_ZERO)

    def amount2prec(self, symbol, amount):
        return self.instance.decimal_to_precision(
            amount,
            ccxt.TRUNCATE,
            self.instance.markets[symbol]['precision']['amount'],
            self.instance.precisionMode,
            self.instance.paddingMode)

    def fee2prec(self, symbol, fee):
        return self.instance.decimal_to_precision(
            fee,
            ccxt.ROUND,
            self.instance.markets[symbol]['precision']['price'],
            self.instance.precisionMode,
            self.instance.paddingMode)

    def currency2prec(self, currency, fee):
        return self.instance.decimal_to_precision(
            fee,
            ccxt.ROUND,
            self.instance.currencies[currency]['precision'],
            self.instance.precisionMode,
            self.instance.paddingMode)


exchanges: Dict[str, Exchange] = {}


async def get_or_create(exchange_id: str) -> Exchange:
    if not exchange_id:
        exchange_id = config.conf.sections['server'].get('default_exchange')

    if not exchange_id:
        raise ExchangeError('No exchange selected')

    assert config.conf.sections[exchange_id] is not None,\
        'Missing %s config!' % exchange_id

    exch: Exchange = exchanges.get(exchange_id)
    if exch is None:
        exch_info = config.conf.sections[exchange_id]
        exch = Exchange(exchange_id,
                        exch_info.get('key'),
                        exch_info.get('secret'),
                        exch_info.get('password'))
        exchanges[exchange_id] = exch

    await exch.load_markets()
    return exch


async def close_all():
    for key, _v in list(exchanges.items()):
        exch = exchanges[key]
        await exch.instance.close()
        del exchanges[key]
