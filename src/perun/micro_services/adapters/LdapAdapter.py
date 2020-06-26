"""
PerunAdapter for connection via LDAP
"""
__author__ = "Pavel Vyskocil"
__email__ = "Pavel.Vyskocil@cesnet.cz"

import logging
from pprint import pprint

import yaml
from perun.micro_services.adapters.LdapConnector import LdapConnector
from perun.micro_services.adapters.RpcAdapter import RpcAdapter
from perun.micro_services.adapters.PerunAdapterAbstract import PerunAdapterAbstract
from perun.micro_services.models.Facility import Facility
from perun.micro_services.models.Group import Group
from perun.micro_services.models.User import User
from perun.micro_services.utils.attribute_utils import AttributeUtils

logger = logging.getLogger(__name__)


class LdapAdapter(PerunAdapterAbstract):
    PERUN_LDAP_HOSTNAMES = 'ldap.hostnames'
    PERUN_LDAP_BASE = 'ldap.base'
    PERUN_LDAP_USER = 'ldap.user'
    PERUN_LDAP_PASSWORD = 'ldap.password'

    PERUN_ATTR_MAP_FILE = 'perun_attr_map_file'

    INTERNAL_ATTR_NAME = 'internalAttrName'

    def __init__(self, config_file):

        with open(config_file, "r") as f:
            perun_configuration = yaml.safe_load(f)
            hostnames = perun_configuration.get(self.PERUN_LDAP_HOSTNAMES, None)
            user = perun_configuration.get(self.PERUN_LDAP_USER, None)
            pasword = perun_configuration.get(self.PERUN_LDAP_PASSWORD, None)
            self.base = perun_configuration.get(self.PERUN_LDAP_BASE, None)

            self.attr_utils_file_name = perun_configuration.get(self.PERUN_ATTR_MAP_FILE)
            self.attribute_utils = AttributeUtils(self.attr_utils_file_name)

        if None in [hostnames, user, pasword, self.base]:
            raise Exception('One of required attributes is not defined!')

        self.connector = LdapConnector(hostnames, user, pasword)
        self.fallback_adapter = RpcAdapter(config_file)

    def get_perun_user(self, idp_entity_id, uids):

        ldap_query = ''
        for uid in uids:
            ldap_query += '(eduPersonPrincipalNames=' + uid + ')'

        if not ldap_query.strip():
            return None

        response = self.connector.search_for_entity('ou=People,' + self.base,
                                                    '(|' + ldap_query + ')',
                                                    ['perunUserId', 'displayName', 'cn']
                                                    )

        if response is None:
            return None

        if response['displayName'][0].strip():
            name = response['displayName'][0]
        elif response['cn'][0].strip():
            name = response['cn'][0]
        else:
            name = None

        return User(response['perunUserId'][0], name)

    def get_facility_by_identifier(self, identifier):
        filter = f'(&(objectClass=perunFacility)(|(entityID={identifier})(OIDCClientID={identifier})))'
        response = self.connector.search_for_entity(self.base,
                                                    filter,
                                                    ['perunFacilityId', 'cn', 'description']
                                                    )

        if response is None:
            return None

        return Facility(response['perunFacilityId'][0], response['cn'][0], response['description'][0], identifier)

    def get_user_groups_on_facility(self, user_id, facility_id):
        resources = self.connector. \
            search_for_entities(
            self.base,
            f'(&(objectClass=perunResource)(perunFacilityDn=perunFacilityId={facility_id}, {self.base}))',
            ['perunResourceId']
        )

        if resources is None:
            return []

        resources_string = '(|'
        for resource in resources:
            resources_string += '(assignedToResourceId=' + resource['perunResourceId'][0] + ')'

        resources_string += ')'

        groups_result = self.connector. \
            search_for_entities(
            self.base,
            '(&(uniqueMember=perunUserId=' + user_id + ', ou=People,' + self.base + ')' + resources_string + ')',
            ['perunGroupId', 'cn', 'perunUniqueGroupName', 'perunVoId', 'description']
        )

        if groups_result is None:
            groups_result = []

        groups = []

        for result in groups_result:
            description = ''
            if result['description']:
                description = result['description'][0]

            groups.append(
                Group(
                    result['perunGroupId'][0],
                    result['perunVoId'][0],
                    result['cn'][0],
                    description,
                    result['perunUniqueGroupName'][0]
                )
            )

        return groups

    def get_resource_capabilities(self, facility_id, groups):

        resource_capabilities = set()

        if not groups or facility_id is None:
            return resource_capabilities

        resources = self.connector. \
            search_for_entities(
            self.base,
            f'(&(objectClass=perunResource)(perunFacilityDn=perunFacilityId={facility_id},{self.base}))',
            ['capabilities', 'assignedGroupId']
        )

        user_group_ids = []
        for group in groups:
            user_group_ids.append(group.id)

        if resources is None:
            return resource_capabilities

        for resource in resources:
            if 'capabilities' not in resource.keys() and 'assignedGroupId' not in resource.keys():
                continue
            for group_id in resource['assignedGroupId']:
                if group_id in user_group_ids:
                    for capability in resource['capabilities']:
                        resource_capabilities.add(capability)
                    break

        return resource_capabilities

    def get_facility_capabilities(self, facility_id):
        if facility_id is None:
            return set()

        response = self.connector.search_for_entity(
            self.base,
            f'(&(objectClass=perunFacility)(perunFacilityId={facility_id}))',
            ['capabilities']
        )

        if response is None:
            return set()

        return set(response['capabilities'])

    def get_user_attributes(self, user_id, attr_names=None):
        if attr_names is None:
            return dict()

        ldap_response = self.connector.search_for_entity(
            f'perunUserId={user_id},ou=People,{self.base}',
            '(objectClass=perunUser)',
            attr_names
        )

        return ldap_response

    def get_user_attributes_values(self, user_id, attributes):
        attr_type_map = self.attribute_utils.create_ldap_attr_name_type_map(attributes)

        perun_attrs = self.connector.search_for_entities(
            self.base,
            f'(&(objectClass=perunUser)(perunUserId={user_id}))',
            attr_type_map.keys()
        )

        attributes_values = {}

        logger.debug("LDAP - ATTR_TYPE_MAP:")
        logger.debug(pprint(attr_type_map))

        logger.debug("LDAP - PERUN_ATTRS[0]:")
        logger.debug(pprint(perun_attrs[0]))

        logger.debug("LDAP - attr_names:")
        logger.debug(pprint(attr_type_map.keys()))

        for attr_name in attr_type_map.keys():
            attributes_values[attr_type_map[attr_name][self.INTERNAL_ATTR_NAME]] = \
                self.attribute_utils.set_internal_attr_value(attr_type_map, perun_attrs[0], attr_name)

        return attributes_values