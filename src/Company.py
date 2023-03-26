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
