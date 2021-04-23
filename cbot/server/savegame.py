"""
# savegame.py
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

import pickle
from datetime import datetime

from cbot.server import config
from cbot.server.event_bus import event_bus, Event
from cbot.server.logger import logger
from cbot.server.memstore import memstore
from cbot.server.task_manager import task_manager


def save_data():
    if not config.conf.datafile:
        return
    logger.info('Saving data to %s', config.conf.datafile)
    try:
        with open(config.conf.datafile, 'wb') as fp:
            memstore.add('savegame_last_update', datetime.now())
            snapshot = {
                'tasks': task_manager.to_savegame(),
                'memstore': memstore.to_savegame(),
            }
            pickle.dump(snapshot, fp)
    except Exception:
        logger.exception('Saving data failed.')


async def async_save_data():
    save_data()


async def load_data():
    if not config.conf.datafile:
        logger.info('No datafile specified!')
        return
    logger.info('Loading data from %s', config.conf.datafile)
    try:
        with open(config.conf.datafile, 'rb') as fp:
            snapshot = pickle.load(fp)
            task_manager.from_savegame(snapshot['tasks'])
            memstore.from_savegame(snapshot['memstore'])
    except IOError:
        pass
    except Exception:
        logger.exception('Loading data failed.')


event_bus.add_listener(Event.SAVEGAME, async_save_data)
