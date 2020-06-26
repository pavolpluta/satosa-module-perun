import os
from unittest import mock

import pytest
from perun.micro_services.models.Facility import Facility
from perun.micro_services.models.Group import Group
from perun.micro_services.perun_entitlement import PerunEntitlement
from satosa.internal import AuthenticationInformation, InternalData
from tests.perun.micro_services.adapters.test_PerunAdapter import TestPerunAdapter


class TestPerunEntitlement:
    PREFIX = 'urn.example.com'
    SUFFIX = 'perun.example.com'
    FORWARDED_ENTITLEMENT_ATTR_NAME = 'forwarded_entitlement_attr_name'

    GROUP_NAME1 = 'vo_name:members'
    GROUP_NAME2 = 'vo_name:Test group!_name.'
    GROUP_NAME1_WRAPPED = f'{PREFIX}:group:vo_name#{SUFFIX}'
    GROUP_NAME2_WRAPPED = f'{PREFIX}:group:vo_name:Test%20group%21_name.#{SUFFIX}'

    CAPABILITY1 = 'res:CAPABILITY'
    CAPABILITY2 = 'res:Capability Test:role:ADMIN'
    CAPABILITY1_WRAPPED = f'{PREFIX}:{CAPABILITY1}#{SUFFIX}'
    CAPABILITY2_WRAPPED = f'{PREFIX}:res:Capability%20Test:role:ADMIN#{SUFFIX}'

    WRAPPED_GROUP_NAMES = {GROUP_NAME1_WRAPPED, GROUP_NAME2_WRAPPED}
    WRAPPED_CAPABILITIES = {CAPABILITY1_WRAPPED, CAPABILITY2_WRAPPED}
    FORWARDED_ENTITLEMENTS = {'urn:forwarded:vo:group#example.com', 'urn:forwarded:vo#example.com'}
    FORWARDED_ENTITLEMENTS_DICT = {FORWARDED_ENTITLEMENT_ATTR_NAME: FORWARDED_ENTITLEMENTS}
    ENTITLEMENTS = set().union(WRAPPED_GROUP_NAMES).union(WRAPPED_CAPABILITIES).union(FORWARDED_ENTITLEMENTS)

    test_facility = Facility(1, 'name', 'description', 'identifier')
    test_group1 = Group(1, 1, 'members', 'group_description', GROUP_NAME1)
    test_group2 = Group(2, 1, 'Test group name', 'group_description2', GROUP_NAME2)
    user_groups = {test_group1, test_group2}
    path = os.getcwd()

    @staticmethod
    def create_perun_entitlement_service(conf=None):
        config = dict(
            interface='rpc',
            perun_config_file_name=TestPerunEntitlement.path + TestPerunAdapter.TEST_CONF_FILE_NAME,
            prefix=TestPerunEntitlement.PREFIX,
            suffix=TestPerunEntitlement.SUFFIX,
            forwarded_entitlement_perun_attr_name=TestPerunEntitlement.FORWARDED_ENTITLEMENT_ATTR_NAME
        )
        configuration = config
        if conf is not None:
            configuration = conf
        service = PerunEntitlement(config=configuration, name="test_service", base_url="https://satosa.example.com")
        service.next = lambda ctx, data: data

        return service

    def test_missing_conf(self):
        config = dict(
            interface="ldap",
        )
        with pytest.raises(Exception):
            PerunEntitlement(config=config, name="test_service", base_url="https://satosa.example.com")

    def test_missing_required_option(self):
        path = os.getcwd()
        config = dict(
            interface='ldap',
            perun_config_file_name=path + TestPerunAdapter.TEST_CONF_FILE_NAME,
        )
        with pytest.raises(Exception):
            PerunEntitlement(config=config, name="test_service", base_url="https://satosa.example.com")

    def test_init_class(self):
        service = self.create_perun_entitlement_service()
        isinstance(service, PerunEntitlement)

    def test_none_user(self):
        service = self.create_perun_entitlement_service()
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name']
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' not in returned_service.attributes.keys()

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_none_facility(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = None
        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' not in returned_service.attributes.keys()

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_none_user_groups(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = set()
        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        assert not returned_service.attributes.get('edupersonentitlement')

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_only_user_groups(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = self.user_groups
        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        edupersonentitlement = returned_service.attributes.get('edupersonentitlement')
        assert len(edupersonentitlement) == 2
        assert set(edupersonentitlement).issubset(self.WRAPPED_GROUP_NAMES)

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_resource_capabilities(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = self.user_groups
        mock_adapter.get_resource_capabilities.return_value = {self.CAPABILITY1}
        mock_adapter.get_facility_capabilities.return_value = set()

        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }
        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        edupersonentitlement = returned_service.attributes.get('edupersonentitlement')
        assert len(edupersonentitlement) == 3
        expected_result = self.WRAPPED_GROUP_NAMES.copy()
        expected_result.add(self.CAPABILITY1_WRAPPED)
        assert set(edupersonentitlement).issubset(expected_result)

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_resource_capabilities_raise_exception(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = self.user_groups
        mock_adapter.get_resource_capabilities.side_effect = Exception('Exception')
        mock_adapter.get_facility_capabilities.return_value = set()

        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }
        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        edupersonentitlement = returned_service.attributes.get('edupersonentitlement')
        assert len(edupersonentitlement) == 2
        assert set(edupersonentitlement).issubset(self.WRAPPED_GROUP_NAMES)

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_facility_capabilities(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = self.user_groups
        mock_adapter.get_resource_capabilities.return_value = set()
        mock_adapter.get_facility_capabilities.return_value = {self.CAPABILITY1}
        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        edupersonentitlement = returned_service.attributes.get('edupersonentitlement')
        assert len(edupersonentitlement) == 3
        assert set(edupersonentitlement).issubset(
            {self.GROUP_NAME1_WRAPPED, self.GROUP_NAME2_WRAPPED, self.CAPABILITY1_WRAPPED}
        )

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_facility_capabilities_raise_exception(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = self.user_groups
        mock_adapter.get_resource_capabilities.return_value = set()
        mock_adapter.get_facility_capabilities.side_effect = Exception('Exception')
        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        edupersonentitlement = returned_service.attributes.get('edupersonentitlement')
        assert len(edupersonentitlement) == 2
        assert set(edupersonentitlement).issubset(self.WRAPPED_GROUP_NAMES)

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_get_capabilities(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = self.user_groups
        mock_adapter.get_resource_capabilities.return_value = {self.CAPABILITY1}
        mock_adapter.get_facility_capabilities.return_value = {self.CAPABILITY2}
        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        edupersonentitlement = returned_service.attributes.get('edupersonentitlement')
        assert len(edupersonentitlement) == 4
        assert set(edupersonentitlement).issubset(
            set().union(self.WRAPPED_GROUP_NAMES).union(self.WRAPPED_CAPABILITIES)
        )

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_get_forwarded_entitlements(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = set()
        mock_adapter.get_resource_capabilities.return_value = set()
        mock_adapter.get_facility_capabilities.return_value = set()
        mock_adapter.get_user_attributes.return_value = self.FORWARDED_ENTITLEMENTS_DICT

        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        edupersonentitlement = returned_service.attributes.get('edupersonentitlement')
        assert len(edupersonentitlement) == 2
        assert set(edupersonentitlement).issubset(self.FORWARDED_ENTITLEMENTS)

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_get_forwarded_entitlements_raise_exception(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = set()
        mock_adapter.get_resource_capabilities.return_value = set()
        mock_adapter.get_facility_capabilities.return_value = set()
        mock_adapter.get_user_attributes.side_effect = Exception('Exception')

        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        assert not returned_service.attributes.get('edupersonentitlement')

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_get_forwarded_entitlements_no_defined_attr(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = set()
        mock_adapter.get_resource_capabilities.return_value = set()
        mock_adapter.get_facility_capabilities.return_value = set()
        mock_adapter.get_user_attributes.return_value = self.FORWARDED_ENTITLEMENTS_DICT

        config = dict(
            interface='rpc',
            perun_config_file_name=self.path + TestPerunAdapter.TEST_CONF_FILE_NAME,
            prefix=TestPerunEntitlement.PREFIX,
            suffix=TestPerunEntitlement.SUFFIX,
        )
        service = self.create_perun_entitlement_service(config)
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        assert not returned_service.attributes.get('edupersonentitlement')

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_get_entitlements(self, mock_adapter):
        mock_adapter.get_facility_by_identifier.return_value = self.test_facility
        mock_adapter.get_user_groups_on_facility.return_value = self.user_groups
        mock_adapter.get_resource_capabilities.return_value = {self.CAPABILITY1}
        mock_adapter.get_facility_capabilities.return_value = {self.CAPABILITY2}
        mock_adapter.get_user_attributes.return_value = self.FORWARDED_ENTITLEMENTS_DICT
        service = self.create_perun_entitlement_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = {
            'displayname': ['Display Name'],
            'perun_id': [1]
        }

        returned_service = service.process(None, resp)
        assert 'edupersonentitlement' in returned_service.attributes.keys()
        edupersonentitlement = returned_service.attributes.get('edupersonentitlement')
        assert len(edupersonentitlement) == 6
        assert set(edupersonentitlement).issubset(self.ENTITLEMENTS)
