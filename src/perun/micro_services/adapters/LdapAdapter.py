"""
PerunAdapter for connection via LDAP
"""
__author__ = "Pavel Vyskocil"
__email__ = "Pavel.Vyskocil@cesnet.cz"

import logging

import yaml
from perun.micro_services.adapters.LdapConnector import LdapConnector
from perun.micro_services.adapters.PerunAdapterAbstract import PerunAdapterAbstract

logger = logging.getLogger(__name__)


class LdapAdapter(PerunAdapterAbstract):

    PERUN_LDAP_HOSTNAMES = 'ldap.hostnames'
    PERUN_LDAP_BASE = 'ldap.base'
    PERUN_LDAP_USER = 'ldap.user'
    PERUN_LDAP_PASSWORD = 'ldap.password'

    def __init__(self, config_file):

        with open(config_file, "r") as f:
            perun_configuration = yaml.safe_load(f)
            hostnames = perun_configuration.get(self.PERUN_LDAP_HOSTNAMES, None)
            user = perun_configuration.get(self.PERUN_LDAP_USER, None)
            pasword = perun_configuration.get(self.PERUN_LDAP_PASSWORD, None)
            self.base = perun_configuration.get(self.PERUN_LDAP_BASE, None)

        if None in [hostnames, user, pasword, self.base]:
            raise Exception('One of required attributes is not defined!')

        self.connector = LdapConnector(hostnames, user, pasword)
