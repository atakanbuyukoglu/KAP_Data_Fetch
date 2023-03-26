from .RequestWrapper import Request
import json
from pathlib import Path
from bs4 import BeautifulSoup
import re
import yfinance as yf
import numpy as np
import time

class KAP():

    def __init__(self) -> None:
        self.constants_path = Path(__file__).parents[1] / 'Config' / 'Constants.json'
        # Load the constants
        with open(self.constants_path, 'r') as f:
            self.constants = json.load(f)
        self.data_path = Path(__file__).parents[1] / 'Data'
        self.companies = None

        self.query_suffix = '.IS'

        # Initialize Request wrapper with sleep time
        self.r = Request(sleep_time=self.constants['sleep_times']['kap'])
        self.r_yahoo = Request(sleep_time=self.constants['sleep_times']['yahoo'])

    def __get_company_list_html(self):

        # Load the constants
        with open(self.constants_path, 'r') as f:
            constants = json.load(f)
        
        # Get the site
        company_list_site = constants['sites']['company_list']
        
        # Fetch the data from the site
        raw_response = self.r.get(company_list_site)
        # Check the status code
        raw_response.raise_for_status()

        # String for compatibility with offline version
        raw_response = raw_response.text

        # Save the HTML results to a log file
        with open(self.data_path / 'Company_List.html', 'w', encoding='utf-8') as f:
            f.write(raw_response)
    
        return raw_response

    def __raw_html_to_html_list(self, raw_html):
        soup = BeautifulSoup(raw_html, 'html.parser')
        html_list = soup.find_all('div', 'w-clearfix w-inline-block comp-row')

        return html_list

    def __html_list_to_company_dict(self, html_list, save_results=True):
        # Load the constants
        with open(self.constants_path, 'r') as f:
            constants = json.load(f)

        company_dict = {}
        for company in html_list:
            ticker_dict = {}

            ticker = company.select('div.comp-cell._04.vtable a.vcell')[0].text
            ticker_dict['ticker'] = ticker
            name = company.select('div.comp-cell._14.vtable a.vcell')[0].text
            ticker_dict['name'] = name
            link = company.select('div.comp-cell._04.vtable a.vcell[href]')[0]['href']
            ticker_dict['link'] = constants['sites']['main_site'] + link
            auditor = company.select('div.comp-cell._11.vtable a.vcell')[0].text
            ticker_dict['auditor'] = auditor
            city = company.select('div.comp-cell._12.vtable div.vcell')[0].text
            ticker_dict['city'] = city
            kap_id = int(re.search(r'\d+', link).group())
            ticker_dict['kap_id'] = kap_id

            company_dict[ticker] = ticker_dict
        
        if save_results:
            self.save_companies(company_dict)

        return company_dict

    def save_companies(self, company_dict):
        with open(self.data_path / 'Companies.json', 'w', encoding='utf-8') as f:
            json.dump(company_dict, f, ensure_ascii=False, indent=2)
    
    def update_companies(self, online=True):
        return self.get_companies(online=online)

    def add_mkk_id(self, ticker:str):
        companies = self.get_companies()
        # Try accessing the ticker
        try:
            company_info = companies[ticker]
        except KeyError as e:
            print("Ticker", ticker, "could not be found in the companies list.")
            print("Try updating the list or checking your ticker input.")
            raise e
        # Try returning the MKK ID if it already exists
        try:
            return company_info['mkk_id']
        # Get the MKK ID from the KAP website instead
        except KeyError:            
            resp = self.r.get(url=company_info['link'])
            soup = BeautifulSoup(resp.text, 'html.parser')
            mkk_id = soup.select('img.comp-logo')[0]['src'].split('/')[-1]
            company_info['mkk_id'] = mkk_id
            self.save_companies(companies)

    def get_price(self, ticker:str):
        query_ticker = ticker + '.' + 'IS'
        yahoo_scraper = yf.Ticker(query_ticker, session=self.r_yahoo)
        info = yahoo_scraper.fast_info
        print(dict(info))
        return np.round(info['lastPrice'], decimals=2)

    def get_companies(self, online=False, save_results=True):

        if online:
            # Get the raw HTML response from KAP
            raw_response = self.__get_company_list_html()

            # Filter the results to companies
            html_list = self.__raw_html_to_html_list(raw_response)
            
            # Convert the results to a dictionary
            company_dict = self.__html_list_to_company_dict(html_list, save_results=save_results)
        else:
            # Get it from the saved varible if possible
            if self.companies is not None:
                return self.companies
            # Try loading them from the saved file
            try:
                with open(self.data_path / 'Companies.json', 'r', encoding='utf-8') as f:
                    company_dict = json.load(f)
            # If the file is not there, obtain it online
            except FileNotFoundError:
                return self.get_companies(online=True, save_results=save_results)
        
        self.companies = company_dict
        return company_dict
    
    # TODO: Find a way to add Yahoo Finance data without affecting offline data loading
    def __add_yahoo_data(self):
        pass
