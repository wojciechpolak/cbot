"""
# operation.py
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

from typing import Any


class Operation:
    def __init__(self, cmd: str = None, args=None, kwargs=None):
        self.cmd: str = cmd
        self.args = args or []
        self.kwargs = kwargs or {}
        self.resp_code: str = 'OK'
        self.output: Any = ''
        self.data: Any = None

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def to_response(self):
        return {
            'resp_code': self.resp_code,
            'output': self.output,
            'data': self.data,
        }

    def to_stream_response(self):
        return {
            'stream': 'RESULT',
            'data': {
                'cmd': self.cmd,
                'resp_code': self.resp_code,
                'output': self.output,
                'data': self.data,
            }
        }
