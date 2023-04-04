from .KAP import KAP
import yfinance as yf
import numpy as np


class Company():

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker.upper()

        # Initialize the info for the KAP website
        self.kap_website = KAP()
        self.company_info = self.update_info(online=False)

    def update_info(self, online=True):
        # Update the info on the KAP database
        self.kap_website.update_companies(online=online)
        self.kap_website.add_mkk_id(ticker=self.ticker)
        company_info = self.kap_website.get_company(self.ticker)

        # Return the company info
        return company_info
    
    def get_price(self):
        return self.kap_website.get_price(self.ticker)
        return self.kap_website.get_stats(self.ticker)
    
    def get_balance_sheet(self):
        return self.kap_website.get_balance_sheet(self.ticker)
    
    def get_latest_balance_sheet(self):
        return self.get_balance_sheet().iloc[-1,:]
    
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
        return self.get_latest_balance_sheet()['NetDebt']

    def get_enterprise_value(self):
        return self.get_market_cap() + self.get_net_debt()

    def get_ebitda(self):
        income_statement = self.get_latest_income_statement()
        ebitda = income_statement['EBITDA']
        return ebitda
    
    def get_ev_ebitda(self):
        return self.get_enterprise_value() / self.get_ebitda()

    @staticmethod
    def __value_to_float(x):
        if type(x) == float or type(x) == int:
            return x
        if 'K' in x:
            if len(x) > 1:
                return float(x.replace('K', '')) * 1e3
            return 1e3
        if 'M' in x:
            if len(x) > 1:
                return float(x.replace('M', '')) * 1e6
            return 1e6
        if 'B' in x:
            if len(x) > 1:
                return float(x.replace('B', '')) * 1e9
            return 1e9
        return float(x)
        
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
