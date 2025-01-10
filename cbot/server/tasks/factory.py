"""
# tasks/factory.py
#
# CBot Copyright (C) 2025 Wojciech Polak
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

from cbot.server.tasks.base import JobStrategy
from cbot.server.tasks.job_bin_live import JobBinLive
from cbot.server.tasks.job_cmc_latest import JobCmcLatest
from cbot.server.tasks.job_crypto_order import JobCryptoOrder
from cbot.server.tasks.job_crypto_pf import JobCryptoPf
from cbot.server.tasks.job_crypto_stats import JobCryptoStats
from cbot.server.tasks.job_crypto_ticker import JobCryptoTicker
from cbot.server.tasks.job_crypto_tsl import JobCryptoTsl
from cbot.server.tasks.job_ping import JobPing

class JobFactory:
    """
    Creates a concrete JobStrategy based on operation.cmd or other params.
    """

    @staticmethod
    def create_job(cmd: str) -> JobStrategy:
        cmd_lower = cmd.lower()
        if cmd_lower == 'ping':
            return JobPing()
        elif cmd_lower == 'bin_live':
            return JobBinLive()
        elif cmd_lower == 'cmc_latest':
            return JobCmcLatest()
        elif cmd_lower == 'crypto_order':
            return JobCryptoOrder()
        elif cmd_lower == 'crypto_pf':
            return JobCryptoPf()
        elif cmd_lower == 'crypto_stats':
            return JobCryptoStats()
        elif cmd_lower == 'crypto_ticker':
            return JobCryptoTicker()
        elif cmd_lower == 'crypto_tsl':
            return JobCryptoTsl()
        raise ValueError(f'Unknown job command: {cmd}')
