#
# Copyright 2016 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from numpy import nan
import pandas as pd
from pandas.tslib import Timedelta

from zipline.testing.fixtures import (
    ZiplineTestCase,
    WithDataPortal
)


class TestDataPortal(WithDataPortal, ZiplineTestCase):

    ASSET_FINDER_EQUITY_SIDS = (1,)
    START_DATE = pd.Timestamp('2016-08-03')
    END_DATE = pd.Timestamp('2016-08-03')

    @classmethod
    def init_class_fixtures(cls):
        # TODO; Should this use calendar?
        cls.minutes = pd.date_range('2016-08-03 9:31',
                                    '2016-08-03 9:36',
                                    freq='min',
                                    tz='US/Eastern').tz_convert('UTC')
        super(TestDataPortal, cls).init_class_fixtures()

    @classmethod
    def make_equity_minute_bar_data(cls):
        yield 1, pd.DataFrame(
            {
                'open': [nan, 103.50, 102.50, 104.50, 101.50, nan],
                'high': [nan, 103.90, 102.90, 104.90, 101.90, nan],
                'low': [nan, 103.10, 102.10, 104.10, 101.10, nan],
                'close': [nan, 103.30, 102.30, 104.30, 101.30, nan],
                'volume': [0, 1003, 1002, 1004, 1001, 0]
            },
            index=cls.minutes,
        )

    def test_get_last_traded_dt(self):
        # dt cases:
        # dt == last traded.
        # last traded is 1 before dt.
        # last traded is two before dt.
        # no last_traded
        asset = self.asset_finder.retrieve_asset(1)
        self.assertTrue(pd.isnull(
            self.data_portal.get_last_traded_dt(
                asset, self.minutes[0], 'minute')))
        # asset cases:
        # equities, futures
        pass

    def test_bar_count_for_simple_transforms(self):
        # July 2015
        # Su Mo Tu We Th Fr Sa
        #           1  2  3  4
        #  5  6  7  8  9 10 11
        # 12 13 14 15 16 17 18
        # 19 20 21 22 23 24 25
        # 26 27 28 29 30 31

        # half an hour into july 9, getting a 4-"day" window should get us
        # all the minutes of 7/6, 7/7, 7/8, and 31 minutes of 7/9

        july_9_dt = self.trading_calendar.open_and_close_for_session(
            pd.Timestamp("2015-07-09", tz='UTC')
        )[0] + Timedelta("30 minutes")

        self.assertEqual(
            (3 * 390) + 31,
            self.data_portal._get_minute_count_for_transform(july_9_dt, 4)
        )

        #    November 2015
        # Su Mo Tu We Th Fr Sa
        #  1  2  3  4  5  6  7
        #  8  9 10 11 12 13 14
        # 15 16 17 18 19 20 21
        # 22 23 24 25 26 27 28
        # 29 30

        # nov 26th closed
        # nov 27th was an early close

        # half an hour into nov 30, getting a 4-"day" window should get us
        # all the minutes of 11/24, 11/25, 11/27 (half day!), and 31 minutes
        # of 11/30
        nov_30_dt = self.trading_calendar.open_and_close_for_session(
            pd.Timestamp("2015-11-30", tz='UTC')
        )[0] + Timedelta("30 minutes")

        self.assertEqual(
            390 + 390 + 210 + 31,
            self.data_portal._get_minute_count_for_transform(nov_30_dt, 4)
        )
