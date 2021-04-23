"""
# event_bus.py
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
from enum import Enum
from typing import Callable


class Event(Enum):
    ALL = 'ALL'
    BIN_LIVE_UPDATE = 'BIN_LIVE_UPDATE'
    CMC_LATEST_UPDATE = 'CMC_LATEST_UPDATE'
    CRYPTO_ORDER = 'CRYPTO_ORDER'
    CRYPTO_STATS = 'CRYPTO_STATS'
    CRYPTO_TSL_UPDATE = 'CRYPTO_TSL_UPDATE'
    LOGGER = 'LOGGER'
    SAVEGAME = 'SAVEGAME'
    STREAM_TICKERS = 'STREAM_TICKERS'
    TASK_FINISHED = 'TASK_FINISHED'
    TASK_INFO = 'TASK_INFO'
    TASK_MANAGER = 'TASK_MANAGER'
    TASK_MODIFIED = 'TASK_MODIFIED'
    TICKER_UPDATE = 'TICKER_UPDATE'


class EventBus:
    def __init__(self):
        self.listeners = {}

    def add_listener(self, event_name: Event, listener: Callable):
        if not self.listeners.get(event_name, None):
            self.listeners[event_name] = {listener}
        else:
            self.listeners[event_name].add(listener)

    def remove_listener(self, event_name: Event, listener: Callable):
        self.listeners[event_name].remove(listener)
        if len(self.listeners[event_name]) == 0:
            del self.listeners[event_name]

    def emit(self, event_name: Event, *args, **kwargs):
        named_listeners = self.listeners.get(event_name, [])
        for listener in named_listeners:
            asyncio.create_task(listener(*args, **kwargs))
        all_listeners = self.listeners.get(Event.ALL, [])
        for listener in all_listeners:
            asyncio.create_task(listener(event_name, *args, **kwargs))


event_bus = EventBus()
