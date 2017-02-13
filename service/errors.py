from service.headers import Headers
from service.utils import HTTP_STATUSES


class HttpError(Exception):
    def __init__(self, code, headers=None):
        self.code = code
        self.headers = headers

    def __str__(self):
        return HTTP_STATUSES[self.code]
