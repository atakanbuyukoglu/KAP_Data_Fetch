import requests as r
import time
from fake_useragent import UserAgent

class Request(r.Session):

    def __init__(self, sleep_time:float=5.0):
        super(Request, self).__init__()
        # Set the header to fake browser agent
        ua = UserAgent()
        self.headers = {'User-Agent':str(ua.chrome)}
        # Set the request time keeper
        self.sleep_time = sleep_time
        self.last_request = 0.0


    def get(self, url, **kwargs):
        # If the request is too new, sleep until enough time has passed
        rem_sleep_time = self.sleep_time - (time.time() - self.last_request)
        if rem_sleep_time > 0:
            time.sleep(rem_sleep_time)
        # Make the request
        result = super(Request, self).get(url, **kwargs)
        return result