"""
# cron.py
#
# CBot Copyright (C) 2022-2025 Wojciech Polak
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

from __future__ import annotations
from typing import TYPE_CHECKING, List
import asyncio
import pycron

if TYPE_CHECKING:
    from cbot.server.task_manager import TaskManager

from cbot.server.logger import logger
from cbot.server.operation import Operation
from cbot.server.periodic import PeriodicTaskRunner, PeriodicRunStatus


class CronEntity:
    schedule: str
    op: Operation
    is_paused: bool = False

    def __init__(self, schedule: str, op: Operation, is_paused: bool = False):
        self.schedule = schedule
        self.op = op
        self.is_paused = is_paused

    def __str__(self):
        return f'{self.schedule} {self.op}{" (paused)" if self.is_paused else ""}'


class CronManager:

    def __init__(self, task_manager: TaskManager):
        self.cron_list: List[CronEntity] = []
        self.scheduler_job = None
        self.task_manager = task_manager

    def get_list(self):
        return self.cron_list

    def add(self, schedule: str, op: Operation):
        self.cron_list.append(CronEntity(schedule, op))
        self.task_manager.emit_lists()

    def modify(self, position: int, schedule: str, is_paused: bool = False):
        try:
            op = self.cron_list[position].op
            self.cron_list[position] = CronEntity(schedule, op, is_paused)
            return self.task_manager.RESP_OK
        except IndexError as exc:
            return str(exc)

    def pause(self, position: int):
        try:
            self.cron_list[position].is_paused = not self.cron_list[position].is_paused
            self.task_manager.emit_lists()
            return self.task_manager.RESP_OK
        except IndexError as exc:
            return str(exc)

    def delete(self, position: int, delete_all: bool = False) -> str:
        if delete_all:
            self.cron_list = []
            self.task_manager.emit_lists()
            return self.task_manager.RESP_OK
        try:
            del self.cron_list[position]
            self.task_manager.emit_lists()
            return self.task_manager.RESP_OK
        except IndexError as exc:
            return str(exc)

    async def scheduler_start(self):
        self.scheduler_job = PeriodicTaskRunner(self.scheduler_runner, interval=60)
        await self.scheduler_job.start()
        try:
            while self.scheduler_job.is_running:
                await asyncio.sleep(1)
        finally:
            await self.scheduler_job.stop()

    def scheduler_stop(self):
        self.scheduler_job.stop()

    async def scheduler_runner(self):
        for cron_entry in self.cron_list:
            if cron_entry.is_paused:
                continue
            if pycron.is_now(cron_entry.schedule):
                logger.info('Executing cron job (%s): %s',
                            cron_entry.schedule, cron_entry.op.cmd)
                self.task_manager.start(cron_entry.op)
        return PeriodicRunStatus.CONTINUE
