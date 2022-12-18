from .KAP import KAP

# TODO: Start with the company class
# TODO: Add fetcher for the MKK ID.

class Company():

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        self.kap_website = KAP()

        self.company_info = self.update_info()


    # TODO: Get company info from KAP
    def update_info(self, online=False):
        company_dict = self.kap_website.get_company(ticker=self.ticker, online=online)
        return company_dict

    def __getattr__(self, name):
        company_info =  object.__getattribute__(self, "company_info")
        if name in company_info:
            return company_info[name]
        else:
            # Fails if the attribute is not found
            # TODO: Add default value or throw KeyError
            company_info = self.update_info(online=True)
            return company_info[name]