"""
# commands/cmd_cron.py
#
# CBot Copyright (C) 2025 Wojciech Polak
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
from typing import TYPE_CHECKING
from cbot.server.commands.base import Command

if TYPE_CHECKING:
    from cbot.server.task_manager import TaskManager


class CronCommand(Command):
    """
    `CRON` command
    """

    async def execute(self, manager: TaskManager):
        op = self.operation
        if 'rm' in op.kwargs:
            op.output = manager.cron_delete(int(op.kwargs['rm']))
        elif 'pause' in op.kwargs:
            op.output = manager.cron_pause(int(op.kwargs['pause']))
        elif 'modify' in op.kwargs and 'cron' in op.kwargs:
            op.output = manager.cron_modify(int(op.kwargs['modify']),
                                            op.kwargs['cron'])
        else:
            res = list(map(lambda x: f'{x[0]}) {x[1]}', enumerate(manager.cron_get_list())))
            op.data = res
            op.output = '\n'.join(res)
