"""
# tcp_server.py
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
from asyncio import AbstractEventLoop

from cbot.server.logger import logger
from cbot.server.task_manager import task_manager


class Server:
    CHUNK_LIMIT = 1024

    def __init__(self, loop: AbstractEventLoop, addr: str, port: int):
        self.loop = loop
        self.addr = addr
        self.port = port
        self.server = None

    def listen(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.addr, self.port))
        self.server.listen(1)
        self.server.setblocking(False)
        logger.info('Listening at %s:%d', self.addr, self.port)

    async def run(self):
        while True:
            client, addr = await self.loop.sock_accept(self.server)
            self.loop.create_task(self.handle_client(client, addr))

    def close(self):
        self.server.close()

    async def handle_client(self, client: socket, addr):
        logger.debug('Received connection from %s:%d', addr[0], addr[1])
        while True:
            request = await self.read_request(client)
            is_done = False
            if request:
                op = await task_manager.process_request(request)
                payload = json.dumps(op.to_response(), default=str)
                await self.send_response(client, payload)
                if op.cmd == 'QUIT':
                    is_done = True
            else:
                is_done = True
            if is_done:
                logger.debug('Closing connection with %s:%d', addr[0], addr[1])
                client.close()
                break

    async def read_request(self, client: socket) -> str:
        request = ''
        while True:
            chunk = (await self.loop.sock_recv(client, self.CHUNK_LIMIT)).decode('utf8')
            request += chunk
            if len(chunk) < self.CHUNK_LIMIT:
                break
        return request

    def send_response(self, client: socket, response: str):
        return self.loop.sock_sendall(client, response.encode('utf8') + b'\r\n')
