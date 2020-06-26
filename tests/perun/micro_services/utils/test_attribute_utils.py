import mock
import pytest

from perun.micro_services.utils.attribute_utils import AttributeUtils


class TestAttributeUtils:
    TEST_CONF_FILE_NAME = '/tests/perun/micro_services/configurations/perun_config_test.yml'
    TEST_MAP_FILE_LOCATION = 'tests/perun/micro_services/configurations/perun_test_attributes_map.yaml'

    TEST_ATTR_NAME_TYPE_MAP = {
        'attr1': {'internalAttrName': 'internal_test_attribute_1',
                  'type': 'bool'},
        'attr2': {'internalAttrName': 'internal_test_attribute_2',
                  'type': 'integer'},
        'attr3': {'internalAttrName': 'internal_test_attribute_3',
                  'type': 'string'},
        'attr4': {'internalAttrName': 'internal_test_attribute_4',
                  'type': 'list'},
        'emptyBool': {'internalAttrName': 'empty_bool_attr',
                      'type': 'bool'},
        'emptyList': {'internalAttrName': 'empty_list_attr',
                      'type': 'list'},
        'emptyString': {'internalAttrName': 'empty_string_attr',
                        'type': 'string'},
        'emptyInt': {'internalAttrName': 'empty_int_attr',
                     'type': 'integer'}
    }

    TEST_ATTRS_FROM_LDAP_CONNECTOR = {
        'attr1': [True],
        'attr2': [2],
        'attr3': ['Value 3'],
        'attr4': ['Value 4', 'Value 5', 'Value 6'],
    }

    @pytest.fixture
    def attr_utils(self):
        return AttributeUtils(self.TEST_MAP_FILE_LOCATION)

    def test_load_config(self, attr_utils):
        assert isinstance(attr_utils, AttributeUtils)
        assert attr_utils.perun_attributes_config.get('internal_test_attribute_1') is not None

    def test_load_invalid_config(self):
        with pytest.raises(FileNotFoundError):
            AttributeUtils('invalid.yaml')

    def test_get_attr_names(self, attr_utils):
        res = attr_utils.get_attr_names(['internal_test_attribute_1', 'internal_test_attribute_2'], 'ldap')
        assert len(res.keys()) == 2 and 'attr1' in res.keys() and 'attr2' in res.keys()

        res = attr_utils.get_attr_names(['internal_test_attribute_1', 'internal_test_attribute_2'], 'rpc')
        assert len(res.keys()) == 2 and 'test:urn:attr:1' in res.keys() and 'test:urn:attr:2' in res.keys()

        res = attr_utils.get_attr_names(['internal_test_attribute_1'], 'ldap')
        assert len(res.keys()) == 1 and 'attr1' in res.keys()

        res = attr_utils.get_attr_names(['internal_test_attribute_1', 'invalid'], 'ldap')
        assert len(res.keys()) == 1 and 'attr1' in res.keys()

        res = attr_utils.get_attr_names(['internal_test_attribute_1', 'invalid'], 'rpc')
        assert len(res.keys()) == 1 and 'test:urn:attr:1' in res.keys()

    def test_get_attr_names_invalid(self, attr_utils):
        res = attr_utils.get_attr_names(['invalid_attr'], 'rpc')
        assert res == {}

        res = attr_utils.get_attr_names([], 'rpc')
        assert res == {}

        res = attr_utils.get_attr_names(['internal_test_attribute_1'], 'invalid')
        assert res == {}

        res = attr_utils.get_attr_names(['internal_test_attribute_1'], '')
        assert res == {}

        res = attr_utils.get_attr_names([], '')
        assert res == {}

    def test_get_attr_name(self, attr_utils):
        res = attr_utils.get_attr_name('internal_test_attribute_3', 'rpc')
        assert res == 'test:urn:attr:3'

        res = attr_utils.get_attr_name('internal_test_attribute_3', 'ldap')
        assert res == 'attr3'

    def test_get_attr_name_invalid(self, attr_utils):
        res = attr_utils.get_attr_name('invalid', 'rpc')
        assert res is None

        res = attr_utils.get_attr_name('internal_test_attribute_3', 'invalid')
        assert res is None

        res = attr_utils.get_attr_name('', 'rpc')
        assert res is None

        res = attr_utils.get_attr_name('', '')
        assert res is None

    def test_create_attr_type_map(self, attr_utils):
        res = attr_utils.create_attr_type_map(['internal_test_attribute_1', 'internal_test_attribute_3'], 'rpc')
        assert 'test:urn:attr:1' in res.keys() and 'test:urn:attr:3' in res.keys()
        assert res['test:urn:attr:1']['internalAttrName'] == 'internal_test_attribute_1'
        assert res['test:urn:attr:1']['type'] == 'bool' and res['test:urn:attr:3']['type'] == 'string'

        res = attr_utils.create_attr_type_map(['internal_test_attribute_1', 'internal_test_attribute_3'], 'ldap')
        assert 'attr1' in res.keys() and 'attr3' in res.keys()

    def test_set_internal_attr_value(self, attr_utils):
        res = {}

        for attr_name in self.TEST_ATTR_NAME_TYPE_MAP.keys():
            res[self.TEST_ATTR_NAME_TYPE_MAP[attr_name]['internalAttrName']] = \
                attr_utils.set_internal_attr_value(self.TEST_ATTR_NAME_TYPE_MAP, self.TEST_ATTRS_FROM_LDAP_CONNECTOR,
                                                   attr_name)

        assert isinstance(res['internal_test_attribute_1'], bool)
        assert isinstance(res['internal_test_attribute_2'], int)
        assert isinstance(res['internal_test_attribute_3'], str)
        assert isinstance(res['internal_test_attribute_4'], list)
        assert isinstance(res['empty_bool_attr'], bool)
        assert isinstance(res['empty_list_attr'], list)
        assert res['empty_string_attr'] is None
        assert res['empty_int_attr'] is None

