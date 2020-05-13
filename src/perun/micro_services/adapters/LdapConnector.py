"""
Ldap Connector
"""
__author__ = "Pavel Vyskocil"
__email__ = "Pavel.Vyskocil@cesnet.cz"

import json
import time
import logging

from ldap3 import Server, Connection, ServerPool, FIRST

logger = logging.getLogger(__name__)


class LdapConnector:

    def __init__(self, hostnames, user, password):
        self.hostnames = hostnames
        self.user = user
        self.password = password

    def search_for_entity(self, base, filter, attributes=None):

        entries = self.search(base, filter, attributes)

        if len(entries) == 0:
            logger.error('LdapConnector.search_for_entity - No entity found. Returning \'None\'.')
            return None

        if len(entries) > 1:
            raise Exception('LdapConnector.search_for_entity - More than one entity found.')

        return entries[0]

    def search_for_entities(self, base, filter, attributes=None):
        entries = self.search(base, filter, attributes)

        if len(entries) == 0:
            logger.error('LdapConnector.search_for_entity - No entity found. Returning \'None\'.')
            return None

        return entries

    def search(self, base, filter, attributes=None):
        if attributes is None:
            attributes = []

        server_pool = ServerPool(None, FIRST)

        for hostname in self.hostnames:
            server = Server(hostname)
            server_pool.add(server)

        conn = Connection(server_pool, user=self.user, password=self.password)
        conn.open()

        if conn.bind() is False:
            raise Exception(f'Unable to bind user to the Perun LDAP {repr(server_pool.get_current_server(conn))}.')

        start_time = time.time()
        conn.search(base, filter, attributes=attributes)
        end_time = time.time()

        response = self.get_simplefied_entries(conn.entries)
        response_time = round((end_time - start_time) * 1000)
        logger.debug(
            f'LdapConnector.search - search query proceeded in {response_time} ms. '
            f'Query base: {base}, filter: {filter}, response: {response}.'
        )
        conn.unbind()
        return response

    @staticmethod
    def get_simplefied_entries(entries):
        data = []
        for entry in entries:
            entry_dict = json.loads(entry.entry_to_json())['attributes']
            x = {}
            for key in entry_dict.keys():
                x.update({key: entry_dict[key]})

            data.append(x)
        return data
