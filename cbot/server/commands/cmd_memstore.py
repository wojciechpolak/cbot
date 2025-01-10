"""
# commands/cmd_memstore.py
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
import pprint
from typing import TYPE_CHECKING
from cbot.server.commands.base import Command
from cbot.server.memstore import memstore

if TYPE_CHECKING:
    from cbot.server.task_manager import TaskManager


class MemstoreCommand(Command):
    """
    `MEMSTORE` command
    """

    async def execute(self, manager: TaskManager):
        op = self.operation
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
