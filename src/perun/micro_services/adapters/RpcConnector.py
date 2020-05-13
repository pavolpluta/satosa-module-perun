"""
Provides interface to call Perun RPC.
Note that Perun RPC should be considered as unreliable
and authentication process should continue without connection to Perun. e.g. use LDAP instead.

"""
__author__ = "Pavel Vyskocil, Pavol Pluta"
__email__ = "vyskocilpavel@muni.cz, pavol.pluta1@gmail.com"

import json
import logging
import time
import urllib.parse
import re
import pycurl

from io import BytesIO

logger = logging.getLogger(__name__)


class RpcConnector:
    COOKIE_FILE = '/tmp/proxyidp_cookie.txt'
    CONNECT_TIMEOUT = 1
    TIMEOUT = 15

    def __init__(self, rpc_url, user, password):
        self.rpc_url = rpc_url
        self.user = user
        self.passwd = password

    def get(self, manager, method, params=None):
        if params is None:
            params = []

        params_query = urllib.parse.urlencode(params)
        params_query = re.sub(r'%5B\d+%5D', '%5B%5D', params_query)

        uri = f'{self.rpc_url}json/{manager}/{method}'

        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, f'{uri}?{params_query}')
        c.setopt(pycurl.USERPWD, f'{self.user}:{self.passwd}')
        c.setopt(pycurl.WRITEDATA, buffer)
        c.setopt(pycurl.COOKIEJAR, self.COOKIE_FILE)
        c.setopt(pycurl.COOKIEFILE, self.COOKIE_FILE)
        c.setopt(pycurl.CONNECTTIMEOUT, self.CONNECT_TIMEOUT)
        c.setopt(pycurl.TIMEOUT, self.TIMEOUT)

        start_time = self.__millitime()
        c.perform()
        end_time = self.__millitime()
        c.close()

        body = buffer.getvalue()
        result_json = body.decode('utf-8')
        result = json.loads(result_json)

        if 'errorId' in result.keys():
            raise Exception(f'Exception from Perun: {result["message"]}')

        response_time = round(end_time - start_time, 3)
        logger.debug(
            f'GET call {uri} with params: {params_query}, response: {result} in: {response_time} ms.'
        )

        return result

    def post(self, manager, method, params=None):
        if params is None:
            params = []

        params_json = json.dumps(params)
        uri = f'{self.rpc_url}json/{manager}/{method}'

        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, uri)
        c.setopt(pycurl.USERPWD, self.user + ':' + self.passwd)
        c.setopt(pycurl.CUSTOMREQUEST, 'POST')
        c.setopt(pycurl.POSTFIELDS, params_json)
        c.setopt(c.WRITEDATA, buffer)
        c.setopt(pycurl.HTTPHEADER, ['Content-Type:application/json', 'Content-Length: {}'.format(len(params_json))])
        c.setopt(pycurl.CONNECTTIMEOUT, self.CONNECT_TIMEOUT)
        c.setopt(pycurl.TIMEOUT, self.TIMEOUT)

        start_time = self.__millitime()
        c.perform()
        end_time = self.__millitime()
        c.close()

        body = buffer.getvalue()
        # Body is a byte string.
        # We have to know the encoding in order to print it to a text file
        # such as standard output.
        result_json = body.decode('utf-8')
        result = json.loads(result_json)

        if 'errorId' in result.keys():
            raise Exception(f'Exception from Perun: {result["message"]}')

        response_time = round(end_time - start_time, 3)
        logger.debug(
            f'POST call {uri} with params: {params_json}, response: {result} in: {response_time} ms.')

        return result

    @staticmethod
    def __millitime():
        return time.time_ns() // 1000000
