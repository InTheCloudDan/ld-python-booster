import launchdarkly_api
from time import time
from launchdarkly_api.rest import ApiException


class LDClient(launchdarkly_api.ApiClient):
    def __init__(self):
        super()

    def handle_rate_limit(self, api_call):
        api_call = api_call
        try:
            response, status, headers = api_call
        except ApiException as e:
            if e.status == 429:
                current = time.time() * 1000.0
                reset_rate = int(
                    (float(e.headers["X-RateLimit-Reset"]) - current + 1000.0) / 1000.0
                )
                time.sleep(reset_rate)
