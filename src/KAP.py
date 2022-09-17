import requests as r
import json
from pathlib import Path
from bs4 import BeautifulSoup

class KAP():

    def __init__(self) -> None:
        pass
    
    def get_company_list(self):
        # Get the site
        constants_path = Path(__file__).parents[1] / 'Data' / 'Constants.json'
        with open(constants_path, 'r') as f:
            constants = json.load(f)
        company_list_site = constants['sites']['company_list']
        
        # Fetch the data from the site
        raw_response = r.get(company_list_site)
        # Check the status code
        raw_response.raise_for_status()
        response = BeautifulSoup(raw_response.text, 'html.parser')
        resp_filter = response.find_all('div', 'w-clearfix w-inline-block comp-row')

        return resp_filter[0]
    
