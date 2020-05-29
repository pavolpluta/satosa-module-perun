"""
Satosa micro_service : Perun Identity
"""

__author__ = "Pavel Vyskocil"
__email__ = "Pavel.Vyskocil@cesnet.cz"

import logging

from perun.micro_services.adapters.PerunAdapter import PerunAdapter
from perun.micro_services.adapters.PerunAdapterAbstract import PerunAdapterAbstract
from satosa.micro_services.base import ResponseMicroService

logger = logging.getLogger(__name__)


class PerunIdentity(ResponseMicroService):
    INTERFACE = 'interface'
    UIDS_IDENTIFIERS = 'uids_identifiers'
    PERUN_CONFIG_FILE_NAME = 'perun_config_file_name'

    logprefix = "PerunIdentity:"

    def __init__(self, config, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.config = config

        self.uids_identifiers = config.get(self.UIDS_IDENTIFIERS, [])
        confif_file_name = config.get(self.PERUN_CONFIG_FILE_NAME, None)

        if confif_file_name is None:
            raise Exception(f'PerunIdentity: Required option "{self.PERUN_CONFIG_FILE_NAME}" not defined.')

        interface = str.lower(config.get(self.INTERFACE))
        self.adapter: PerunAdapterAbstract = PerunAdapter.get_instance(confif_file_name, interface)

    def process(self, context, data):
        """
        Finds Perun user and store perunUserId into data.attributes
        """
        idp_entity_id = data.auth_info['issuer']
        attributes = data.attributes

        uids = []

        for identifier in self.uids_identifiers:
            if identifier in attributes.keys():
                uid = attributes[identifier][0]
                uids.append(uid)

        user = self.adapter.get_perun_user(idp_entity_id, uids)

        logger.debug(f'User: {user} found')
        if user is not None:
            attributes.update({'perun_id': [user.id]})
            data.attributes = attributes

        return super().process(context, data)
