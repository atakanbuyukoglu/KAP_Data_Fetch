from KAP import KAP

# TODO: Start with the company class
# TODO: Add fetcher for the MKK ID.

class Company():

    def __init__(self) -> None:
        self.mkk_id = None
        self.kap_website = KAP()

    # TODO: Get company info from KAP
    def update_info(self):
        pass

    def get_mkk_id(self):
        if self.mkk_id:
            return self.mkk_id
        self.update_info()
        return self.mkk_id