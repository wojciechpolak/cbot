#!/usr/bin/env python3
"""
# run_server.py
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
import getopt
import grp
import logging
import os
import pwd
import signal
import sys
import time
from asyncio import AbstractEventLoop

from setproctitle import setproctitle  # pylint: disable=no-name-in-module

from cbot import __version__
from cbot.server import logger as logger_service, exchange, DEFAULT_PORT
from cbot.server import config
from cbot.server.logger import logger
from cbot.server.savegame import save_data, load_data
from cbot.server.task_manager import task_manager
from cbot.server.tcp_server import Server
from cbot.server.ws_server import Server as WsServer


async def shutdown(sig_name: str, ws_server: WsServer, loop: AbstractEventLoop):
    logger.info('Caught %s, shutting down...', sig_name)
    await exchange.close_all()
    tasks = [task for task in asyncio.all_tasks() if task is not
             asyncio.current_task()]
    list(map(lambda task: task.cancel(), tasks))
    await asyncio.gather(*tasks, return_exceptions=True)

    ws_server.close()
    await ws_server.wait_closed()

    logger.debug('Finished awaiting cancelled tasks')
    loop.stop()


def main():
    config.read_config()
    logger_service.setup(config.conf.sections['server'].get('logfile'))

    getopt_shorts = 'fv:'
    getopt_longs = [
        'verbosity=',
        'foreground',
        'bind=',
        'user=',
        'datafile=',
        'pidfile=',
    ]

    user = None
    pidfile = None

    try:
        opts, _args = getopt.getopt(sys.argv[1:], getopt_shorts, getopt_longs)
        for o, a in opts:
            if o in ('-v', '--verbosity'):
                verbosity = int(a)
                if verbosity == 0:
                    logger.setLevel(logging.ERROR)
                elif verbosity == 1:
                    logger.setLevel(logging.INFO)
                elif verbosity > 1:
                    logger.setLevel(logging.DEBUG)
            elif o == '--bind':
                if ':' in a:
                    addr, port = a.split(':', 1)
                    config.conf.bind = (addr, int(port))
                else:
                    config.conf.bind = (a, DEFAULT_PORT)
            elif o in ('-f', '--foreground'):
                config.conf.foreground = True
            elif o == '--datafile':
                config.conf.datafile = a
            elif o == '--pidfile':
                pidfile = a
            elif o == '--user':
                user = a
    except getopt.GetoptError:
        print("Usage: %s [OPTION...]" % sys.argv[0])
        print("""%s -- BOT

        -v, --verbosity=LEVEL
            --bind=ADDR[:PORT]
            --user=USER[:GROUP]
            --pidfile=FILENAME
            --datafile=FILENAME
        -f, --foreground
        """ % (sys.argv[0]))
        sys.exit(0)

    try:
        if not config.conf.foreground:
            os.chdir('/')
            os.umask(0)

            pid = os.fork()
            if pid > 0:
                time.sleep(0.1)
                os._exit(0)  # pylint: disable=protected-access

            os.setsid()
            os.close(0)
            os.close(1)
            os.close(2)

        setproctitle('CBot')

        if pidfile:
            try:
                with open(pidfile, 'w') as fp:  # pylint: disable=unspecified-encoding
                    fp.write('%d\n' % os.getpid())
            except IOError as exc:
                logger.error('Error writing PID file %s. %s', pidfile, exc)

        if user:
            try:
                if ':' in user:
                    user, group = user.split(':', 1)
                    gid = grp.getgrnam(group).gr_gid
                else:
                    gid = None
                u = pwd.getpwnam(user)
                os.setegid(gid if gid else u.pw_gid)
                os.seteuid(u.pw_uid)
            except Exception:
                logger.error('Cannot change user privileges (%s).', user)

        logger.info('Starting CBot (%s)', _get_version())

        loop = asyncio.get_event_loop()
        server = Server(loop, config.conf.bind[0], config.conf.bind[1])
        server.listen()
        ws_server = WsServer(config.conf.bind[0], config.conf.bind[1] + 1)

        for sig_name in ('SIGINT', 'SIGTERM'):
            loop.add_signal_handler(
                getattr(signal, sig_name),
                lambda: asyncio.create_task(
                    shutdown(sig_name, ws_server, loop)))  # pylint: disable=cell-var-from-loop

        asyncio.ensure_future(server.run(), loop=loop)
        asyncio.ensure_future(ws_server.run(), loop=loop)
        asyncio.ensure_future(load_data(), loop=loop)
        asyncio.ensure_future(task_manager.scheduler_start(), loop=loop)

        try:
            loop.run_forever()
        finally:
            server.close()
            loop.close()
            save_data()

    except Exception:
        logger.exception('Initialization failed.')


def _get_version():
    return __version__


if __name__ == '__main__':
    main()
