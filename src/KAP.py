import requests as r
import json
from pathlib import Path
from bs4 import BeautifulSoup
import os
import re

class KAP():

    def __init__(self) -> None:
        pass
    
    def get_company_list(self, online=False):
        
        resp_html_path = Path(__file__).parents[1] / 'Data' / 'Company_List.html'
        constants_path = Path(__file__).parents[1] / 'Config' / 'Constants.json'

        # Load the constants
        with open(constants_path, 'r') as f:
            constants = json.load(f)

        # Check if the data is available
        if not online:
            data_available = resp_html_path.is_file()
            data_available = data_available and os.path.getsize(resp_html_path) > 0
            if data_available:
                with open(resp_html_path, 'r') as f:
                    raw_response = f.read()
        else:
            # Get the site
            company_list_site = constants['sites']['company_list']
            
            # Fetch the data from the site
            raw_response = r.get(company_list_site)
            # Check the status code
            raw_response.raise_for_status()

            # String for compatibility with offline version
            raw_response = raw_response.text

            # Save the HTML results to a log file
            with open(resp_html_path, 'w+', encoding='utf-8') as f:
                f.write(raw_response)

        # Filter the results
        response = BeautifulSoup(raw_response, 'html.parser')
        resp_filter = response.find_all('div', 'w-clearfix w-inline-block comp-row')
        
        # Convert the results to a dictionary
        company_dict = {}
        for idx, company in enumerate(resp_filter):
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
            if idx==0:
                resp = r.get(url=ticker_dict['link'])
                soup = BeautifulSoup(resp.text, 'html.parser')
                mkk_id = soup.select('img.comp-logo')[0]['src'].split('/')[-1]
                ticker_dict['mkk_id'] = mkk_id

            company_dict[ticker] = ticker_dict

        # Save the temp results for testing
        temp_path = resp_html_path.parent / 'Dict_Sample.json'
        with open(temp_path, 'w+', encoding='utf-8') as f:
            json.dump(company_dict['AVOD'], f, ensure_ascii=False)
        temp_path = resp_html_path.parent / 'HTML_Sample.html'
        with open(temp_path, 'w+', encoding='utf-8') as f:
            f.write(str(resp_filter[0]))

        return type(company_dict['AVOD'])

        
