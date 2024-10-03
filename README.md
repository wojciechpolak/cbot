# CBot

This project began as a playground for developing crypto trading bots
and has since evolved into a more general-purpose task execution
server, written in Python. It supports creating and managing running
jobs via both a CLI client and a Web UI.

⚠️ Note: This is a personal project and is not intended for general
use, nor is it likely to be polished for broader distribution.

## Running

### Running with Docker (out of the box)

```shell
docker run -it -p 8080:80 -p 2269:2269 --name cbot ghcr.io/wojciechpolak/cbot
```

### Running with Docker Compose

```shell
docker compose up
```

### Building Docker image from source

```shell
./scripts/build-docker.sh
APP_IMAGE=wap/cbot docker compose up
```

### Running from the source code

1. Clone the repository

   ```shell
   git clone https://github.com/wojciechpolak/cbot.git
   cd cbot
   ```

2. Install dependencies

   Install Python dependencies using
   [Poetry](https://python-poetry.org/) or PIP.

   ```shell
   $ poetry install
   # or
   $ pip install -r requirements.txt
   ```

   Install Web UI dependencies.

   ```shell
   (cd cbot/client_web && npm ci) 
   ```

3. Prepare the configuration file

    Start by copying the sample configuration file located at
    `conf/etc/cbot/cbot.conf`.

    Save the copied file in one of the following locations (based on
    your preference):

    - `/etc/cbot/cbot.conf`
    - `~/.cbot.conf`
    - `./cbot.conf`

4. Run the Server

   ```shell
   ./bin/cbot-server.sh
   ```

5. Run the CLI client

   ```shell
   ./bin/cbot-client.sh
   ```

6. Run the Web UI client

   ```shell
   ./bin/cbot-web-serve.sh
   ```

7. Open in Browser

Visit http://localhost:4200 to access the Web UI.

## Client Commands

* clean
* cmc_latest
  - num=25
  - sortby=
* cron
  - rm=1
  - pause=1
  - modify=1 cron="* * * * *"
* crypto_stats
  - exchange=binance
  - symbol=BTC/USDT
  - timeframe=1h
* crypto_ticker
  - exchange=binance
  - symbol=pair1,pair2
* crypto_tsl (Trailing Stop Loss)
  - aboveInitialPrice
  - algo=std1/std2
  - buy
  - exchange=binance
  - initialPrice=
  - interval=60
  - quantity=100
  - quoteOrderQty=100
  - simulate/dry
  - stopLoss
  - stopOffsetPrice=500
  - stopOffsetPricePct=5
  - symbol=pair
* get
  - 1 25
* ifttt
  - rm=1
  - pause=1
* info
  - 1
* kill
  - 1 all
* ls
* memstore
  - keys
  - raw
  - get=key_name
* modify
  - 1
  - key=val
* pause
  - 1
* ping
  - 25
  - interval=5
* ps
* reload
  - job_name
* quit
* savegame
* sendmail
* stats
* status

## Server Jobs

### crypto-tsl output

`#1; SS;EOS/USDT;QTY 1.84;H 7.5021;CUR 7.5021 (13.8268) (PD:+0.9556/+14.60%);STOP 7.2770 (GAP:0.2251/+1.00%);GR%:0.00/80.0;LIMIT 7.2770`

* S     - Simulation
* SS    - Simulation / Start
* QTY   - Quantity
* H     - The highest price (during this task run)
* CUR   - Last price
* PD    - Price difference (currentPrice - initialPrice)
* STOP  - Stop price
* GAP   - stopPriceChange (currentPrice - stopPrice)
* GR%   - offsetPctRaisedBy / reduceStopOffsetPriceByMax
* LIMIT - Limit price

With each iteration, but only when currentPrice > lastHigh:

* stopOffsetPrice = stopOffsetPricePct / 100 * price
* stopPrice = lastHigh - stopOffsetPrice
* limitPrice = stopPrice - limitOffsetPrice

## License

This project is licensed under the GNU General Public License v3.0.
See the [COPYING](COPYING) file for details.

### Icon Attribution

The icons used in this project are from the
[Twitter Twemoji](https://github.com/twitter/twemoji)
project and are licensed under the
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.
