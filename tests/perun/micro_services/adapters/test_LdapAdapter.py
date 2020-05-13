import os

import pytest
from perun.micro_services.adapters.LdapAdapter import LdapAdapter


class TestLdapAdapter:

    TEST_CONF_FILE_NAME = '/tests/perun/micro_services/adapters/perun_config_test.yml'
    TEST_BADCONF_FILE_NAME = '/tests/perun/micro_services/adapters/perun_bad_config_test.yml'

    def test_get_adapter(self):
        path = os.getcwd()
        perun_adapter = LdapAdapter(path + self.TEST_CONF_FILE_NAME)

        assert isinstance(perun_adapter, LdapAdapter)

    def test_init_bad_conf(self):
        path = os.getcwd()

        with pytest.raises(Exception):
            LdapAdapter(path + self.TEST_BADCONF_FILE_NAME)
