import os
import pytest

from perun.micro_services.adapters.LdapAdapter import LdapAdapter
from perun.micro_services.adapters.PerunAdapterAbstract import PerunAdapterAbstract
from perun.micro_services.adapters.RpcAdapter import RpcAdapter


class TestPerunAdapter:

    TEST_CONF_FILE_NAME = '/tests/perun/micro_services/configurations/perun_config_test.yml'
    TEST_MAP_FILE_LOCATION = 'tests/perun/micro_services/configurations/perun_test_attributes_map.yaml'

    def test_get_instance_rpc(self):
        path = os.getcwd()
        perun_adapter = PerunAdapterAbstract.get_instance(path + self.TEST_CONF_FILE_NAME)

        assert isinstance(perun_adapter, RpcAdapter)

    def test_get_instance_ldap(self):
        path = os.getcwd()
        perun_adapter = PerunAdapterAbstract.get_instance(path + self.TEST_CONF_FILE_NAME, PerunAdapterAbstract.LDAP)

        assert isinstance(perun_adapter, LdapAdapter)

    def test_get_instance_no_conf_file(self):
        with pytest.raises(FileNotFoundError):
            PerunAdapterAbstract.get_instance('/testfile.yml', PerunAdapterAbstract.LDAP)

    def test_get_attr_map_file(self):
        path = os.getcwd()
        perun_adapter = PerunAdapterAbstract.get_instance(path + self.TEST_CONF_FILE_NAME, PerunAdapterAbstract.LDAP)
        attr_map = perun_adapter.attr_utils_file_name

        assert attr_map == self.TEST_MAP_FILE_LOCATION

        perun_adapter = PerunAdapterAbstract.get_instance(path + self.TEST_CONF_FILE_NAME, PerunAdapterAbstract.RPC)
        attr_map = perun_adapter.attr_utils_file_name

        assert attr_map == self.TEST_MAP_FILE_LOCATION