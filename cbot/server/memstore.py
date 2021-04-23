"""
# memstore.py
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

from typing import Any

from cbot.server.event_bus import event_bus, Event


class MemStore:

    def __init__(self):
        self.store = {
            'symbols': {},
            'ohlcv': {},
            'tickers': {},
        }

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def get_keys(self):
        return list(self.store.keys())

    def add(self, key: str, val: Any):
        self.store[key] = val

    def add_ohlcv(self, exchange: str, symbol: str, ohlcv: Any):
        if exchange not in self.store['ohlcv']:
            self.store['ohlcv'][exchange] = {}
        self.store['ohlcv'][exchange][symbol] = ohlcv

    def add_ticker(self, exchange: str, ticker: Any):
        if exchange not in self.store['tickers']:
            self.store['tickers'][exchange] = {}
        key = ticker['symbol']
        self.store['tickers'][exchange][key] = ticker
        event_bus.emit(Event.TICKER_UPDATE, self.store['tickers'])

    def get(self, key: str, default: Any = None):
        if key not in self.store:
            return default
        return self.store[key]

    def get_ohlcv(self, exchange: str, key: str, default: Any = None):
        self.store['ohlcv'][exchange].get(key, default)

    def get_ticker(self, exchange: str, key: str, default: Any = None):
        self.store['tickers'][exchange].get(key, default)

    def to_savegame(self):
        return self.store

    def from_savegame(self, store):
        self.store = store


memstore = MemStore()
