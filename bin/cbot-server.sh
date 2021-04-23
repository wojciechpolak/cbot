#!/bin/bash
#
# cbot-server.sh
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

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DIR="$( dirname $DIR )"

NAME=${NAME:-prod}
PIDFILE=${PIDFILE:-"$DIR/run/cbot-$NAME.pid"}
DATAFILE=${DATAFILE:-"$DIR/run/cbot-$NAME-savegame.data"}

echo "Running cbot-server-$NAME as `whoami`"

RUN_DIR=$(dirname $DATAFILE)
test -d $RUN_DIR || mkdir -p $RUN_DIR

# Activate the virtual environment
cd $DIR
[[ -e venv/bin/activate ]] && source venv/bin/activate

export PYTHONPATH="${PYTHONPATH}:$DIR"

exec ./cbot/run_server.py \
  --foreground \
  --datafile=$DATAFILE \
  --pidfile=$PIDFILE $@
