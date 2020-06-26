"""
Satosa micro_service : Perun Attributes
"""

__author__ = "Pavol Pluta"
__email__ = "pavol.pluta1@gmail.com"

import logging
from collections.abc import Mapping, Iterable
from numbers import Number
from pprint import pprint
from typing import List

from satosa.micro_services.base import ResponseMicroService

from perun.micro_services.adapters.PerunAdapterAbstract import PerunAdapterAbstract

logger = logging.getLogger(__name__)


class PerunAttributes(ResponseMicroService):
    INTERFACE = 'interface'
    UIDS_IDENTIFIERS = 'uids_identifiers'
    PERUN_CONFIG_FILE_NAME = 'perun_config_file_name'
    MODE = 'mode'
    ATTR_MAP = 'attr_map'

    MODE_FULL = 'FULL'
    MODE_PARTIAL = 'PARTIAL'

    def __init__(self, config, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.config = config

        self.uids_identifiers = config.get(self.UIDS_IDENTIFIERS, [])
        config_file_name = config.get(self.PERUN_CONFIG_FILE_NAME, None)

        if config_file_name is None:
            raise Exception(f'PerunAttributes: Required option "{self.PERUN_CONFIG_FILE_NAME}" not defined.')

        interface = str.lower(config.get(self.INTERFACE))
        self.attr_map = config.get(self.ATTR_MAP)
        self.mode = config.get(self.MODE)
        if self.mode.upper() not in [self.MODE_FULL, self.MODE_PARTIAL]:
            self.mode = self.MODE_FULL

        self.adapter: PerunAdapterAbstract = PerunAdapterAbstract.get_instance(config_file_name, interface)

    def process(self, context, data):

        logger.debug('PerunAttributes:data START:')
        logger.debug(pprint(data))

        user_id = data.attributes.get('perun_id', None)

        if isinstance(user_id, List):
            user_id = user_id[0]

        if user_id is None:
            logger.debug(
                f'PerunAttributes: missing mandatory field "perun.user" in request.\n'
                f'Hint: Did you configured PerunIdentity filter before this filter?')
            return super().process(context,data)

        if self.attr_map is None:
            logger.debug(
                f'PerunAttributes: attribute map not defined in config file.'
                f'PerunAttributes cannot be loaded.'
            )
            return super().process(context,data)

        attributes = []
        if self.mode == self.MODE_FULL:
            attributes = self.attr_map.keys()
        elif self.mode == self.MODE_PARTIAL:
            for attr_name, attr_value in self.attr_map.items():
                if isinstance(attr_value, list):
                    for val in attr_value:
                        if val in data.attributes.keys():
                            attr = data.attributes.get(val)
                            if not attr:
                                attributes.append(attr_name)
                        else:
                            attributes.append(attr_name)
                else:
                    if attr_value in data.attributes.keys():
                        attr = data.attributes.get(attr_value)
                        if not attr:
                            attributes.append(attr_name)
                    else:
                        attributes.append(attr_name)

        attrs = self.adapter.get_user_attributes_values(user_id, attributes)

        logger.debug('PERUN ATTRS:')
        logger.debug(pprint(attrs))

        for attr_name, attr_value in attrs.items():
            ssp_attr = self.attr_map[attr_name]

            if attr_value is None:
                value = []

            # Boolean also considered as instance of Number
            elif isinstance(attr_value, str) or isinstance(attr_value, Number):
                value = [attr_value]
            elif self.__has_string_keys(attr_value):
                value = attr_value
            elif isinstance(attr_value, Iterable):
                value = attr_value
            else:
                raise Exception(f'sspmod_perun_Auth_Process_PerunAttributes - Unsupported attribute type.\n'
                                f'Attribute name: {attr_name}\n'
                                f'Supported types: None, string, numeric, list and dictionary.')

            if isinstance(ssp_attr, str):
                attr_array = [ssp_attr]
            elif isinstance(ssp_attr, list):
                attr_array = [attr for attr in ssp_attr if attr not in data.attributes.keys()]

            else:
                raise Exception(f'sspmod_perun_Auth_Process_PerunAttributes - Unsupported attribute type.\n'
                                f'Attribute: {attr_name}\n'
                                f'Supported types: string, list')

            logger.debug(f'PerunAttributes: perun attribute "{attr_name}" was fetched.\n'
                         f'Value: "{",".join(str(x) for x in value)}" is being set to ssp attributes "{",".join(attr_array)}"')

            for attribute in attr_array:
                data.attributes[attribute] = value

        logger.debug('PerunAttributes:data END:')
        logger.debug(pprint(data))

        return super().process(context, data)

    @staticmethod
    def __has_string_keys(array_dict):
        if not isinstance(array_dict, Mapping):
            return False

        return len([key for key in array_dict.keys() if isinstance(key, str)]) > 0
