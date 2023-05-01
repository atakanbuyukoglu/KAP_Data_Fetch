from .KAP import KAP
import yfinance as yf
import numpy as np
import pandas as pd


class Company():

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker.upper()

        # Initialize the info for the KAP website
        self.kap_website = KAP()
        self.company_info = self.update_info(online=False)

    def update_info(self, online=True):
        # Update the info on the KAP database
        self.kap_website.update_companies(self.ticker, online=online)
        self.kap_website.get_mkk_id(ticker=self.ticker)
        company_info = self.kap_website.get_company(self.ticker)

        # Return the company info
        return company_info
    
    def get_price(self):
        return self.kap_website.get_price(self.ticker)
        return self.kap_website.get_stats(self.ticker)
    
    def get_balance_sheet(self, online=False):
        balance_sheet = self.kap_website.get_balance_sheet(self.ticker, online=online)
        if isinstance(balance_sheet, str) and 'unavailable' in balance_sheet:
            raise ValueError(balance_sheet)
        return balance_sheet
    
    # TODO: Implement a way to approximate next earnings date
    def get_next_earnings_date():
        raise NotImplementedError
    
    # TODO: Get the historical prices from yahooquery
    def get_historical_prices():
        raise NotImplementedError

    def get_latest_balance_sheet(self):
        balance_sheet = self.get_balance_sheet()
        return balance_sheet.iloc[-1,:]
    
    def get_cash_flow(self):
        return self.kap_website.get_cash_flow(self.ticker)
    
    def get_latest_cash_flow(self):
        return self.get_cash_flow().iloc[-1,:]
    
    def get_income_statement(self):
        return self.kap_website.get_income_statement(self.ticker)
    
    def get_latest_income_statement(self):
        return self.get_income_statement().iloc[-1,:]
    
    def get_share_count(self):
        query_ticker = self.kap_website.get_query_ticker(self.ticker)
        stats = self.key_stats[query_ticker]
        share_count = stats['sharesOutstanding']

        return share_count
    
    def get_market_cap(self):
        share_count = self.get_share_count()
        price = self.get_price()
        return share_count * price
    
    def get_net_debt(self):
        balance_sheet = self.get_latest_balance_sheet()
        return balance_sheet['NetDebt']

    def get_enterprise_value(self):
        return self.get_market_cap() + self.get_net_debt()

    def get_ebitda(self):
        income_statement = self.get_latest_income_statement()
        return income_statement['EBITDA']
    
    def get_ebit(self):
        income_statement = self.get_latest_income_statement()
        return income_statement['EBIT']
    
    def get_net_income(self):
        income_statement = self.get_latest_income_statement()
        return income_statement['NetIncomeCommonStockholders']
    
    def get_net_income_all(self):
        income_statement = self.get_latest_income_statement()
        return income_statement['NetIncome']
    
    ### Ratios ###
    def get_ev_ebitda(self):
        return self.get_enterprise_value() / self.get_ebitda()

    def get_price_earnings(self):
        return self.get_market_cap() / self.get_net_income()

    def get_pe_ratio(self):
        return self.get_price_earnings()

    # Get attributes from company_dict
    def __getattr__(self, name):
        company_info =  object.__getattribute__(self, "company_info")
        try:
            return company_info[name]
        # Try updating the KAP data
        except KeyError:
            company_info = self.update_info()
        try:
            return company_info[name]
        # Try updating the Yahoo data
        except KeyError as e:
            company_info[name] = self.kap_website.get_yahoo_property(self.ticker, name)
            return company_info[name]
