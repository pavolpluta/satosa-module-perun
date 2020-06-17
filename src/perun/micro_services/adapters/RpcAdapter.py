import logging
from pprint import pprint

import yaml
from perun.micro_services.adapters.PerunAdapterAbstract import PerunAdapterAbstract
from perun.micro_services.adapters.RpcConnector import RpcConnector
from perun.micro_services.models.User import User
from perun.micro_services.utils.attribute_utils import AttributeUtils

logger = logging.getLogger(__name__)


class RpcAdapter(PerunAdapterAbstract):

    PERUN_CONFIG_FILE_NAME = 'perun_config_file_name'

    PERUN_RPC_HOSTNAME = 'rpc.hostname'
    PERUN_RPC_USER = 'rpc.user'
    PERUN_RPC_PASSWORD = 'rpc.password'

    connector = None

    def __init__(self, config_file = None):

        if config_file is None:
            config_file = self.PERUN_CONFIG_FILE_NAME

        with open(config_file, "r") as f:
            perun_configuration = yaml.safe_load(f)
            hostname = perun_configuration.get(self.PERUN_RPC_HOSTNAME, None)
            user = perun_configuration.get(self.PERUN_RPC_USER, None)
            pasword = perun_configuration.get(self.PERUN_RPC_PASSWORD, None)

        if None in [hostname, user, pasword]:
            raise Exception('One of required attributes is not defined!')

        self.connector = RpcConnector(hostname, user, pasword)

    def get_perun_user(self, idp_entity_id, uids):
        user = None

        for uid in uids:
            try:
                result = self.connector.post('usersManager', 'getUserByExtSourceNameAndExtLogin', {
                    'extSourceName': idp_entity_id,
                    'extLogin': uid
                })

                name = ''
                for item in ['titleBefore', 'firstName', 'middleName', 'lastName', 'titleAfter']:
                    field = result[item]

                    if field is not None and field.strip():
                        name += field + ' '

                name = name.strip()
                logger.debug("User is found")
                return User(result['id'], name)
            except Exception as ex:
                logger.debug(ex.args)

        logger.debug('User not found')
        return user

    def get_facility_by_identifier(self, identifier):
        pass

    def get_user_groups_on_facility(self, user, facility_id):
        pass

    def get_facility_capabilities(self, facility_id):
        pass

    def get_resource_capabilities(self, facility_id, groups):
        pass

    # TODO test
    def get_user_attributes(self, user_id, attr_names):

        attr_names_map = AttributeUtils.get_rpc_attr_names(attr_names)

        logger.debug("RPC MAP:")
        logger.debug(pprint(attr_names_map))
        logger.debug("RPC MAP KEYS:")
        logger.debug(pprint([*attr_names_map]))

        perun_attrs = self.connector.get('attributesManager', 'getAttributes', {
            'user': user_id,
            'attrNames': [*attr_names_map],
        }
        )

        return self.__get_attributes(perun_attrs,attr_names_map)

    # TODO test
    def get_user_attributes_values(self,user_id, attributes):
        perun_attrs = self.get_user_attributes(user_id,attributes)
        attributes_values = {}

        for perun_attr_name, perun_attr in perun_attrs.items():
            attributes_values[perun_attr_name] = perun_attr['value']

        return attributes_values

    # TODO test
    def __get_attributes(self, perun_attrs,attr_names_map):

        attributes = {}

        for perun_attr in perun_attrs:
            perun_attr_name = perun_attr['namespace'] + ':' + perun_attr['friendlyName']

            attributes[attr_names_map[perun_attr_name]] = {
                'id': perun_attr['id'],
                'name': perun_attr_name,
                'displayName': perun_attr['displayName'],
                'type': perun_attr['type'],
                'value': perun_attr['value']
            }

        return attributes