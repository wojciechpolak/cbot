"""
# ws_server.py
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

import asyncio
import json
from contextlib import suppress
from decimal import Decimal
from typing import Set, Any

from websockets.server import serve as ws_serve
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.server import WebSocketServerProtocol, WebSocketServer

from cbot.server.event_bus import event_bus, Event
from cbot.server.logger import logger
from cbot.server.task_manager import task_manager

WEBSOCKET_PORT = 2269


class JsonCustomEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, Event):
            return str(o.value)
        return json.JSONEncoder.default(self, o)


class Server:
    server: WebSocketServer = None

    def __init__(self, addr: str, port: int = WEBSOCKET_PORT):
        self.addr = addr
        self.port = port
        self.connections: Set[WebSocketServerProtocol] = set()

    async def run(self):
        logger.info('Listening websocket at %s:%d', self.addr, self.port)
        self.server = await ws_serve(self._handler, self.addr, self.port)
        event_bus.add_listener(Event.ALL, self.event_to_all)

    def close(self):
        if self.server:
            self.server.close()

    async def wait_closed(self):
        if self.server:
            return await self.server.wait_closed()
        return None

    async def _handler(self, ws: WebSocketServerProtocol, _path: str):
        logger.debug('Received connection from %s', ws.remote_address)
        self.connections.add(ws)

        consumer_task = asyncio.ensure_future(self.consumer_handler(ws, _path))
        producer_task = asyncio.ensure_future(self.producer_handler(ws, _path))
        try:
            with suppress(asyncio.CancelledError):
                _done, pending = await asyncio.wait(
                    [consumer_task, producer_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
        finally:
            logger.debug('Closing connection with %s', ws.remote_address)
            try:
                await ws.close()
            except Exception:
                pass
            self.connections.remove(ws)

    async def consumer_handler(self, ws: WebSocketServerProtocol, _path: str):
        try:
            async for request in ws:
                is_done = False
                if request:
                    op = await task_manager.process_request(request)
                    payload = json.dumps(op.to_stream_response(), default=str)
                    await ws.send(payload)
                    if op.cmd == 'QUIT':
                        is_done = True
                else:
                    is_done = True
                if is_done:
                    break
        except ConnectionClosedError:
            pass

    async def producer_handler(self, ws: WebSocketServerProtocol, _path: str):
        while True:
            data = await self.producer()
            if data:
                d = {
                    'stream': 'test',
                    'data': data,
                }
                payload = json.dumps(d, default=str)
                await ws.send(payload)

    async def producer(self):
        await asyncio.sleep(1)
        return None

    async def send_to_all(self, stream_name: str, data: Any = None):
        if data is None:
            data = {}
        if self.connections:
            d = {
                'stream': stream_name,
                'data': data
            }
            payload = json.dumps(d, cls=JsonCustomEncoder)
            await asyncio.gather(
                *[con.send(payload) for con in self.connections],
                return_exceptions=True  # This ensures that one failing send doesn't cancel others
            )

    async def event_to_all(self, event_name: str, data: Any = None):
        await self.send_to_all(event_name, data)
