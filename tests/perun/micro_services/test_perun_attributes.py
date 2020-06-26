import os

import mock
import pytest
from satosa.internal import InternalData, AuthenticationInformation

from perun.micro_services.perun_attributes import PerunAttributes
from tests.perun.micro_services.adapters.test_PerunAdapter import TestPerunAdapter


class TestPerunAttributes:
    path = os.getcwd()
    ATTR_MAP = {
                'perunUserAttribute_einfra': 'einfra_login',
                'perun_user_attribute-cn': ['cn', 'full_name'],
                'perunUserAttribute_groupNames': 'group_names',
                'perun_user_attribute-admin_key': 'admin_key',
                'perun_user_attribute_random_number': 'random_number'
            }

    ATTRS_FROM_CONNECTOR = {
        'perunUserAttribute_einfra': 'tester',
        'perunUserAttribute_groupNames': ['1','2','3'],
        'perun_user_attribute-admin_key': True,
        'perun_user_attribute-cn': 'Test User',
        'perun_user_attribute_random_number': 5
    }

    @staticmethod
    def create_perun_attributes_service():
        config = dict(
            interface='rpc',
            perun_config_file_name=TestPerunAttributes.path + TestPerunAdapter.TEST_CONF_FILE_NAME,
            uids_identifiers=['edupersonuniqueid','displayname'],
            mode='FULL',
            attr_map= TestPerunAttributes.ATTR_MAP
        )

        service = PerunAttributes(config=config, name='test_service', base_url="https://satosa.example.com")
        service.next = lambda ctx, data: data

        return service

    @pytest.fixture
    def service(self):
        return self.create_perun_attributes_service()

    def test_missing_conf(self):
        config = dict(
            interface="ldap",
        )
        with pytest.raises(Exception):
            PerunAttributes(config=config, name="test_service", base_url="https://satosa.example.com")

    def test_init_class(self, service):
        isinstance(service,PerunAttributes)

    def test_none_user(self, service):
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name']
        }

        returned_service = service.process(None, resp)
        assert 'perun_id' not in returned_service.attributes.keys()

    # Same structure returned from both rpc and ldap adapter, so it is sufficient
    # to mock just one of them
    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_rpc_full_mode(self, mock_adapter, service):
        mock_adapter.get_user_attributes_values.return_value = self.ATTRS_FROM_CONNECTOR
        service.adapter = mock_adapter

        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)

        assert returned_service.attributes.get('einfra_login') == ['tester']
        assert returned_service.attributes.get('group_names') == ['1', '2', '3']
        assert returned_service.attributes.get('admin_key') == [True]
        assert returned_service.attributes.get('cn') == ['Test User']
        assert returned_service.attributes.get('full_name') == ['Test User']
        assert returned_service.attributes.get('random_number') == [5]

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_rpc_partial_mode(self, mock_adapter, service):
        mock_adapter.get_user_attributes_values.return_value = {k:v for k,v in self.ATTRS_FROM_CONNECTOR.items() if k != 'perunUserAttribute_einfra'}
        service.adapter = mock_adapter
        service.mode = 'PARTIAL'

        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1],
            'einfra_login': ['another_tester'],
            'full_name': ['Another test user']
        }

        returned_service = service.process(None, resp)

        assert returned_service.attributes.get('einfra_login') == ['another_tester']
        assert returned_service.attributes.get('cn') == ['Test User']
        assert returned_service.attributes.get('full_name') == ['Another test user']

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_rpc_unsupported_type_exception(self, mock_adapter, service):
        mock_adapter.get_user_attributes_values.return_value = self.ATTRS_FROM_CONNECTOR
        service.adapter = mock_adapter
        service.attr_map = {
            'perunUserAttribute_einfra': 10
        }

        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        with pytest.raises(Exception):
            service.process(None, resp)