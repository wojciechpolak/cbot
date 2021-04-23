"""
# tcp_client.py
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

import json
import socket

from cbot.server import DEFAULT_PORT


class Client:

    def __init__(self, server=None, verbose=False):
        if server is None:
            server = ['localhost', DEFAULT_PORT]
        if server[1] is None:
            server[1] = DEFAULT_PORT
        self.server = server
        self.socket = None
        self.verbose = verbose

    def __del__(self):
        self.disconnect()

    def connect(self):
        if self.verbose:
            print(f'Connecting to {self.server[0]}:{self.server[1]:d}')
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.socket.connect(tuple(self.server))
            return 0
        except socket.error as msg:
            self.disconnect()
            return f'Cannot connect. {msg}'

    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def call(self, name: str = None, args=None, kwargs=None,
             raw_input: str = None):
        if not args:
            args = ()
        if kwargs is None:
            kwargs = {}
        retries = 3
        while retries:
            if not self.socket:
                self.connect()
            if self.socket:
                if raw_input:
                    data = {
                        'raw_input': raw_input
                    }
                else:
                    data = {
                        "cmd": name,
                        "args": args,
                        "kwargs": kwargs,
                    }
                self.__send(data)
                try:
                    res = self.__recv()
                    if res != -1:
                        return res
                except ConnectionResetError:
                    pass
            retries -= 1
        raise Exception('CBot call failed.')

    def __send(self, data):
        try:
            blob = json.dumps(data)
            if self.verbose:
                print('SEND', blob)
            self.socket.sendall(blob.encode('utf8') + b'\r\n')
            return 0
        except Exception as exc:
            print('Exception', exc)
            return -1

    def __recv(self):
        res = ''
        while True:
            chunk = self.socket.recv(4096).decode('utf8')
            res += chunk
            if len(chunk) < 4096:
                break
        if not res:
            self.disconnect()
            return -1  # Connection closed

        data = json.loads(res)
        if self.verbose:
            print('GOT', data)
        return data
