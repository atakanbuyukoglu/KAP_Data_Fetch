import requests as r
import json
from pathlib import Path
from bs4 import BeautifulSoup
import os

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
            link = company.select('div.comp-cell._04.vtable a.vcell[href]')[0]['href']
            
            ticker_dict['ticker'] = ticker
            ticker_dict['link'] = constants['sites']['main_site'] + link
            company_dict[ticker] = ticker_dict

        # Save the temp results for testing
        temp_path = resp_html_path.parent / 'Temp.html'
        with open(temp_path, 'w+', encoding='utf-8') as f:
            f.write(str(company_dict['AVOD']))

        return type(company_dict['AVOD'])

        
