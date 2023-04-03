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
        company_info = self.kap_website.get_companies()[self.ticker]

        # Return the company info
        return company_info
    
    def get_price(self):
        return self.kap_website.get_price(self.ticker)
    
    def get_stats(self):
        return self.kap_website.get_stats(self.ticker)
    
    def get_share_count(self):
        stats = self.get_stats()
        share_str = stats['Shares Outstanding 5']
        share_count = Company.__value_to_float(share_str)

        return share_count
    
    def get_market_cap(self):
        share_count = self.get_share_count()
        price = self.get_price()
        return share_count * price
    
    def get_enterprise_value(self):
        stats = self.get_stats()
        # Get approximate values from Yahoo for net debt
        market_cap_yahoo = Company.__value_to_float(stats['Market Cap (intraday)'])
        enterprise_value_yahoo = Company.__value_to_float(stats['Enterprise Value'])
        net_debt = enterprise_value_yahoo - market_cap_yahoo

        enterprise_value = self.get_market_cap() + net_debt
        return enterprise_value

    def get_ebitda(self):
        stats = self.get_stats()
        ebitda = Company.__value_to_float(stats['EBITDA'])
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
        except KeyError:
            company_info = self.update_info()
        try:
            return company_info[name]
        except KeyError as e:
            print('No attribute with', name, 'in company', company_info['ticker'], 'found.')
            raise e
