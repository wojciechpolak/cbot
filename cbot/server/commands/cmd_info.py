"""
# commands/cmd_info.py
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


class InfoCommand(Command):
    """
    `INFO` command: Gets info from a single task.
    """

    async def execute(self, manager: TaskManager):
        task_id = int(self.operation.args[0]) if len(self.operation.args) > 0 else None
        task_info = manager.get_info(task_id)
        self.operation.data = task_info
        self.operation.output = str(task_info)
