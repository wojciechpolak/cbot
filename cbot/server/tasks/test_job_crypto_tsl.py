"""
# test_job_crypto_tsl.py
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

from decimal import Decimal
from unittest import TestCase

from cbot.server.tasks import job_crypto_tsl
from cbot.server.tasks.job_crypto_tsl import Data


class Test(TestCase):

    def setUp(self) -> None:
        self.ticker = {}

    def test_calc_long_tsl_1_1(self):
        data: Data = Data()
        data.quantity = 1
        data.initialPrice = Decimal('40.00')
        data.stopOffsetPrice = Decimal('0.10')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '40.00',
            '40.10',
            '40.20',
            '40.15',
            '40.10',  # break
            '40.00',
            '35.00',
            '20.00',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_1(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('40.10'))

    def test_calc_long_tsl_1_2(self):
        data: Data = Data()
        data.aboveInitialPrice = False
        data.quantity = 1
        data.initialPrice = Decimal('40.00')
        data.stopOffsetPrice = Decimal('0.10')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '40.00',
            '39.95',
            '39.90',  # break
            '39.80',
            '50.00',
            '10.00',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_1(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('39.90'))

    def test_calc_long_tsl_1_2b(self):
        data: Data = Data()
        data.aboveInitialPrice = True
        data.quantity = 1
        data.initialPrice = Decimal('40.00')
        data.stopOffsetPrice = Decimal('0.10')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '40.00',
            '39.95',
            '39.90',  # no break here
            '39.80',
            '42.00',
            '41.90',  # break
            '40.00',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_1(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('41.90'))

    def test_calc_long_tsl_1_3(self):
        data: Data = Data()
        data.aboveInitialPrice = False
        data.quantity = 1
        data.initialPrice = Decimal('10000.00')
        data.limitPrice = Decimal('10500.00')
        data.stopOffsetPricePct = Decimal('5.0')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '10000',
            '10500',
            '10200',
            '11000',
            '10000',  # break
            '9000',
            '16000',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_1(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('10000'))
        self.assertEqual(data.stopPrice, Decimal('10450'))
        self.assertEqual(data.limitPrice, Decimal('10450'))

    def test_calc_long_tsl_1_3b(self):
        data: Data = Data()
        data.aboveInitialPrice = True
        data.quantity = 1
        data.initialPrice = Decimal('10000.00')
        data.limitPrice = Decimal('10500.00')
        data.stopOffsetPricePct = Decimal('5.0')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '10000',
            '10500',
            '10200',
            '11000',
            '10000',
            '9000',
            '16000',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_1(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('16000'))
        self.assertEqual(data.stopPrice, Decimal('15200.00'))
        self.assertEqual(data.limitPrice, Decimal('15200.00'))

    def test_calc_long_tsl_1_4(self):
        data: Data = Data()
        data.quantity = 1
        data.initialPrice = Decimal('10500.00')
        data.limitPrice = Decimal('11000.00')
        data.stopOffsetPricePct = Decimal('2.0')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '10500',
            '11500',
            '11200',  # break
            '11000',
            '12000',
            '10000',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_1(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('11200'))
        self.assertEqual(data.stopPrice, Decimal('11270'))
        self.assertEqual(data.limitPrice, Decimal('11270'))

    def test_calc_long_tsl_1_5(self):
        data: Data = Data()
        data.quantity = 1
        data.initialPrice = Decimal('1000.00')
        data.stopOffsetPricePct = Decimal('5.0')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '1000', '990', '995', '1005', '1006', '1007', '1008', '1009',
            '1100', '1090', '1095', '1105', '1106', '1107', '1108', '1109',
            '1200', '1190', '1195', '1205', '1206', '1207', '1208', '1209',
            '1300', '1290', '1295', '1305', '1306', '1307', '1308', '1309',
            '1400', '1390', '1395', '1405', '1406', '1407', '1408', '1409',
            '1500', '1490', '1495', '1505', '1506', '1507', '1508', '1509',
            '1600', '1590', '1595', '1605', '1606', '1607', '1608', '1609',
            '1700', '1690', '1695', '1705', '1706', '1707', '1708', '1709',
            '1800', '1790', '1795', '1805', '1806', '1807', '1808', '1809',
            '1900', '1890', '1895', '1905', '1906', '1907', '1908', '1909',
            '2000', '1990', '1995', '2005', '2006', '2007', '2008', '2009',
            '2010', '2020', '2030', '2040', '2050', '2060', '2080', '2090',
            '2080', '2070', '2060', '2050', '2040', '2030', '2020', '2010',
            '2000', '1990', '1980', '1970', '1960', '1950', '1940', '1930',
            '1920', '1910', '1900', '1890', '1880', '1870', '1860', '1850',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_1(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(is_done, True)
        self.assertEqual(data.currentPrice, Decimal('1980'))
        self.assertEqual(data.stopPrice, Decimal('1985.50'))
        self.assertEqual(data.limitPrice, Decimal('1985.50'))

        data = Data()
        data.quantity = 1
        data.initialPrice = Decimal('1000.00')
        data.stopOffsetPricePct = Decimal('5.0')
        data.reduceStopOffsetPriceBy = Decimal('0.5')
        job_crypto_tsl.calc_stop_offset_price(data)

        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(is_done, True)
        self.assertEqual(data.currentPrice, Decimal('2050'))
        self.assertEqual(data.stopPrice, Decimal('2058.25'))
        self.assertEqual(data.limitPrice, Decimal('2058.25'))

    def test_calc_long_tsl_1_6(self):
        data: Data = Data()
        data.quantity = 1
        data.initialPrice = Decimal('1000.00')
        data.stopOffsetPricePct = Decimal('10.0')
        data.aboveInitialPrice = True
        # data.aboveInitialPriceOffsetPct = Decimal('10.0')
        data.takeProfitPct = Decimal('10.0')
        job_crypto_tsl.calc_above_offset_price(data)
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '1000', '1100', '1200',
            '1101',  # takeProfit >= 1100
            '1100',
            '1000',  # should break, but AIP is 1000... FIXME
            '900',
            '800',
            '0',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_1(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('1101'))
        self.assertEqual(data.stopPrice, Decimal('1080'))

    def test_calc_long_tsl_2_1(self):
        data: Data = Data()
        data.quantity = 1
        data.initialPrice = Decimal('40.00')
        data.stopOffsetPrice = Decimal('0.10')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '40.00',
            '40.10',
            '40.20',
            '40.15',
            '40.10',  # break
            '40.00',
            '35.00',
            '20.00',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('40.10'))

    def test_calc_long_tsl_2_2(self):
        data: Data = Data()
        data.aboveInitialPrice = False
        data.quantity = 1
        data.initialPrice = Decimal('40.00')
        data.stopOffsetPrice = Decimal('0.10')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '40.00',
            '39.95',
            '39.90',  # break
            '39.80',
            '50.00',
            '10.00',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('39.90'))

    def test_calc_long_tsl_2_2b(self):
        data: Data = Data()
        data.aboveInitialPrice = True
        data.quantity = 1
        data.initialPrice = Decimal('40.00')
        data.stopOffsetPrice = Decimal('0.10')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '40.00',
            '39.95',
            '39.90',
            '39.80',
            '50.00',
            '10.00',  # break (AIP)
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('10.00'))

    def test_calc_long_tsl_2_3(self):
        data: Data = Data()
        data.aboveInitialPrice = False
        data.quantity = 1
        data.initialPrice = Decimal('10000.00')
        data.limitPrice = Decimal('10500.00')
        data.stopOffsetPricePct = Decimal('5.0')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '10000',
            '10500',
            '10200',
            '11000',
            '10000',  # break
            '9000',
            '16000',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('10000'))
        self.assertEqual(data.stopPrice, Decimal('10505'))
        self.assertEqual(data.limitPrice, Decimal('10505'))

    def test_calc_long_tsl_2_3b(self):
        data: Data = Data()
        data.aboveInitialPrice = True
        data.quantity = 1
        data.initialPrice = Decimal('10000.00')
        data.limitPrice = Decimal('10500.00')
        data.stopOffsetPricePct = Decimal('5.0')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '10000',
            '10500',
            '10200',
            '11000',
            '10000',  # break
            '9000',
            '16000',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('16000'))
        self.assertEqual(data.stopPrice, Decimal('15507.50000'))
        self.assertEqual(data.limitPrice, Decimal('15507.50000'))

    def test_calc_long_tsl_2_4(self):
        data: Data = Data()
        data.quantity = 1
        data.initialPrice = Decimal('10500.00')
        data.limitPrice = Decimal('11000.00')
        data.stopOffsetPricePct = Decimal('2.0')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '10500',
            '11500',
            '11200',  # break
            '11000',
            '12000',
            '10000',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('11200'))
        self.assertEqual(data.stopPrice, Decimal('11291.05'))
        self.assertEqual(data.limitPrice, Decimal('11291.05'))

    def test_calc_long_tsl_2_5(self):
        data: Data = Data()
        data.quantity = 10
        data.initialPrice = Decimal('1000')
        data.stopOffsetPricePct = Decimal('10')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '1000',
            '5000',
            '10000',
            '9000',  # break
            '8000',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('9000'))

    def test_calc_long_tsl_2_6(self):
        data: Data = Data()
        data.aboveInitialPrice = False
        data.quantity = 10
        data.initialPrice = Decimal('1000')
        data.stopOffsetPricePct = Decimal('10')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '1000',
            '950',
            '910',
            '900',  # break
            '800',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('900'))

    def test_calc_long_tsl_2_6b(self):
        data: Data = Data()
        data.aboveInitialPrice = True
        data.quantity = 10
        data.initialPrice = Decimal('1000')
        data.stopOffsetPricePct = Decimal('10')
        job_crypto_tsl.calc_stop_offset_price(data)
        last_price = [
            '1000',
            '950',
            '910',
            '900',
            '800',
        ]
        for lp in last_price:
            self.ticker['last'] = lp
            is_done = job_crypto_tsl.calc_long_tsl_2(data, self.ticker)
            print(data)
            if is_done:
                break
        self.assertEqual(data.currentPrice, Decimal('800'))
