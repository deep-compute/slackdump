"""
This module patches requests module to always make requests
using a default session so that the same socket connection
is re-used.
"""

import sys
import requests


class PatchedRequests(object):
    def __init__(self):
        self._session = requests.Session()

    def post(self, *args, **kwargs):
        return self._session.post(*args, **kwargs)


requests = sys.modules["requests"] = PatchedRequests()
