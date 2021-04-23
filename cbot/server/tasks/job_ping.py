"""
# job_ping.py
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
from typing import cast

from cbot.server.logger import logger
from cbot.server.periodic import Periodic, PeriodicRunStatus
from cbot.server.task import Task
from cbot.server.tasks.data import TaskData


class Data(TaskData):
    interval: int = 5
    iteration: int = 0
    max_iter: int = None

    def map_options(self, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        for arg in args:
            self.max_iter = int(arg)

        for k, v in kwargs.items():
            if k == 'max_iter':
                self.max_iter = int(v)
            elif k == 'interval':
                self.interval = int(v)
            elif k == 'desc':
                pass
            else:
                logger.error('Invalid call argument: %s', k)


async def job_ping(task: Task):
    if task.data is None:
        task.data = Data()
        task.data.map_options(task.op.args, task.op.kwargs)

    t1 = Periodic(job_ping_run, task=task)
    await t1.start(task)
    try:
        while t1.is_running:
            await asyncio.sleep(task.data.interval)
        task.set_finished()
    finally:
        await t1.stop()


async def job_ping_run(task: Task):
    printer = task.printer
    data = cast(Data, task.data)

    data.iteration += 1
    out = f'Ping #{data.iteration:d}'
    printer(out)
    if data.max_iter and data.max_iter <= data.iteration:
        return PeriodicRunStatus.DONE

    return PeriodicRunStatus.CONTINUE
