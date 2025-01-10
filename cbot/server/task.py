"""
# task.py
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

import time
import asyncio
import datetime
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Optional, Callable, Dict, Any

from cbot.server.event_bus import Event, event_bus
from cbot.server.logger import logger
from cbot.server.operation import Operation
from cbot.server.tasks.data import TaskData


async def catch(awaitable):
    try:
        with suppress(asyncio.CancelledError):
            return await awaitable
    except Exception:
        logger.exception('Exception')


class TaskMemento:
    id: int = 0
    name: str = ''
    state_name: str = ''
    output: []
    op: Operation = None
    start_time = datetime.datetime.now()
    data: TaskData = None

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


class Task:
    MAX_OUTPUT_LINES = 1000

    def __init__(self, op: Operation, func: Callable,
                 name: str = '', task_memento: TaskMemento = None):
        self.id = 0
        self.name = name
        self.state: TaskState = RunningState()
        self.output = []
        self.op = op
        self.start_time = datetime.datetime.now()
        self.data: Optional[TaskData] = None
        if task_memento:
            self.restore_from_memento(task_memento)
        if not self.is_finished:
            self.task = asyncio.create_task(catch(func(self)))

    def __repr__(self):
        desc = ''
        state = ''
        if self.is_paused:
            state = ' (paused)'
        elif self.is_finished:
            state = ' (finished)'
        if self.op.kwargs.get('desc'):
            desc = f' [{self.op.kwargs.get("desc")}]'
        return '#%d (%s), started %s%s%s' % \
               (self.id, self.name, self.start_time, desc, state)

    def __str__(self):
        return self.__repr__()

    @property
    def is_paused(self) -> bool:
        return isinstance(self.state, PausedState)

    @property
    def is_finished(self) -> bool:
        return isinstance(self.state, FinishedState)

    def to_info_dict(self, full=False) -> Any:
        res = {
            'id': self.id,
            'name': self.name,
            'start_time': int(datetime.datetime.timestamp(self.start_time)),
            'state': self.state.__class__.__name__,
            'is_paused': self.is_paused,
            'is_finished': self.is_finished,
            'desc': self.op.kwargs.get('desc'),
        }
        if full:
            res.update({
                'op': self.op.__dict__,
                # 'output': self.output, # FIXME
                'data': self.data.__dict__,
            })
        return res

    def create_memento(self) -> TaskMemento:
        memento = TaskMemento()
        memento.id = self.id
        memento.name = self.name
        memento.state_name = self.state.__class__.__name__
        memento.output = self.output
        memento.op = self.op
        memento.data = self.data
        memento.start_time = self.start_time
        return memento

    def restore_from_memento(self, memento: TaskMemento):
        self.id = memento.id
        self.state = STATE_MAP.get(memento.state_name, FinishedState)()
        self.output = memento.output
        self.start_time = memento.start_time
        self.data = memento.data

    def _printer(self, *args) -> str:
        if len(self.output) >= self.MAX_OUTPUT_LINES:
            self.output = self.output[-self.MAX_OUTPUT_LINES:]  # n-last elements
        str_args = ' '.join(map(str, args))
        out = {
            'ts': time.time(),
            'taskId': self.id,
            'msg': str_args,
        }
        self.output.append(out)
        event_bus.emit(Event.LOGGER, out)
        return str_args

    def printer(self, *args) -> str:
        str_args = self._printer(*args)
        logger.info(str_args)
        return str_args

    def printer_warning(self, *args) -> str:
        str_args = self._printer(*args)
        logger.warning(str_args)
        return str_args

    def printer_error(self, *args) -> str:
        str_args = self._printer(*args)
        logger.error(str_args)
        return str_args

    def get_output(self, num: int = None):
        if num:  # get latest num entries
            return self.output[-num:]  # pylint: disable=E1130
        return self.output

    def get_info(self) -> Any:
        info = self.to_info_dict(full=True)
        event_bus.emit(Event.TASK_INFO, {
            'taskId': self.id,
            'info': info,
        })
        return info

    def kill(self):
        if not self.is_finished:
            logger.info('Killing task #%d', self.id)
            self.task.cancel()
            self.set_finished()

    def set_finished(self):
        self.state.finish(self)

    def pause(self) -> str:
        self.state.pause(self)
        return 'OK'

    def modify_data(self, kwargs: Dict) -> str:
        self.op.kwargs = kwargs
        if self.data:
            self.data.map_options(None, kwargs)
        event_bus.emit(Event.TASK_MODIFIED, {
            'taskId': self.id
        })
        return 'OK'


class TaskState(ABC):
    """
    Abstract base for Task state.
    Each state decides what happens when we call pause() or finish().
    """
    @abstractmethod
    def pause(self, task: Task):
        pass

    @abstractmethod
    def finish(self, task: Task):
        pass


class RunningState(TaskState):
    def pause(self, task: Task):
        task.state = PausedState()
        logger.info('Pausing task #%d', task.id)

    def finish(self, task: Task):
        task.state = FinishedState()
        event_bus.emit(Event.TASK_FINISHED, {
            'taskId': task.id
        })


class PausedState(TaskState):
    def pause(self, task: Task):
        # Paused -> Running
        task.state = RunningState()
        logger.info('Unpausing task #%d', task.id)

    def finish(self, task: Task):
        task.state = FinishedState()
        event_bus.emit(Event.TASK_FINISHED, {
            'taskId': task.id
        })


class FinishedState(TaskState):
    def pause(self, task: Task):
        logger.debug('Task #%d is finished; cannot pause.', task.id)

    def finish(self, task: Task):
        logger.debug('Task #%d is already finished.', task.id)


STATE_MAP = {
    'RunningState': RunningState,
    'PausedState': PausedState,
    'FinishedState': FinishedState,
}
