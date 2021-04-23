#!/usr/bin/env python3
"""
# run_client.py
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

import sys
import cmd
import getopt
import os.path
from datetime import datetime

try:
    import readline
except ImportError:
    readline = None

from cbot.client_cli.tcp_client import Client

HISTFILE = os.path.expanduser('~/.cbot_history')
HISTFILE_SIZE = 1000


class Shell(cmd.Cmd):
    intro = 'Welcome'
    prompt = '> '

    def __init__(self, client: Client):
        cmd.Cmd.__init__(self)
        self.client = client

    def preloop(self):
        if readline and os.path.exists(HISTFILE):
            readline.read_history_file(HISTFILE)

    def postloop(self):
        if readline:
            readline.set_history_length(HISTFILE_SIZE)
            readline.write_history_file(HISTFILE)

    def call(self, name, arg):
        raw_input = name
        if arg:
            raw_input += ' ' + arg
        res = self.client.call(raw_input=raw_input)
        if 'output' in res:
            if isinstance(res['output'], list):
                for line in res['output']:
                    print(line)
            else:
                print(res['output'])

    def emptyline(self) -> bool:
        return False

    def do_EOF(self, _line):  # pylint: disable=invalid-name,no-self-use
        return True

    def do_ping(self, arg):
        """
          - 25
          - interval=5
        """
        self.call('PING', arg)

    def complete_ping(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = ['cron=', 'desc=', 'ifttt=', 'interval=']
        return list(filter(lambda x: x.startswith(text), k))

    def do_crypto_pf(self, arg):
        """
          - exchange=binance
          - symbol=
        """
        self.call('CRYPTO_PF', arg)

    def complete_crypto_pf(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = ['cron=', 'desc=', 'ifttt=', 'exchange=', 'symbol=']
        return list(filter(lambda x: x.startswith(text), k))

    def do_crypto_order(self, arg):
        self.call('CRYPTO_ORDER', arg)

    def complete_crypto_order(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = [
            'buy',
            'cron=',
            'desc=',
            'exchange=',
            'ifttt=',
            'orderTypeLimit',
            'orderTypeMarket',
            'orderTypeStopLoss',
            'orderTypeStopLossLimit',
            'orderTypeTakeProfit',
            'orderTypeTakeProfitLimit',
            'price=',
            'quantity=',
            'quoteOrderQty=',
            'sell',
            'simulate',
            'stopPrice=',
            'symbol=',
        ]
        return list(filter(lambda x: x.startswith(text), k))

    def do_crypto_tsl(self, arg):
        """
          TSL (Trailing Stop Loss)
          - aboveInitialPrice
          - aboveInitialPriceOffset=
          - aboveInitialPriceOffsetPct=
          - algo=std1/std2
          - buy
          - exchange=binance
          - initialPrice=
          - interval=60
          - lastHigh=
          - quantity=100
          - quoteOrderQty=100
          - simulate/dry
          - stopLoss
          - stopOffsetPrice=500
          - stopOffsetPricePct=5
          - symbol=pair,
          - takeProfit=1000
          - takeProfitPct=2
        """
        self.call('CRYPTO_TSL', arg)

    def complete_crypto_tsl(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = [
            'aboveInitialPrice',
            'aboveInitialPriceOffset=',
            'aboveInitialPriceOffsetPct=',
            'algo=',  # std1/std2
            'buy',
            'cron=',
            'desc=',
            'exchange=',
            'ifttt=',
            'initialPrice=',
            'interval=',
            'lastHigh=',
            'quantity=',
            'quoteOrderQty=',
            'simulate',
            'stopLoss',
            'stopOffsetPrice=',
            'stopOffsetPricePct=',
            'symbol=',
            'takeProfit=',
            'takeProfitPct=',
        ]
        return list(filter(lambda x: x.startswith(text), k))

    def do_crypto_stats(self, arg):
        """
          - exchange=binance
          - limit=int
          - symbol=BTC/USDT
          - timeframe=1h
        """
        self.call('CRYPTO_STATS', arg)

    def complete_crypto_stats(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = ['cron=', 'desc=', 'ifttt=', 'exchange=', 'limit=', 'symbol=', 'timeframe=']
        return list(filter(lambda x: x.startswith(text), k))

    def do_crypto_ticker(self, arg):
        """
          - exchange=binance
          - symbol=pair1,pair2
        """
        self.call('CRYPTO_TICKER', arg)

    def complete_crypto_ticker(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = ['cron=', 'desc=', 'ifttt=', 'exchange=', 'symbol=']
        return list(filter(lambda x: x.startswith(text), k))

    def do_cmc_latest(self, arg):
        """
          - num=25
          - quote=BTC
          - sortby=percent_change_1h
        """
        self.call('CMC_LATEST', arg)

    def complete_cmc_latest(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = ['cron=', 'desc=', 'ifttt=', 'num=', 'quote=', 'sortby=']
        return list(filter(lambda x: x.startswith(text), k))

    def do_bin_live(self, arg):
        """
          - streams=klines,!ticker@arr
          - streamAllTickers
          - sortby=5m
          - symbol=BTC/USDT
          - symbolsTrackAdd
          - trackCmcLatest=true
        """
        self.call('BIN_LIVE', arg)

    def complete_bin_live(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = ['cron=', 'desc=', 'ifttt=', 'streams=', 'streamAllTickers',
             'sortby=', 'symbol=', 'symbolsTrackAdd', 'trackCmcLatest=']
        return list(filter(lambda x: x.startswith(text), k))

    def do_ps(self, arg):
        self.call('PS', arg)

    def do_ls(self, arg):
        self.do_ps(arg)

    def do_reload(self, arg):
        """
          - task_name
        """
        self.call('RELOAD', arg)

    def do_stats(self, arg):
        self.call('STATS', arg)

    def do_status(self, arg):
        self.do_stats(arg)

    def do_kill(self, arg):
        """
          - 1 all
        """
        self.call('KILL', arg)

    def do_clean(self, arg):
        self.call('CLEAN', arg)

    def do_info(self, arg):
        """
          - 1
        """
        self.call('INFO', arg)

    def do_modify(self, arg):
        """
          - 1
          - key=val
        """
        self.call('MODIFY', arg)

    def do_pause(self, arg):
        """
          - 1
        """
        self.call('PAUSE', arg)

    def do_get(self, arg):
        """
          - 1 25
        """
        raw_input = 'GET'
        if arg:
            raw_input += ' ' + arg
        res = self.client.call(raw_input=raw_input)
        for line in res['data']:
            ts = line['ts']
            task_id = line['taskId']
            msg = line['msg']
            print('%s %d - %s' % (
                datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), task_id, msg))

    def do_cron(self, arg):
        """
  ┌───────────── minute (0 - 59)
  │ ┌───────────── hour (0 - 23)
  │ │ ┌───────────── day of the month (1 - 31)
  │ │ │ ┌───────────── month (1 - 12)
  │ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday;
  │ │ │ │ │                                   7 is also Sunday on some systems)
  │ │ │ │ │
  │ │ │ │ │
  * * * * *

  1) cron
  2) cron rm=1
  3) cron modify=2 cron="* * * * *"
  4) cron pause=3
        """
        self.call('CRON', arg)

    def complete_cron(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = ['cron=', 'pause=', 'rm=', 'modify=']
        return list(filter(lambda x: x.startswith(text), k))

    def do_ifttt(self, arg):
        """
          - rm=1
          - pause=1
        """
        self.call('IFTTT', arg)

    def complete_ifttt(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = ['pause=', 'rm=']
        return list(filter(lambda x: x.startswith(text), k))

    def do_memstore(self, arg):
        """
          - keys
          - raw
          - get=key_name
        """
        self.call('MEMSTORE', arg)

    def do_savegame(self, _arg):
        self.call('SAVEGAME', _arg)

    def complete_memstore(self, text, _line, _begidx, _endidx):  # pylint: disable=R0201
        k = ['get=', 'keys', 'raw']
        return list(filter(lambda x: x.startswith(text), k))

    def do_sendmail(self, arg):
        self.call('SENDMAIL', arg)

    def do_quit(self, arg):
        self.call('QUIT', arg)
        return True


def main():
    interactive = True
    server = None
    verbosity = 0

    getopt_shorts = 'ev:'
    getopt_longs = (
        'verbosity=',
        'server=',
    )

    try:
        opts, args = getopt.getopt(sys.argv[1:], getopt_shorts, getopt_longs)
        cmd_args = args
        for o, a in opts:
            if o in ('-v', '--verbosity'):
                verbosity = int(a)
            elif o == '-e':
                interactive = False
            elif o == '--server':
                if ':' in a:
                    addr, port = a.split(':', 1)
                    server = [addr, int(port)]
                else:
                    server = [a, None]
    except getopt.GetoptError:
        print("Usage: %s [OPTION...]" % sys.argv[0])
        print("""%s -- BOT

        -v, --verbosity=LEVEL
            --server=HOST:PORT
        """ % (sys.argv[0]))
        sys.exit(0)

    client = Client(server=server, verbose=bool(verbosity))
    if client.connect() != 0:
        print("Can't connect!")
        sys.exit(1)

    if interactive:
        shell = Shell(client)
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            pass
        finally:
            shell.postloop()
    else:
        if not cmd_args:
            print('Nothing to send!')
            sys.exit(1)
        args = ' '.join(cmd_args[1:])
        ri = cmd_args[0]
        if args:
            ri += ' ' + args
        res = client.call(raw_input=ri)
        if cmd_args[0] == 'get':
            for line in res['data']:
                ts = line['ts']
                task_id = line['taskId']
                msg = line['msg']
                print('%s %d - %s' % (
                    datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'), task_id, msg))
        elif isinstance(res['output'], list):
            for line in res['output']:
                print(line)
        elif isinstance(res['output'], str) and res['output']:
            print(res['output'])
        elif verbosity:
            print(res['resp_code'])
        client.disconnect()


if __name__ == '__main__':
    main()
