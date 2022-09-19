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
        constants_path = Path(__file__).parents[1] / 'Data' / 'Constants.json'

        # Check if the data is available
        if not online:
            data_available = resp_html_path.is_file()
            data_available = data_available and os.path.getsize(resp_html_path) > 0
            if data_available:
                with open(resp_html_path, 'r') as f:
                    html_data = f.read()
                    return html_data

        # Get the site
        with open(constants_path, 'r') as f:
            constants = json.load(f)
        company_list_site = constants['sites']['company_list']
        
        # Fetch the data from the site
        raw_response = r.get(company_list_site)
        # Check the status code
        raw_response.raise_for_status()

        # Filter the results
        response = BeautifulSoup(raw_response.text, 'html.parser')
        resp_filter = response.find_all('div', 'w-clearfix w-inline-block comp-row')

        # Save the HTML results to a log file
        with open(resp_html_path, 'w+', encoding='utf-8') as f:
            for company in resp_filter:
                f.write(str(company) + '\n\n')
        with open(resp_html_path, 'r', encoding='utf-8') as f:
            return f.read()
    
