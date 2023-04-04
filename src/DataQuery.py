import requests
import pandas as pd
from pandas import Timestamp
from datetime import datetime
import ftplib
import io
import re
import json
import time
import numpy as np
import math
from pathlib import Path
from fake_useragent import UserAgent

####!!! OBSOLETE, WILL BE DELETED LATER !!! ####


class YahooSession(requests.Session):

    def __init__(self, sleep_time:float=2.0):
        super(YahooSession, self).__init__()
        constants_path = Path(__file__).parents[1] / 'Config' / 'Constants.json'
        # Load the constants
        with open(constants_path, 'r') as f:
            constants = json.load(f)
        self.url = constants['sites']['yahoo_query']
        # Set the header to fake browser agent
        ua = UserAgent()
        self.headers = {'User-Agent':str(ua.chrome)}
        # Set the request time keeper
        self.sleep_time = sleep_time
        self.last_request = 0.0

    def get(self, url, **kwargs):
        # If the request is too new, sleep until enough time has passed
        rem_sleep_time = self.sleep_time - (time.time() - self.last_request)
        if rem_sleep_time > 0:
            time.sleep(rem_sleep_time)
        # Make the request
        result = super(YahooSession, self).get(url, **kwargs)
        return result


    @staticmethod
    def _force_float(elt):
        try:
            return float(elt)
        except Exception:
            return elt

    def _build_url(self, ticker, start_date=None, end_date=None, interval="1d"):
        # Initialize default values if none are given
        if end_date is None:
            end_seconds = int(pd.Timestamp("now").timestamp())
        else:
            end_seconds = int(pd.Timestamp(end_date).timestamp())
        if start_date is None:
            start_seconds = 0
        else:
            start_seconds = int(pd.Timestamp(start_date).timestamp())
        # Build the site and parameters for the get request
        site = self.url + ticker
        params = {"period1": start_seconds, "period2": end_seconds,
                  "interval": interval.lower(), "events": "div,splits"}

        return site, params

    def get_data(self, ticker, start_date=None, end_date=None, index_as_date=True,
                 interval="1d"):
        """Downloads historical stock price data into a pandas data frame.  Interval
           must be "1d", "1wk", or "1mo" for daily, weekly, or monthly data.

           @param: ticker
           @param: start_date = None
           @param: end_date = None
           @param: index_as_date = True
           @param: interval = "1d"
        """

        if interval not in ("1d", "1wk", "1mo"):
            raise AssertionError("interval must be of '1d', '1wk', or '1mo'")

        # Build and connect to URL
        site, params = self._build_url(ticker, start_date, end_date, interval)
        resp = self.get(site, params=params)
        # Throw the error in case of an error status code
        resp.raise_for_status()

        # Convert the response to JSON
        data = resp.json()

        # Get open / high / low / close / volume data
        frame = pd.DataFrame(data["chart"]["result"][0]["indicators"]["quote"][0])

        # add in adjclose
        try:
            frame["adjclose"] = data["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"]
        except KeyError:
            frame["adjclose"] = frame["close"]
        # get the date info
        temp_time = data["chart"]["result"][0]["timestamp"]

        frame.index = pd.to_datetime(temp_time, unit="s")
        frame.index = frame.index.map(lambda dt: dt.floor("d"))

        # frame = frame[["open", "high", "low", "close", "adjclose", "volume"]]
        # frame = frame[["open", "high", "low", "close", "volume"]]

        frame['ticker'] = ticker.upper()

        if not index_as_date:
            frame = frame.reset_index()
            frame.rename(columns={"index": "date"}, inplace=True)

        return frame

    @staticmethod
    def tickers_sp500():
        """Downloads list of tickers currently listed in the S&P 500 """
        # get list of all S&P 500 stocks
        sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        sp_tickers = sorted(sp500.Symbol.tolist())

        return sp_tickers

    @staticmethod
    def tickers_nasdaq():
        """Downloads list of tickers currently listed in the NASDAQ"""

        ftp = ftplib.FTP("ftp.nasdaqtrader.com")
        ftp.login()
        ftp.cwd("SymbolDirectory")

        r = io.BytesIO()
        ftp.retrbinary('RETR nasdaqlisted.txt', r.write)

        info = r.getvalue().decode()
        splits = info.split("|")

        tickers = [x for x in splits if "\r\n" in x]
        tickers = [x.split("\r\n")[1] for x in tickers if "NASDAQ" not in x != "\r\n"]
        tickers = [ticker for ticker in tickers if "File" not in ticker]

        ftp.close()

        return tickers

    @staticmethod
    def tickers_other():
        """Downloads list of tickers currently listed in the "otherlisted.txt"
           file on "ftp.nasdaqtrader.com" """
        ftp = ftplib.FTP("ftp.nasdaqtrader.com")
        ftp.login()
        ftp.cwd("SymbolDirectory")

        r = io.BytesIO()
        ftp.retrbinary('RETR otherlisted.txt', r.write)

        info = r.getvalue().decode()
        splits = info.split("|")

        tickers = [x for x in splits if "\r\n" in x]
        tickers = [x.split("\r\n")[1] for x in tickers]
        tickers = [ticker for ticker in tickers if "File" not in ticker]

        ftp.close()

        return tickers

    # TODO: Fix DOW tickers data retrieval
    @staticmethod
    def tickers_dow():
        """Downloads list of currently traded tickers on the Dow"""

        site = "https://finance.yahoo.com/quote/%5EDJI/components?p=%5EDJI"

        table = pd.read_html(site)[0]

        dow_tickers = sorted(table['Symbol'].tolist())

        return dow_tickers

    def get_quote_table(self, ticker, dict_result=True):
        """Scrapes data elements found on Yahoo Finance's quote page
           of input ticker

           @param: ticker
           @param: dict_result = True
        """

        site = "https://finance.yahoo.com/quote/" + ticker + "?p=" + ticker

        resp = self.get(site)

        tables = pd.read_html(resp.text)

        data = pd.concat(tables[0], tables[1])

        data.columns = ["attribute", "value"]

        price_etc = [elt for elt in tables if elt.iloc[0][0] == "Previous Close"][0]
        price_etc.columns = data.columns.copy()

        data = pd.concat(data, price_etc)

        quote_price = pd.DataFrame(["Quote Price", self.get_live_price(ticker)]).transpose()
        quote_price.columns = data.columns.copy()

        data = data.append(quote_price)

        data = data.sort_values("attribute")

        data = data.drop_duplicates().reset_index(drop=True)

        data["value"] = data.value.map(self._force_float)

        if dict_result:
            result = {key: val for key, val in zip(data.attribute, data.value)}
            return result

        return data

    def get_stats(self, ticker):
        """Scrapes information from the statistics tab on Yahoo Finance
           for an input ticker

           @param: ticker
        """

        stats_site = "https://finance.yahoo.com/quote/" + ticker + \
                     "/key-statistics?p=" + ticker

        stats_resp = self.get(stats_site)

        tables = pd.read_html(stats_resp.text)

        tables = [table for table in tables if table.shape[1] == 2]

        table = tables[0]
        table = pd.concat(tables)

        stats_dict = {}
        for _, s in table.iterrows():
            stats_dict[s[0]] = s[1]

        return stats_dict

    def get_stats_valuation(self, ticker):
        """Scrapes Valuation Measures table from the statistics tab on Yahoo Finance
           for an input ticker

           @param: ticker
        """

        stats_site = "https://finance.yahoo.com/quote/" + ticker + \
                     "/key-statistics?p=" + ticker

        stats_resp = self.get(stats_site)

        tables = pd.read_html(stats_resp.text)

        tables = [table for table in tables if "Trailing P/E" in table.iloc[:, 0].tolist()]

        table = tables[0].reset_index(drop=True)

        return table

    def _parse_json(self, url):
        html = self.get(url=url).text

        json_str = html.split('root.App.main =')[1].split(
            '(this)')[0].split(';\n}')[0].strip()
        json_data = json.loads(json_str)
        data = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']

        # return data
        new_data = json.dumps(data).replace('{}', 'null')
        new_data = re.sub(r'{[\'|\"]raw[\'|\"]:(.*?),(.*?)}', r'\1', new_data)

        json_info = json.loads(new_data)

        return json_info

    @staticmethod
    def _parse_table(json_info):
        df = pd.DataFrame(json_info)
        try:
            del df["maxAge"]
        except KeyError:
            pass
        if df.empty:
            return df


        df.set_index("endDate", inplace=True)
        df.index = pd.to_datetime(df.index, unit="s")

        df = df.transpose()
        df.index.name = "Breakdown"

        return df

    def get_income_statement(self, ticker, yearly=True, try_left=3):
        """Scrape income statement from Yahoo Finance for a given ticker

           @param: ticker
        """

        income_site = "https://finance.yahoo.com/quote/" + ticker + \
                      "/financials?p=" + ticker
        info_obtained = False
        while(not info_obtained):
            try:
                json_info = self._parse_json(income_site)
                info_obtained = (json_info["incomeStatementHistory"] is not None) if yearly \
                    else (json_info["incomeStatementHistoryQuarterly"] is not None)
            except IndexError:
                info_obtained = True
            except TypeError:
                if try_left > 0:
                    print('Type Error at', ticker, ', retrying in 5 seconds.')
                    time.sleep(5)
                else:
                    json_info = {'error': True}
        if 'error' in json_info and try_left > 0:
            return self.get_income_statement(ticker, yearly, try_left=try_left - 1)
        elif 'error' in json_info:
            temp = [[]]
        else:
            try:
                if yearly and try_left > 0:
                    temp = json_info["incomeStatementHistory"]["incomeStatementHistory"]
                elif try_left > 0:
                    temp = json_info["incomeStatementHistoryQuarterly"]["incomeStatementHistory"]
                else:
                    temp = [[]]
            except (IndexError, KeyError):
                temp = [[]]

        return self._parse_table(temp)

    def get_key_statistics(self, ticker):
        """Scrape key statistics from Yahoo Finance for a given ticker

           @param: ticker
        """

        stats_site = "https://finance.yahoo.com/quote/" + ticker + \
                      "/key-statistics?p=" + ticker

        json_info = self._parse_json(stats_site)

        stats = json_info["defaultKeyStatistics"]

        temp_s = pd.Series(stats)
        del temp_s['maxAge']

        return temp_s.transpose()

    def get_summary_details(self, ticker):
        """Scrape key statistics from Yahoo Finance for a given ticker

           @param: ticker
        """

        summary_site = "https://finance.yahoo.com/quote/" + ticker + \
                      "/financials?p=" + ticker

        json_info = self._parse_json(summary_site)

        temp = json_info["summaryDetail"]

        temp_df = pd.Series(temp)
        del temp_df['maxAge']

        return temp_df.transpose()

    def get_common_stock_count(self, ticker):
        """Scrapes balance sheet from Yahoo Finance for an input ticker

           @param: ticker
        """

        balance_sheet_site = "https://finance.yahoo.com/quote/" + ticker + \
                             "/balance-sheet?p=" + ticker

        json_info = self._parse_json(balance_sheet_site)
        try:
            temp = json_info["balanceSheetHistoryQuarterly"]["balanceSheetStatements"][0]['commonStock']
        except IndexError:
            try:
                temp = json_info["balanceSheetHistory"]["balanceSheetStatements"][0]['commonStock']
            except IndexError:
                temp = 1

        return temp

    def get_balance_sheet(self, ticker, yearly=True, try_left=5):
        """Scrapes balance sheet from Yahoo Finance for an input ticker

           @param: ticker
        """

        balance_sheet_site = "https://finance.yahoo.com/quote/" + ticker + \
                             "/balance-sheet?p=" + ticker
        info_obtained = False
        while(not info_obtained):
            try:
                json_info = self._parse_json(balance_sheet_site)
                info_obtained = (json_info["balanceSheetHistory"] is not None) if yearly \
                    else (json_info["balanceSheetHistoryQuarterly"] is not None)
            except IndexError:
                info_obtained = True
            except TypeError:
                if try_left > 0:
                    print('Type Error at', ticker, ', retrying in 5 seconds.')
                    time.sleep(5)
                    try_left -= 1
                else:
                    pass


        try:
            if yearly and try_left > 0:
                temp = json_info["balanceSheetHistory"]["balanceSheetStatements"]
            elif try_left > 0:
                temp = json_info["balanceSheetHistoryQuarterly"]["balanceSheetStatements"]
            else:
                temp = [[]]
        except (IndexError, KeyError):
            temp = [[]]

        return self._parse_table(temp)

    def get_cash_flow(self, ticker, yearly=True):
        """Scrapes the cash flow statement from Yahoo Finance for an input ticker

           @param: ticker
        """

        cash_flow_site = "https://finance.yahoo.com/quote/" + \
                         ticker + "/cash-flow?p=" + ticker

        json_info = self._parse_json(cash_flow_site)

        if yearly:
            temp = json_info["cashflowStatementHistory"]["cashflowStatements"]
        else:
            temp = json_info["cashflowStatementHistoryQuarterly"]["cashflowStatements"]

        return self._parse_table(temp)

    def get_financials(self, ticker, yearly=True, quarterly=True):
        """Scrapes financials data from Yahoo Finance for an input ticker, including
           balance sheet, cash flow statement, and income statement.  Returns dictionary
           of results.

           @param: ticker
           @param: yearly = True
           @param: quarterly = True
        """

        if not yearly and not quarterly:
            raise AssertionError("yearly or quarterly must be True")

        financials_site = "https://finance.yahoo.com/quote/" + ticker + \
                          "/financials?p=" + ticker

        json_info = self._parse_json(financials_site)

        result = {}

        if yearly:
            temp = json_info["incomeStatementHistory"]["incomeStatementHistory"]
            table = self._parse_table(temp)
            result["yearly_income_statement"] = table

            temp = json_info["balanceSheetHistory"]["balanceSheetStatements"]
            table = self._parse_table(temp)
            result["yearly_balance_sheet"] = table

            temp = json_info["cashflowStatementHistory"]["cashflowStatements"]
            table = self._parse_table(temp)
            result["yearly_cash_flow"] = table

        if quarterly:
            temp = json_info["incomeStatementHistoryQuarterly"]["incomeStatementHistory"]
            table = self._parse_table(temp)
            result["quarterly_income_statement"] = table

            temp = json_info["balanceSheetHistoryQuarterly"]["balanceSheetStatements"]
            table = self._parse_table(temp)
            result["quarterly_balance_sheet"] = table

            temp = json_info["cashflowStatementHistoryQuarterly"]["cashflowStatements"]
            table = self._parse_table(temp)
            result["quarterly_cash_flow"] = table

        return result

    def get_holders(self, ticker):
        """Scrapes the Holders page from Yahoo Finance for an input ticker

           @param: ticker
        """

        holders_site = "https://finance.yahoo.com/quote/" + \
                       ticker + "/holders?p=" + ticker

        holders_resp = self.get(holders_site)

        tables = pd.read_html(holders_resp.text)

        table_names = ["Major Holders", "Direct Holders (Forms 3 and 4)",
                       "Top Institutional Holders", "Top Mutual Fund Holders"]

        table_mapper = {key: val for key, val in zip(table_names, tables)}

        return table_mapper

    def get_analysts_info(self, ticker):
        """Scrapes the Analysts page from Yahoo Finance for an input ticker

           @param: ticker
        """

        analysts_site = "https://finance.yahoo.com/quote/" + ticker + \
                        "/analysts?p=" + ticker

        analysts_resp = self.get(analysts_site)

        tables = pd.read_html(analysts_resp.text)

        table_names = [table.columns[0] for table in tables]

        table_mapper = {key: val for key, val in zip(table_names, tables)}

        return table_mapper

    def get_live_price(self, ticker):
        """Gets the live price of input ticker

           @param: ticker
        """
        # Get the closest business day as starting time (prevents errors on weekends)
        now = pd.Timestamp.today()
        closest_bday = now
        # If it is before market open, get data from the day before
        # FIXME: Adapt to different market opening hours
        if now.hour < 9:
            closest_bday -= pd.Timedelta(days=1)
        # Subtract weekends
        if closest_bday.weekday() > 4:
            closest_bday -= pd.Timedelta(days=closest_bday.weekday() - 4)
        

        # Make the data request
        df = self.get_data(ticker, start_date=closest_bday.replace(hour=0, minute=0, second=0),
                           end_date=now)
        
        # The most recent adjusted close price is the price, round and return it 
        return np.round(float(df['adjclose']), decimals=2)

    def _raw_get_daily_info(self, site):

        resp = self.get(site)

        tables = pd.read_html(resp.text)

        df = tables[0].copy()

        df.columns = tables[0].columns

        del df["52 Week Range"]

        df["% Change"] = df["% Change"].map(lambda x: float(x.strip("%")))

        fields_to_change = [x for x in df.columns.tolist() if "Vol" in x
                            or x == "Market Cap"]

        for field in fields_to_change:

            if type(df[field][0]) == str:
                df[field] = df[field].str.strip("B").map(self._force_float)
                df[field] = df[field].map(lambda x: x if type(x) == str
                                          else x * 1000000000)

                df[field] = df[field].map(lambda x: x if type(x) == float else
                                          self._force_float(x.strip("M")) * 1000000)

        return df

    def get_day_most_active(self):
        return self._raw_get_daily_info("https://finance.yahoo.com/most-active?offset=0&count=100")

    def get_day_gainers(self):
        return self._raw_get_daily_info("https://finance.yahoo.com/gainers?offset=0&count=100")

    def get_day_losers(self):
        return self._raw_get_daily_info("https://finance.yahoo.com/losers?offset=0&count=100")

    def get_top_crypto(self):
        """Gets the top 100 Cryptocurrencies by Market Cap"""

        resp = self.get("https://finance.yahoo.com/cryptocurrencies?offset=0&count=100")

        tables = pd.read_html(resp.text)

        df = tables[0].copy()

        df["% Change"] = df["% Change"].map(lambda x: float(x.strip("%").
                                                            strip("+").
                                                            replace(",", "")))
        del df["52 Week Range"]
        del df["1 Day Chart"]

        fields_to_change = [x for x in df.columns.tolist() if "Volume" in x
                            or x == "Market Cap" or x == "Circulating Supply"]

        for field in fields_to_change:

            if type(df[field][0]) == str:
                df[field] = df[field].str.strip("B").map(self._force_float)
                df[field] = df[field].map(lambda x: x if type(x) == str
                                          else x * 1000000000)

                df[field] = df[field].map(lambda x: x if type(x) == float else
                                          self._force_float(x.strip("M")) * 1000000)

        return df

    def get_dividends(self, ticker, start_date=None, end_date=None, index_as_date=True):
        """Downloads historical dividend data into a pandas data frame.

           @param: ticker
           @param: start_date = None
           @param: end_date = None
           @param: index_as_date = True
        """

        # build and connect to URL
        site, params = self._build_url(ticker, start_date, end_date, "1d")
        resp = self.get(site, params=params)

        if not resp.ok:
            raise AssertionError(resp.json())

        # get JSON response
        data = resp.json()

        # check if there is data available for dividends
        if "dividends" not in data["chart"]["result"][0]['events']:
            raise AssertionError("There is no data available on dividends, or none have been granted")

        # get the dividend data
        frame = pd.DataFrame(data["chart"]["result"][0]['events']['dividends'])

        frame = frame.transpose()

        frame.index = pd.to_datetime(frame.index, unit="s")
        frame.index = frame.index.map(lambda dt: dt.floor("d"))

        # sort in to chronological order
        frame = frame.sort_index()

        frame['ticker'] = ticker.upper()

        # remove old date column
        frame = frame.drop(columns='date')

        frame = frame.rename({'amount': 'dividend'}, axis='columns')

        if not index_as_date:
            frame = frame.reset_index()
            frame.rename(columns={"index": "date"}, inplace=True)

        return frame

    def get_splits(self, ticker, start_date=None, end_date=None, index_as_date=True):
        """Downloads historical stock split data into a pandas data frame.

           @param: ticker
           @param: start_date = None
           @param: end_date = None
           @param: index_as_date = True
        """

        # build and connect to URL
        site, params = self._build_url(ticker, start_date, end_date, "1d")
        resp = self.get(site, params=params)

        if not resp.ok:
            raise AssertionError(resp.json())

        # get JSON response
        data = resp.json()

        # check if there is data available for splits
        if "splits" not in data["chart"]["result"][0]['events']:
            raise AssertionError("There is no data available on stock splits, or none have occured")

        # get the split data
        frame = pd.DataFrame(data["chart"]["result"][0]['events']['splits'])

        frame = frame.transpose()

        frame.index = pd.to_datetime(frame.index, unit="s")
        frame.index = frame.index.map(lambda dt: dt.floor("d"))

        # sort in to chronological order
        frame = frame.sort_index()

        frame['ticker'] = ticker.upper()

        # remove unnecessary columns
        frame = frame.drop(columns=['date', 'denominator', 'numerator'])

        if not index_as_date:
            frame = frame.reset_index()
            frame.rename(columns={"index": "date"}, inplace=True)

        return frame

    def get_earnings(self, ticker):
        """Scrapes earnings data from Yahoo Finance for an input ticker

           @param: ticker
        """

        financials_site = "https://finance.yahoo.com/quote/" + ticker + \
                          "/financials?p=" + ticker

        json_info = self._parse_json(financials_site)

        temp = json_info["earnings"]

        result = {"quarterly_results": pd.DataFrame.from_dict(temp["earningsChart"]["quarterly"]),
                  "yearly_revenue_earnings": pd.DataFrame.from_dict(temp["financialsChart"]["yearly"]),
                  "quarterly_revenue_earnings": pd.DataFrame.from_dict(temp["financialsChart"]["quarterly"])}

        return result

    def get_price(self, stocks, date=None, verbose=False):
        stock_names = [stock.quote for stock in stocks if stock.quote is not None]
        prices = []
        for name in stock_names:
            try:
                if name[-2:] == '.X':
                    prices.append([1.0, 1.0, 1.0, 1.0, 0.0])
                else:
                    if date:
                        if date.date() == datetime.today().date():
                            prices.append(self.get_live_price(name))
                        else:
                            quote_result = self.get_data(name, start_date=date, end_date=date + pd.DateOffset(1))
                            prices.append(quote_result)
                    else:
                        prices.append(self.get_live_price(name))
                if verbose:
                    print(name, 'price obtained!')
            except AssertionError:
                print('No Stock found with name ', name)
                prices.append(np.zeros((5,)))
            except IndexError:
                print('No price found for ', name)
                prices.append(np.zeros((5,)))
        prices = np.asarray(prices)
        prices = prices.astype(np.double)
        return prices.round(decimals=2)

    @staticmethod
    def _get_currency_quote(cur1, cur2):
        if not isinstance(cur1, list):
            cur1 = [cur1]
        if not isinstance(cur2, list):
            cur2 = [cur2]
        cur1 = ['' if cur == 'USD' else cur for cur in cur1]
        result = [cur_1 + cur_2 + '=X' for (cur_1, cur_2) in zip(cur1, cur2)]
        return result

    def get_currency_price(self, cur1, cur2):
        cur_quotes = [self._get_currency_quote(cur_1.name, cur_2.name) for (cur_1, cur_2) in zip(cur1, cur2)]
        cur_prices = []
        for idx, cur_pair in enumerate(cur_quotes):
            cur_pair = cur_pair[0]
            if cur_pair == 'USD=X' or (len(cur_pair) >= 6 and cur_pair[:3] == cur_pair[3:6]):
                close_price = 1.0
            else:
                price_quote = self.get_live_price(cur_pair)
                close_price = price_quote[0]
            cur_prices.append(close_price)
            print(cur_pair, 'price obtained.')
        return cur_prices

    @staticmethod
    def _date_to_q(date: Timestamp):
        return ((date.month - 1) // 3)

    def get_income_summary(self, positions, states, verbose=False):
        statements = np.zeros((len(positions), len(states) * 4))
        last_q_one_hot = np.zeros((len(positions), 4), dtype=np.int)
        for idx, position in enumerate(positions):
            if position.quote[-2:] != '.X':
                statement = self.get_income_statement(ticker=position.quote, yearly=False)
                if not statement.empty:
                    statement_dates = statement.keys()
                    last_quarter = self._date_to_q(statement_dates.max())
                    statement_q = np.asarray([self._date_to_q(date) for date in statement_dates])
                    _, q_idx = np.unique(statement_q, return_index=True)
                    statement_q_idx = statement_q[np.sort(q_idx)]
                    statement_dates = statement_dates[np.sort(q_idx)]
                    state_vals = np.zeros((statements.shape[1],))
                    for state_idx, state in enumerate(states):
                        state_val = np.zeros((4,))
                        state_temp = statement.loc[state, statement_dates]
                        for i in range(len(state_temp) - 1):
                            if state_temp[i] == state_temp[i+1]:
                                state_temp[i+1] = 0.0
                        state_val[statement_q_idx] = state_temp
                        state_vals[state_idx*4:state_idx*4+4] = state_val

                    last_q_one_hot[idx, last_quarter] = 1
                else:
                    state_vals = 0.0
                statements[idx, :] = state_vals

                if verbose:
                    print(position.quote, 'income statement obtained.')
        return statements, last_q_one_hot

    def get_share_count(self, positions, verbose=False):
        share_counts = []
        for pos in positions:
            if pos.quote[-2:] != '.X':
                stats = self.get_key_statistics(pos.quote)
                try:
                    share_count = stats['impliedSharesOutstanding']
                except KeyError:
                    share_count = None
                if share_count is None or math.isnan(share_count):
                    try:
                        share_count = stats['sharesOutstanding']
                    except KeyError:
                        share_count = None
                if share_count is None or math.isnan(share_count):
                    share_count = self.get_common_stock_count(pos.quote)
                if verbose:
                    print(pos.quote, 'share count obtained.')
            else:
                share_count = 1
            share_counts.append(share_count)

        return share_counts

    def get_book_value(self, positions, verbose=False):
        book_values = np.zeros((len(positions),))
        for idx, position in enumerate(positions):
            if position.quote[-2:] != '.X':
                balance = self.get_balance_sheet(ticker=position.quote, yearly=False)
                if not balance.empty:
                    statement_dates = balance.keys()
                    bv_date = statement_dates.max()
                    book_value = balance.loc['totalStockholderEquity', bv_date]
                else:
                    book_value = 0.0
                book_values[idx] = book_value

                if verbose:
                    print(position.quote, 'book value obtained.')
        return book_values

