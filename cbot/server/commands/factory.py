"""
# commands/factory.py
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

from cbot.server.commands.base import Command
from cbot.server.commands.cmd_clean import CleanCommand
from cbot.server.commands.cmd_cron import CronCommand
from cbot.server.commands.cmd_get import GetCommand
from cbot.server.commands.cmd_ifttt import IftttCommand
from cbot.server.commands.cmd_info import InfoCommand
from cbot.server.commands.cmd_kill import KillCommand
from cbot.server.commands.cmd_memstore import MemstoreCommand
from cbot.server.commands.cmd_modify import ModifyCommand
from cbot.server.commands.cmd_pause import PauseCommand
from cbot.server.commands.cmd_ps import PsCommand
from cbot.server.commands.cmd_quit import QuitCommand
from cbot.server.commands.cmd_reload import ReloadCommand
from cbot.server.commands.cmd_run import RunCommand
from cbot.server.commands.cmd_savegame import SaveGameCommand
from cbot.server.commands.cmd_sendmail import SendmailCommand
from cbot.server.commands.cmd_stats import StatsCommand
from cbot.server.operation import Operation


class CommandFactory:
    """
    Maps a command string to a concrete Command class.
    """

    _command_map = {
        'CLEAN': CleanCommand,
        'CRON': CronCommand,
        'GET': GetCommand,
        'IFTTT': IftttCommand,
        'INFO': InfoCommand,
        'KILL': KillCommand,
        'MEMSTORE': MemstoreCommand,
        'MODIFY': ModifyCommand,
        'PAUSE': PauseCommand,
        'PS': PsCommand,
        'QUIT': QuitCommand,
        'RELOAD': ReloadCommand,
        'RUN': RunCommand,
        'SAVEGAME': SaveGameCommand,
        'SENDMAIL': SendmailCommand,
        'STATS': StatsCommand,
    }

    @classmethod
    def create_command(cls, operation: Operation) -> Command:
        cmd_upper = operation.cmd.upper() if operation.cmd else ''
        cmd_class = cls._command_map.get(cmd_upper)

        if not cmd_class:
            # Fallback / unknown command
            raise ValueError(f"Unknown command '{operation.cmd}'")

        return cmd_class(operation)
