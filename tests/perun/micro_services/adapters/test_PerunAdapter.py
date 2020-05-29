import os
import pytest

from perun.micro_services.adapters.LdapAdapter import LdapAdapter
from perun.micro_services.adapters.PerunAdapter import PerunAdapter
from perun.micro_services.adapters.PerunAdapterAbstract import PerunAdapterAbstract
from perun.micro_services.adapters.RpcAdapter import RpcAdapter


class TestPerunAdapter:

    TEST_CONF_FILE_NAME = '/tests/perun/micro_services/adapters/perun_config_test.yml'

    def test_get_instance_rpc(self):
        path = os.getcwd()
        perun_adapter = PerunAdapter.get_instance(path + self.TEST_CONF_FILE_NAME)

        assert isinstance(perun_adapter, RpcAdapter)

    def test_get_instance_ldap(self):
        path = os.getcwd()
        perun_adapter = PerunAdapter.get_instance(path + self.TEST_CONF_FILE_NAME, PerunAdapterAbstract.LDAP)

        assert isinstance(perun_adapter, LdapAdapter)

    def test_get_instance_no_conf_file(self):
        with pytest.raises(FileNotFoundError):
            PerunAdapter.get_instance('/testfile.yml', PerunAdapterAbstract.LDAP)
