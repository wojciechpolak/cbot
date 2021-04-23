"""
# task_manager.py
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
import json
import pprint
import shlex
from datetime import datetime
from importlib import import_module, reload
from typing import Dict, List, Any

import pycron

from cbot import VERSION
from cbot.server import mail
from cbot.server.memstore import memstore
from cbot.server.event_bus import event_bus, Event
from cbot.server.logger import logger
from cbot.server.operation import Operation
from cbot.server.periodic import Periodic, PeriodicRunStatus
from cbot.server.task import Task, TaskInfo
from cbot.server.utils import get_timestamp

RESP_OK = 'OK'
RESP_ERR = 'ERR'


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


class TaskManager:
    def __init__(self):
        self.counter = 0
        self.scheduler_job = None
        self.task_list: List[Task] = []
        self.cron_list: List[CronEntity] = []
        self.ifttt_list: List[IftttEntity] = []
        self.start_time = datetime.now()

        event_bus.add_listener(Event.TICKER_UPDATE, self.ifttt_scan)
        event_bus.add_listener(Event.TASK_FINISHED, self.catch_task_finished)

    def add(self, task: Task):
        self.counter += 1
        task.id = self.counter
        self.task_list.append(task)

    def start(self, op: Operation):
        if 'ifttt' in op.kwargs:
            conditions = op.kwargs['ifttt']
            del op.kwargs['ifttt']
            self.ifttt_add(conditions, op)
            return
        if 'cron' in op.kwargs:
            cron_schedule = op.kwargs['cron']
            del op.kwargs['cron']
            self.cron_add(cron_schedule, op)
            return
        cmd = op.cmd
        mod = import_module('cbot.server.tasks.job_' + cmd)
        job = getattr(mod, 'job_' + cmd, None)
        if callable(job):
            self.add(Task(op, job, name=cmd))
            self.emit_lists()
        else:
            logger.error('Non-callable job: %s', cmd)

    def get_all_lists(self):
        return {
            'cron_list': self.cron_list,
            'ifttt_list': self.ifttt_list,
            'tasks': self.tasks_get_info_list(),
        }

    def emit_lists(self):
        event_bus.emit(Event.TASK_MANAGER, self.get_all_lists())

    def tasks_get_list(self):
        return self.task_list

    def tasks_get_info_list(self):
        return list(map(lambda x: x.to_info_dict(), self.task_list))

    def cron_get_list(self):
        return self.cron_list

    def cron_add(self, schedule: str, op: Operation):
        self.cron_list.append(CronEntity(schedule, op))
        self.emit_lists()

    def cron_modify(self, position: int, schedule: str, is_paused: bool = False):
        try:
            op = self.cron_list[position].op
            self.cron_list[position] = CronEntity(schedule, op, is_paused)
            return RESP_OK
        except IndexError as exc:
            return str(exc)

    def cron_pause(self, position: int):
        try:
            self.cron_list[position].is_paused = not self.cron_list[position].is_paused
            self.emit_lists()
            return RESP_OK
        except IndexError as exc:
            return str(exc)

    def cron_delete(self, position: int, delete_all: bool = False) -> str:
        if delete_all:
            self.cron_list = []
            self.emit_lists()
            return RESP_OK
        try:
            del self.cron_list[position]
            self.emit_lists()
            return RESP_OK
        except IndexError as exc:
            return str(exc)

    def ifttt_get_list(self):
        return self.ifttt_list

    def ifttt_add(self, conditions: str, op: Operation):
        for cond in conditions.split(';'):
            cond = cond.strip()
            self.ifttt_list.append(IftttEntity(cond, op))
        self.emit_lists()

    def ifttt_pause(self, position: int):
        try:
            self.ifttt_list[position].is_paused = not self.ifttt_list[position].is_paused
            self.emit_lists()
            return RESP_OK
        except IndexError as exc:
            return str(exc)

    def ifttt_delete(self, position: int, delete_all: bool = False) -> str:
        if delete_all:
            self.ifttt_list = []
            self.emit_lists()
            return RESP_OK
        try:
            del self.ifttt_list[position]
            self.emit_lists()
            return RESP_OK
        except IndexError as exc:
            return str(exc)

    async def ifttt_scan(self, tickers: Dict):
        for entry in self.ifttt_list[:]:
            if entry.is_paused:
                continue
            condition = entry.condition
            op = entry.op
            try:
                if eval(condition, {}, tickers):  # pylint: disable=eval-used
                    logger.info('Executing ifttt job (%s): %s', condition, op)
                    self.start(op)
                    self.ifttt_list.remove(entry)  # run only once
                else:
                    logger.debug('IFTTT no match: %s', condition)
            except Exception:
                self.ifttt_list.remove(entry)  # run only once
                logger.exception('IFTTT eval (%s)', condition)

    def kill(self, task_id: int) -> str:
        """Kills a single task"""
        t: Task = next(filter(lambda x: x.id == task_id, self.task_list), None)
        if t:
            t.kill()
            self.emit_lists()
            return RESP_OK
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

    def reload(self, cmd: str) -> str:  # pylint: disable=no-self-use
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

    async def scheduler_start(self):
        self.scheduler_job = Periodic(self.scheduler_runner, interval=60)
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
                self.start(cron_entry.op)
        return PeriodicRunStatus.CONTINUE

    def to_savegame(self):
        data = {
            'counter': self.counter,
            'cron_list': self.cron_list,
            'ifttt_list': self.ifttt_list,
            'tasks': list(map(lambda x: x.to_savegame(), self.task_list)),
        }
        logger.debug('task_manager::to_savegame: %s', data)
        return data

    def from_savegame(self, pick_data):
        logger.debug('task_manager::from_savegame: %s', pick_data)
        self.counter = pick_data['counter']
        self.cron_list = pick_data.get('cron_list', [])
        self.ifttt_list = pick_data.get('ifttt_list', [])

        task_info: TaskInfo
        for task_info in pick_data['tasks']:
            op = task_info.op
            name = task_info.name
            mod = import_module('cbot.server.tasks.job_' + op.cmd)
            job = getattr(mod, 'job_' + name, None)
            if callable(job):
                task = Task(op, job, name=name, task_info=task_info)
                self.task_list.append(task)

    async def process_request(self, request: str) -> Operation:
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
        cmd = op.cmd.upper()
        if cmd == 'PS':
            op.data = self.tasks_get_info_list()
            op.output = list(map(str, self.tasks_get_list()))
            self.emit_lists()
        elif cmd == 'INFO':
            try:
                task_id = int(op.args[0]) if len(op.args) > 0 else None
                task_info = self.get_info(task_id)
                op.data = task_info
                op.output = str(task_info)
            except (IndexError, ValueError) as exc:
                op.output = str(exc)
        elif cmd == 'MODIFY':
            try:
                task_id = int(op.args[0])
                op.output = self.modify_task_data(task_id, op)
            except (IndexError, ValueError) as exc:
                op.output = str(exc)
        elif cmd == 'PAUSE':
            try:
                task_id = int(op.args[0])
                op.output = self.pause_task(task_id)
            except (IndexError, ValueError) as exc:
                op.output = str(exc)
        elif cmd == 'RELOAD':
            op.output = self.reload(op.args[0])
        elif cmd == 'STATS':
            stats = self.get_stats()
            op.data = stats
            op.output = str(stats)
        elif cmd == 'KILL':
            args = ''.join(op.args)
            if args == 'all':
                self.kill_all()
            elif args.isdigit():
                op.output = self.kill(int(args))
            else:
                op.output = 'Argument missing'
        elif cmd == 'CLEAN':
            self.clean()
        elif cmd == 'GET':
            try:
                task_id = int(op.args[0]) if len(op.args) > 0 else None
                num = int(op.args[1]) if len(op.args) > 1 else None
                op.data = self.get_output(task_id, num=num)
            except (IndexError, ValueError) as exc:
                op.data = [{'ts': 0, 'taskId': 0, 'msg': str(exc)}]
        elif cmd == 'CRON':
            if 'rm' in op.kwargs:
                op.output = self.cron_delete(int(op.kwargs['rm']))
            elif 'pause' in op.kwargs:
                op.output = self.cron_pause(int(op.kwargs['pause']))
            elif 'modify' in op.kwargs and 'cron' in op.kwargs:
                op.output = self.cron_modify(int(op.kwargs['modify']),
                                             op.kwargs['cron'])
            else:
                res = list(map(lambda x: f'{x[0]}) {x[1]}', enumerate(self.cron_get_list())))
                op.data = res
                op.output = '\n'.join(res)
        elif cmd == 'IFTTT':
            if 'rm' in op.kwargs:
                op.output = self.ifttt_delete(int(op.kwargs['rm']))
            elif 'pause' in op.kwargs:
                op.output = self.ifttt_pause(int(op.kwargs['pause']))
            else:
                res = list(map(lambda x: f'{x[0]}) {x[1]}', enumerate(self.ifttt_get_list())))
                op.data = res
                op.output = '\n'.join(res)
        elif cmd == 'SAVEGAME':
            event_bus.emit(Event.SAVEGAME)
        elif cmd == 'MEMSTORE':
            if 'keys' in op.args:
                ret = memstore.get_keys()
            elif 'get' in op.kwargs:
                ret = memstore.get(op.kwargs['get'])
            else:
                ret = memstore.store
            op.data = ret
            if 'raw' in op.args:
                op.output = str(ret)
            else:
                op.output = pprint.pformat(ret, indent=2, width=1)
        elif cmd == 'SENDMAIL':
            mail.send_mail('Hello World!')
            op.output = 'Email sent'
        elif cmd == 'QUIT':
            op.output = 'Goodbye!'
        elif cmd in (
                'PING',
                'BIN_LIVE',
                'CRYPTO_ORDER',
                'CRYPTO_PF',
                'CRYPTO_STATS',
                'CRYPTO_TICKER',
                'CRYPTO_TSL',
                'CMC_LATEST'):
            self.start(op)
        else:
            op.output = 'Unknown command'
            op.resp_code = 'ERR'

    def parse_args(self, line: str):  # pylint: disable=no-self-use
        cmd_kwargs = {}
        cmd_args = shlex.split(line or '')
        for arg in cmd_args[:]:
            if '=' in arg:
                arg_t = arg.split('=', 1)
                cmd_kwargs[arg_t[0].strip()] = arg_t[1].strip()
                cmd_args.remove(arg)
        return cmd_args, cmd_kwargs

    def get_stats(self):
        savegame_last_update = memstore.get('savegame_last_update')
        if savegame_last_update:
            savegame_last_update = savegame_last_update.isoformat()
        return {
            'version': VERSION,
            'start_time': self.start_time.isoformat(),
            'start_time_ts': get_timestamp(self.start_time),
            'savegame_last_update': savegame_last_update,
            'uptime': str(datetime.now() - self.start_time),
            'uptime_ts': int((datetime.now() - self.start_time).total_seconds()),
        }


task_manager = TaskManager()
