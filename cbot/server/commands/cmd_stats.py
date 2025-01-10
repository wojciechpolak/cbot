"""
# commands/cmd_stats.py
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


class StatsCommand(Command):
    """
    `STATS` command: Gets stats
    """

    async def execute(self, manager: TaskManager):
        stats = manager.get_stats()
        self.operation.data = stats
        self.operation.output = str(stats)
