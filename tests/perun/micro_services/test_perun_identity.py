import os

import mock
import pytest
from perun.micro_services.models.User import User
from perun.micro_services.perun_identity import PerunIdentity
from satosa.internal import InternalData, AuthenticationInformation

from tests.perun.micro_services.adapters.test_PerunAdapter import TestPerunAdapter


class TestPerunIdentity:

    ATTRIBUTES = {
            'edupersonuniqueid': ['uniqueid@example.com'],
            'edupersonprincipalname': ['principalname@example.com'],
            'displayname': ['Display Name']
        }

    @staticmethod
    def create_perun_identity_service():
        path = os.getcwd()
        config = dict(
            interface='ldap',
            perun_config_file_name=path + TestPerunAdapter.TEST_CONF_FILE_NAME,
            uids_identifiers=['edupersonuniqueid', 'edupersonprincipalname']
        )
        service = PerunIdentity(config=config, name='test_service', base_url='https://satosa.example.com')
        service.next = lambda ctx, data: data

        return service

    def test_missing_conf(self):
        config = dict(
            interface='ldap',
            uids_identifiers=['edupersonuniqueid', 'edupersonprincipalname']
        )
        with pytest.raises(Exception):
            PerunIdentity(config=config, name='test_service', base_url='https://satosa.example.com')

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_perun_identity_none_user(self, mock_adapter):
        mock_adapter.get_perun_user.return_value = None
        service = self.create_perun_identity_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = self.ATTRIBUTES

        returned_service = service.process(None, resp)
        assert 'perun_id' not in returned_service.attributes.keys()

    @mock.patch('perun.micro_services.adapters.RpcAdapter')
    def test_perun_identity_test_user(self, mock_adapter):
        user = User(1, 'Test user')
        mock_adapter.get_perun_user.return_value = user
        service = self.create_perun_identity_service()
        service.adapter = mock_adapter
        resp = InternalData(auth_info=AuthenticationInformation())
        resp.attributes = self.ATTRIBUTES

        returned_service = service.process(None, resp)
        assert 'perun_id' in returned_service.attributes.keys()
        assert returned_service.attributes.get('perun_id') == [user.id]
