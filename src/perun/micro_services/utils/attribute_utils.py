from pathlib import Path
from typing import List
import yaml
import logging

logger = logging.getLogger(__name__)


# TODO tests for relevant methods
class AttributeUtils:
    #CONFIG_FILE_NAME = Path('perun/config_templates/perun_attributes_map.yml')
    CONFIG_FILE_NAME = '/etc/satosa/configuration/perun_attributes_map.yaml'
    INTERNAL_ATTR_NAME = 'internalAttrName'

    LDAP = 'ldap'
    RPC = 'rpc'

    TYPE = 'type'
    TYPE_BOOL = 'bool'
    TYPE_MAP = 'map'

    @staticmethod
    def get_config():
        perun_attributes_config = None

        with open(AttributeUtils.CONFIG_FILE_NAME, 'r') as stream:
            try:
                perun_attributes_config = yaml.safe_load(stream)
            except yaml.YAMLError as ex:
                logger.warning(':AttributeUtils: ' + str(ex))

            if perun_attributes_config is None:
                raise Exception('perun:AttributeUtils: invalid perun_attributes_map.yml config file')

        return perun_attributes_config

    @staticmethod
    def get_attr_name(internal_attr_name: str, interface: str):
        perun_attributes_config = AttributeUtils.get_config()
        result_attr_name = None

        try:
            attr_array = perun_attributes_config.get(internal_attr_name)

            if interface in attr_array:
                result_attr_name = attr_array[interface]

            if result_attr_name is None:
                logger.warning(
                    f'perun:AttributeUtils: interface "{interface}" does not exist for attribute '
                    f'"{internal_attr_name}"')

        except TypeError:
            logger.warning(
                f'perun:AttributeUtils: missing "{internal_attr_name}" attribute in perun_attributes_map.yml file')

        return result_attr_name

    @staticmethod
    def create_attr_type_map(internal_attr_names: List[str], interface: str):
        perun_attributes_config = AttributeUtils.get_config()
        result_map = {}

        for internal_attr_name in internal_attr_names:
            try:
                attr_array = perun_attributes_config.get(internal_attr_name)

                if interface in attr_array:
                    result_map[attr_array[interface]] = {
                        AttributeUtils.INTERNAL_ATTR_NAME: internal_attr_name,
                        AttributeUtils.TYPE: attr_array[AttributeUtils.TYPE]
                    }
                else:
                    logger.warning(f'perun:AttributeUtils: interface "{interface}" does not exist for attribute '
                                   f'"{internal_attr_name}"')
            except TypeError:
                logger.warning(f'perun:AttributeUtils: missing {internal_attr_name} atrribute in '
                               f'perun_attributes_map.yml file')

        return result_map

    @staticmethod
    def get_attr_names(internal_attr_names: List[str], interface: str):
        perun_attributes_config = AttributeUtils.get_config()
        result_map = {}

        for internal_attr_name in internal_attr_names:
            try:
                attr_array = perun_attributes_config.get(internal_attr_name)

                if interface in attr_array:
                    result_map[attr_array[interface]] = internal_attr_name

                else:
                    logger.warning(f'perun:AttributeUtils: interface "{interface}" does not exist for attribute '
                                   f'"{internal_attr_name}"')

            except TypeError:
                logger.warning(f'perun:AttributeUtils: missing "{internal_attr_name}" attribute '
                               f'in perun_attributes_map.yml file')

        return result_map

    @staticmethod
    def get_ldap_attr_name(internal_attr_name: str):
        return AttributeUtils.get_attr_name(internal_attr_name, AttributeUtils.LDAP)

    @staticmethod
    def get_rpc_attr_name(internal_attr_name: str):
        return AttributeUtils.get_attr_name(internal_attr_name, AttributeUtils.RPC)

    @staticmethod
    def create_ldap_attr_name_type_map(internal_attr_names: List[str]):
        return AttributeUtils.create_attr_type_map(internal_attr_names, AttributeUtils.LDAP)

    @staticmethod
    def create_rpc_attr_name_type_map(internal_attr_names: List[str]):
        return AttributeUtils.create_attr_type_map(internal_attr_names, AttributeUtils.RPC)

    @staticmethod
    def get_ldap_attr_names(internal_attr_names: List[str]):
        return AttributeUtils.get_attr_names(internal_attr_names, AttributeUtils.LDAP)

    @staticmethod
    def get_rpc_attr_names(internal_attr_names: List[str]):
        return AttributeUtils.get_attr_names(internal_attr_names, AttributeUtils.RPC)

    @staticmethod
    def set_attr_value(attrs_name_type_map, attrs_from_ldap, attr):
        if (attr not in attrs_from_ldap) and (
                attrs_name_type_map[attr][AttributeUtils.TYPE] == AttributeUtils.TYPE_BOOL):
            return False
        elif (attr not in attrs_from_ldap) and (
                attrs_name_type_map[attr][AttributeUtils.TYPE] == AttributeUtils.TYPE_MAP):
            return {}
        elif (attr in attrs_from_ldap) and (attrs_name_type_map[attr][AttributeUtils.TYPE] == AttributeUtils.TYPE_MAP):
            return attrs_from_ldap[attr]
        elif attr in attrs_from_ldap:
            return attrs_from_ldap[attr][0]
        else:
            return None