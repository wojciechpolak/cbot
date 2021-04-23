"""
# periodic.py
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
from contextlib import suppress
from enum import Enum
from typing import Callable

from cbot.server.logger import logger
from cbot.server.task import Task


class PeriodicRunStatus(Enum):
    CONTINUE = None
    DONE = 0
    ERROR_SOFT = 1
    ERROR_HARD = 2


class Periodic:
    def __init__(self, func: Callable, interval: int = None, task: Task = None):
        self.func = func
        self.interval = interval
        self.is_running = False
        self.task = task
        self._task = None

    async def start(self, *args, **kwargs):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._run(*args, **kwargs))

    async def stop(self):
        if self.is_running:
            self.is_running = False
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run(self, *args, **kwargs):
        while True:
            if self.task is None or not self.task.is_paused:
                try:
                    rs = await self.func(*args, **kwargs)
                    if rs is not PeriodicRunStatus.CONTINUE:
                        if rs is not PeriodicRunStatus.ERROR_SOFT:
                            logger.info('Stopping periodic run.')
                            break
                except Exception:
                    logger.exception('Exception')
            interval: int = 1
            if self.interval:
                interval = self.interval
            elif self.task:
                interval = getattr(self.task.data, 'interval', 1)
            await asyncio.sleep(interval)
        await self.stop()
