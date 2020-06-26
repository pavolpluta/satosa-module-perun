import os

import pytest
import mock
from perun.micro_services.adapters.RpcAdapter import RpcAdapter


class TestRpcAdapter:
    TEST_CONF_FILE_NAME = '/tests/perun/micro_services/configurations/perun_config_test.yml'
    TEST_BADCONF_FILE_NAME = '/tests/perun/micro_services/configurations/perun_bad_config_test.yml'
    TEST_RPC_PERUN_ATTRS = [
        {
            'namespace': 'test',
            'friendlyName': 'urn:attr:1',
            'id': 1,
            'displayName': 'Test attribute 1',
            'type': 'java.lang.Boolean',
            'value': True
        },
        {
            'namespace': 'test',
            'friendlyName': 'urn:attr:2',
            'id': 2,
            'displayName': 'Test attribute 2',
            'type': 'java.lang.Integer',
            'value': 2
        },
        {
            'namespace': 'test',
            'friendlyName': 'urn:attr:3',
            'id': 3,
            'displayName': 'Test attribute 3',
            'type': 'java.lang.String',
            'value': 'Test value 3'
        },
        {
            'namespace': 'test',
            'friendlyName': 'urn:attr:4',
            'id': 4,
            'displayName': 'Test attribute 4',
            'type': 'java.util.ArrayList',
            'value': ['Test value 4', 'Test value 5', 'Test value 6']
        }

    ]

    def test_get_adapter(self):
        path = os.getcwd()
        perun_adapter = RpcAdapter(path + self.TEST_CONF_FILE_NAME)

        assert isinstance(perun_adapter, RpcAdapter)

    def test_init_bad_conf(self):
        path = os.getcwd()

        with pytest.raises(Exception):
            RpcAdapter(path + self.TEST_BADCONF_FILE_NAME)

    @mock.patch('perun.micro_services.adapters.RpcConnector')
    def test_get_attributes(self, mock_connector):
        mock_connector.get.return_value = self.TEST_RPC_PERUN_ATTRS

        path = os.getcwd()
        rpc_adapter = RpcAdapter(path + self.TEST_CONF_FILE_NAME)
        rpc_adapter.connector = mock_connector

        # RpcAdapter.__get_attributes() called within this function
        attr_names_map = rpc_adapter.get_user_attributes(1, ['internal_test_attribute_1', 'internal_test_attribute_2',
                                                             'internal_test_attribute_3', 'internal_test_attribute_4'])

        assert 'internal_test_attribute_1' in attr_names_map.keys()
        assert attr_names_map.get('internal_test_attribute_1').get('id') == 1
        assert attr_names_map.get('internal_test_attribute_1').get('name') == 'test:urn:attr:1'
        assert attr_names_map.get('internal_test_attribute_1').get('displayName') == 'Test attribute 1'
        assert attr_names_map.get('internal_test_attribute_1').get('type') == 'java.lang.Boolean'
        assert attr_names_map.get('internal_test_attribute_1').get('value') is True
