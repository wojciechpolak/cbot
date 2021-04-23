"""
# utils.py
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

import calendar
from datetime import datetime
from cbot.server.logger import logger


def parse_bool(arg: str) -> bool:
    if isinstance(arg, bool):
        return arg
    if arg.lower() in ('true', 'on', 'yes', '1'):
        return True
    if arg.lower() in ('false', 'off', 'no', '0'):
        return False
    logger.error('Invalid bool argument: %s', arg)
    return False


def get_timestamp(dt=None) -> int:
    if dt is None:
        dt = datetime.utcnow()
    return calendar.timegm(dt.utctimetuple())
