"""
# ifttt.py
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
from typing import TYPE_CHECKING, List, Dict

if TYPE_CHECKING:
    from cbot.server.task_manager import TaskManager

from cbot.server.logger import logger
from cbot.server.operation import Operation


class IftttEntity:
    condition: str
    op: Operation
    is_paused: bool = False

    def __init__(self, condition: str, op: Operation, is_paused: bool = False):
        self.condition = condition
        self.op = op
        self.is_paused = is_paused

    def __str__(self):
        return f'{self.condition} {self.op}{" (paused)" if self.is_paused else ""}'


class IftttManager:
    def __init__(self, task_manager: TaskManager):
        self.ifttt_list: List[IftttEntity] = []
        self.task_manager = task_manager

    def get_list(self):
        return self.ifttt_list

    def add(self, conditions: str, op: Operation):
        for cond in conditions.split(';'):
            cond = cond.strip()
            self.ifttt_list.append(IftttEntity(cond, op))
        self.task_manager.emit_lists()

    def pause(self, position: int):
        try:
            self.ifttt_list[position].is_paused = not self.ifttt_list[position].is_paused
            self.task_manager.emit_lists()
            return self.task_manager.RESP_OK
        except IndexError as exc:
            return str(exc)

    def delete(self, position: int, delete_all: bool = False) -> str:
        if delete_all:
            self.ifttt_list = []
            self.task_manager.emit_lists()
            return self.task_manager.RESP_OK
        try:
            del self.ifttt_list[position]
            self.task_manager.emit_lists()
            return self.task_manager.RESP_OK
        except IndexError as exc:
            return str(exc)

    async def scan(self, tickers: Dict):
        for entry in self.ifttt_list[:]:
            if entry.is_paused:
                continue
            condition = entry.condition
            op = entry.op
            try:
                if eval(condition, {}, tickers):  # pylint: disable=eval-used
                    logger.info('Executing ifttt job (%s): %s', condition, op)
                    self.task_manager.start(op)
                    self.ifttt_list.remove(entry)  # run only once
                else:
                    logger.debug('IFTTT no match: %s', condition)
            except Exception:
                self.ifttt_list.remove(entry)  # run only once
                logger.exception('IFTTT eval (%s)', condition)
