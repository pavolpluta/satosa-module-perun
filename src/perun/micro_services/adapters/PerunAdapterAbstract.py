"""
Abstract class PerunAdapterAbstract
"""
__author__ = "Pavel Vyskocil"
__email__ = "Pavel.Vyskocil@cesnet.cz"

from abc import ABC, abstractmethod


class PerunAdapterAbstract(ABC):

    LDAP = 'ldap'
    RPC = 'rpc'

    @staticmethod
    def get_instance(config_file_path, interface=RPC):
        if interface == PerunAdapterAbstract.LDAP:
            from perun.micro_services.adapters.LdapAdapter import LdapAdapter
            adapter = LdapAdapter(config_file_path)
        else:
            from perun.micro_services.adapters.RpcAdapter import RpcAdapter
            adapter = RpcAdapter(config_file_path)
        return adapter

    @abstractmethod
    def get_perun_user(self, idp_entity_id, uids):
        pass

    @abstractmethod
    def get_facility_by_identifier(self, identifier):
        pass

    @abstractmethod
    def get_user_groups_on_facility(self, user, facility_id):
        pass

    @abstractmethod
    def get_facility_capabilities(self, facility_id):
        pass

    @abstractmethod
    def get_resource_capabilities(self, facility_id, groups):
        pass

    @abstractmethod
    def get_user_attributes_values(self, user_id, attributes):
        pass
