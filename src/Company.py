from .KAP import KAP
import yfinance as yf


class Company():

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        self.kap_website = KAP()

        self.company_info = self.update_info()

        self.query_ticker = self.ticker + '.' + 'IS'
        self.yahoo_scraper = yf.Ticker(self.query_ticker)

    def update_info(self, online=False, mkk=False):
        company_dict = self.kap_website.get_company(ticker=self.ticker, online=online, mkk=mkk)
        return company_dict
    
    def get_price(self):
        return self.yahoo_scraper.fast_info['lastPrice']
        

    def __getattr__(self, name):
        company_info =  object.__getattribute__(self, "company_info")
        if name in company_info:
            return company_info[name]
        # Fails if the attribute is not found
        # Check for mkk_id
        if name == 'mkk_id':
            company_info = self.update_info(mkk=True)
            if name in company_info:
                return company_info[name]
        # Try one last online update if nothing works
        company_info = self.update_info(online=True)
        if name in company_info:
            return company_info[name]
        else:
            raise KeyError('Name', name, 'is not an attribute of the company', self.ticker)