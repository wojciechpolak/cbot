"""
# logger.py
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

import logging
import logging.handlers

FORMAT = '%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s'
DATE_FMT = '%Y-%m-%d %H:%M:%S'

logger = logging.getLogger('cbot')


def setup(logfile: str = None):
    logger.setLevel(logging.INFO)

    if logfile:
        handler = logging.handlers.WatchedFileHandler(logfile)
        handler.setFormatter(logging.Formatter(FORMAT, DATE_FMT))
        logger.addHandler(handler)

    has_stream_handler = False
    for h in (logger.handlers or []):
        if type(h) is logging.StreamHandler:  # pylint: disable=C0123
            has_stream_handler = True

    if not has_stream_handler:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(FORMAT, DATE_FMT))
        logger.addHandler(handler)
