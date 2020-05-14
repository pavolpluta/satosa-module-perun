"""
Satosa micro_service : Perun Entitlement
"""

__author__ = "Pavel Vyskocil"
__email__ = "Pavel.Vyskocil@cesnet.cz"

import logging
import urllib
from typing import List

from perun.micro_services.adapters.PerunAdapterAbstract import PerunAdapterAbstract
from perun.micro_services.models.Facility import Facility
from perun.micro_services.models.Group import Group

from satosa.micro_services.base import ResponseMicroService


logger = logging.getLogger(__name__)


class PerunEntitlement(ResponseMicroService):
    INTERFACE = 'interface'
    PREFIX = 'prefix'
    SUFFIX = 'suffix'
    PERUN_CONFIG_FILE_NAME = 'perun_config_file_name'
    FORWARDED_ENTITLEMENT_PERUN_ATTR_NAME = 'forwarded_entitlement_perun_attr_name'

    def __init__(self, config, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.config = config

        interface = str.lower(config.get(self.INTERFACE))
        confif_file_name = config.get(self.PERUN_CONFIG_FILE_NAME, None)

        if confif_file_name is None:
            raise Exception(f'PerunEntitlement: Required option "{self.PERUN_CONFIG_FILE_NAME}" not defined.')

        self.adapter: PerunAdapterAbstract = PerunAdapterAbstract.get_instance(confif_file_name, interface)

        self.prefix = config.get(self.PREFIX, None)
        self.suffix = config.get(self.SUFFIX, None)

        if None in [self.prefix, self.suffix]:
            raise Exception(f'PerunEntitlement: One of required options: {[self.prefix, self.suffix]} is "None".')

        self.forwarded_entitlement_attr_name = config.get(self.FORWARDED_ENTITLEMENT_PERUN_ATTR_NAME, None)

    def process(self, context, data):

        sp_entity_id = data.requester
        user_id = data.attributes.get('perun_id', None)

        if isinstance(user_id, List):
            user_id = user_id[0]

        if user_id is None:
            logger.debug(
                f'PerunEntitlement: Perun userId is not defined in data. => '
                f'EduPersonEntitlement cannot be loaded.'
            )
            return super().process(context, data)

        facility = self.adapter.get_facility_by_identifier(sp_entity_id)

        if facility is None:
            logger.debug(
                f'PerunEntitlement: Facility with entityId: {sp_entity_id} wasn\'t found. => '
                f'EduPersonEntitlement cannot be loaded.'
            )
            return super().process(context, data)

        groups = self.adapter.get_user_groups_on_facility(user_id, facility.id)

        group_names = set()

        for group in groups:
            group_name = group.unique_name
            if group.name == 'members':
                group_name = group.unique_name.split(':')[0]

            group_names.add(self.__groupname_wrapper(group_name))

        capabilities = self.__get_capabilities(facility, groups)

        entitlements = capabilities.union(group_names)

        if self.forwarded_entitlement_attr_name is not None:
            forwarded_entitlements = self.__get_forwarded_entitlements(user_id)
            entitlements = entitlements.union(forwarded_entitlements)

        data.attributes.update({'edupersonentitlement': list(entitlements)})

        return super().process(context, data)

    def __get_forwarded_entitlements(self, user_id):
        """
        Get forwarded entitlements from other Identity providers stored in Perun system.
        """
        forwarded_entitlements = set()

        try:
            response = self.adapter.get_user_attributes_values(user_id, [self.forwarded_entitlement_attr_name])
            forwarded_entitlements = response.get(self.forwarded_entitlement_attr_name, set())
        except Exception:
            logger.error('Exception during get forwarded entitlements')

        return forwarded_entitlements

    def __get_capabilities(self, facility: Facility, groups: List[Group]):
        """
        Get capabilities

        :param facility: Facility object
        :param groups: List of Groups
        :return: returns List of strings
        """
        resource_capabilities = set()
        facility_capabilities = set()

        try:
            resource_capabilities = self.adapter.get_resource_capabilities(facility.id, groups)
            facility_capabilities = self.adapter.get_facility_capabilities(facility.id)
        except Exception:
            logger.error('Exception during get Capability')

        capabilities = set()
        for capability in (resource_capabilities.union(facility_capabilities)):
            capabilities.add(self.__capabilities_wrapper(capability))

        return capabilities

    def __capabilities_wrapper(self, name):
        """
        Wrap name with the prefix and suffix to the correct form.

        :param name: The capability string
        :return: Returns string
        """
        return f'{self.prefix}:{urllib.parse.quote(name, safe=":/")}#{self.suffix}'

    def __groupname_wrapper(self, name):
        """
        Wrap name with the prefix and suffix to the correct form.

        :param name: The capability string
        :return: Returns string
        """
        return f'{self.prefix}:group:{urllib.parse.quote(name, safe=":/")}#{self.suffix}'
