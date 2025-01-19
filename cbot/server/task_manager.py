"""
# task_manager.py
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


import json
import shlex
from datetime import datetime
from importlib import import_module, reload
from typing import List, Any

from cbot import VERSION
from cbot.server.commands.factory import CommandFactory
from cbot.server.cron import CronManager
from cbot.server.event_bus import event_bus, Event
from cbot.server.ifttt import IftttManager
from cbot.server.logger import logger
from cbot.server.memstore import memstore
from cbot.server.operation import Operation
from cbot.server.task import Task, TaskMemento
from cbot.server.tasks.factory import JobFactory
from cbot.server.utils import get_timestamp


class TaskManager:

    RESP_OK = 'OK'
    RESP_ERR = 'ERR'

    def __init__(self):
        self.counter = 0
        self.task_list: List[Task] = []
        self.cron_manager = CronManager(self)
        self.ifttt_manager = IftttManager(self)
        self.start_time = datetime.now()

        event_bus.add_listener(Event.TICKER_UPDATE, self.ifttt_manager.scan)
        event_bus.add_listener(Event.TASK_FINISHED, self.catch_task_finished)

    def add(self, task: Task):
        self.counter += 1
        task.id = self.counter
        self.task_list.append(task)

    def start(self, op: Operation):
        if 'ifttt' in op.kwargs:
            conditions = op.kwargs['ifttt']
            del op.kwargs['ifttt']
            self.ifttt_manager.add(conditions, op)
            return
        if 'cron' in op.kwargs:
            cron_schedule = op.kwargs['cron']
            del op.kwargs['cron']
            self.cron_manager.add(cron_schedule, op)
            return
        job_strategy = JobFactory.create_job(op.cmd)
        task = Task(op, job_strategy.run, name=op.cmd)
        self.add(task)
        self.emit_lists()

    def get_all_lists(self):
        return {
            'cron_list': self.cron_manager.cron_list,
            'ifttt_list': self.ifttt_manager.ifttt_list,
            'tasks': self.tasks_get_info_list(),
        }

    def emit_lists(self):
        event_bus.emit(Event.TASK_MANAGER, self.get_all_lists())

    def tasks_get_list(self):
        return self.task_list

    def tasks_get_info_list(self):
        return [x.to_info_dict() for x in self.task_list]

    def kill(self, task_id: int) -> str:
        """Kills a single task"""
        t: Task = next(filter(lambda x: x.id == task_id, self.task_list), None)
        if t:
            t.kill()
            self.emit_lists()
            return self.RESP_OK
        return 'kill: unknown task id #%d' % task_id

    def kill_all(self):
        """Kills all tasks"""
        for t in self.task_list:
            t.kill()
        self.emit_lists()

    def pause_task(self, task_id: int) -> str:
        """Pauses and unpauses a single task"""
        t: Task = next(filter(lambda x: x.id == task_id, self.task_list), None)
        if t:
            ret = t.pause()
            self.emit_lists()
            return ret
        return 'pause: unknown task id #%d' % task_id

    def reload(self, cmd: str) -> str:
        mod = import_module('cbot.server.tasks.job_' + cmd)
        reload(mod)
        return 'Reloaded cbot.server.tasks.job_' + cmd

    def clean(self):
        """Removes finished tasks from task list"""
        for t in list(filter(lambda x: x.is_finished, self.task_list)):
            self.task_list.remove(t)
        self.emit_lists()

    def get_output(self, task_id: int = None, num: int = None) -> list:
        """Gets output from a single or many tasks"""
        if task_id == -1:
            res = []
            for t in self.task_list:
                res.extend(t.get_output(num))
            return res

        if task_id is None:
            task_id = self.task_list[-1].id if len(self.task_list) > 0 else 0
        t: Task = next(filter(lambda x: x.id == task_id, self.task_list), None)
        if t:
            return t.get_output(num)

        return [{
            'ts': 0,
            'taskId': 0,
            'msg': 'get_output: unknown task id #%d' % task_id
        }]

    def get_info(self, task_id: int = None) -> Any:
        """Gets info from a single task"""
        if task_id is None:
            task_id = self.task_list[-1].id if len(self.task_list) > 0 else 0
        t: Task = next(filter(lambda x: x.id == task_id, self.task_list), None)
        if t:
            return t.get_info()
        return 'get_info: unknown task id #%d' % task_id

    def modify_task_data(self, task_id: int, op: Operation) -> str:
        t: Task = next(filter(lambda x: x.id == task_id, self.task_list), None)
        if t:
            ret = t.modify_data(op.kwargs)
            self.emit_lists()
            return ret
        return 'modify_task_data: unknown task id #%d' % task_id

    async def catch_task_finished(self, _task_id: int):
        self.emit_lists()

    def savegame(self):
        event_bus.emit(Event.SAVEGAME)

    def create_memento(self):
        data = {
            'counter': self.counter,
            'cron_list': self.cron_manager.cron_list,
            'ifttt_list': self.ifttt_manager.ifttt_list,
            'tasks': [x.create_memento() for x in self.task_list],
        }
        logger.debug('task_manager::create_memento: %s', data)
        return data

    def restore_from_memento(self, pick_data):
        logger.debug('task_manager::restore_from_memento: %s', pick_data)
        self.counter = pick_data['counter']
        self.cron_manager.cron_list = pick_data.get('cron_list', [])
        self.ifttt_manager.ifttt_list = pick_data.get('ifttt_list', [])

        task_memento: TaskMemento
        for task_memento in pick_data['tasks']:
            op = task_memento.op
            name = task_memento.name
            job_strategy = JobFactory.create_job(op.cmd)
            task = Task(op, job_strategy.run, name=name, task_memento=task_memento)
            self.task_list.append(task)

    async def handle_request(self, request: str) -> Operation:
        op = Operation()
        if not request:
            return op
        try:
            data = json.loads(request)
            logger.debug('Incoming data: %s', data)
            if 'raw_input' in data:
                cmd_args, cmd_kwargs = task_manager.parse_args(data['raw_input'])
                op.cmd = cmd_args[0].lower()
                op.args = cmd_args[1:]
                op.kwargs = cmd_kwargs
            else:
                op.cmd = data['cmd'].lower()
                op.args = data['args']
                op.kwargs = data['kwargs']
        except Exception as exc:
            logger.exception('Exception')
            op.resp_code = 'ERR'
            op.output = 'ERR: %s' % exc
            return op

        await task_manager.process_cmd(op)

        if 'raw_input' not in data:
            op.output = None
        return op

    async def process_cmd(self, op: Operation):
        try:
            command = CommandFactory.create_command(op)
            await command.execute(self)
        except ValueError as exc:
            op.resp_code = 'ERR'
            op.output = str(exc)
            raise exc
        except Exception as exc:
            op.resp_code = 'ERR'
            op.output = f"Exception in command: {exc}"

    def parse_args(self, line: str):
        cmd_kwargs = {}
        cmd_args = shlex.split(line or '')
        for arg in cmd_args[:]:
            if '=' in arg:
                arg_t = arg.split('=', 1)
                cmd_kwargs[arg_t[0].strip()] = arg_t[1].strip()
                cmd_args.remove(arg)
        return cmd_args, cmd_kwargs

    def get_stats(self):
        memento_last_update = memstore.get('memento_last_update')
        if memento_last_update:
            memento_last_update = memento_last_update.isoformat()
        return {
            'version': VERSION,
            'start_time': self.start_time.isoformat(),
            'start_time_ts': get_timestamp(self.start_time),
            'memento_last_update': memento_last_update,
            'uptime': str(datetime.now() - self.start_time),
            'uptime_ts': int((datetime.now() - self.start_time).total_seconds()),
        }


task_manager = TaskManager()
