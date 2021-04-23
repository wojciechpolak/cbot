"""
# config.py
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

import os
import configparser
from typing import Tuple

from cbot.server import DEFAULT_PORT


class Config:
    bind: Tuple[str, int] = ('localhost', DEFAULT_PORT)
    datafile: str = 'cbot-savegame.data'
    foreground: bool = False
    sections = {
        'server': {},
        'mail': {},
    }

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


conf = Config()


def read_config():
    config_file = configparser.ConfigParser()
    config_file.read([
        '/etc/cbot/cbot.conf',
        os.path.expanduser('~/.cbot.conf'),
        './cbot.conf'
    ])

    for section in config_file.sections():
        if section not in conf.sections:
            conf.sections[section] = {}
        for k, v in config_file.items(section):
            conf.sections[section][k] = v
