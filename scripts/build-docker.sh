#!/bin/bash
#
# build-docker.sh
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
#

set -xe

DIR="$(cd "$(dirname "$0")" && pwd)"

(cd "$DIR/../cbot/client_web" && npm run prebuild)
git describe --always --tags >cbot/.version
docker build . -t wap/cbot
