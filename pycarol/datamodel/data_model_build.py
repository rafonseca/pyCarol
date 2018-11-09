from . import data_models


class DataModelBuild:
    """ Automatize the process of building and maintaining a Data Model

        Methods to get, interpret and update information about data model structure, which includes:
            * Data Models
            * Fields
            * Validation Rules
    """

    def __init__(self, carol):
        self.carol = carol
        self.dms = None
        self.dms_id = None
        self.field_functions = None
        self.field_functions_id = None

    def _get_all_dm(self):
        """ Set up data models

            Updates:
                self.dms: Dict with Data Model information, following MDM Model
                self.dms_ds: Dict with {data_model_name:data_model_id} for convenience

        :return: None
        """
        dm = data_models.DataModel(self.carol).get_all()
        self.dms = dm.template_data
        self.dms_id = {d['mdmName']: d['mdmId'] for d in self.dms}

    def get_dm(self, dm_name):
        """ Get a data model by its name

        :param dm_name: Data Model name
        :return: Dict with selected data model information following MDM Model
        """
        if self.dms is None:
            self._get_all_dm()
        for d in self.dms:
            if d['mdmName'] == dm_name:
                return d

    def get_fields(self, dm_name):
        """ Get a fields from a data model by its name

        :param dm_name: Data Model name

        :return: Dict with selected data model fields following MDM Model
        """
        dm = self.get_dm(dm_name)
        return dm['mdmFields']

    def select_field(self, dm_name, field_name):
        """ Get a specific field from a data model

        :param dm_name: Data Model name
        :param field_name: Field name in data model

        :return: Dict with selected data model and field following MDM Model
        """
        fields = self.get_fields(dm_name)
        # TODO: Nested fields
        for f in fields:
            if f['mdmName'] == field_name:
                return f

    def _get_all_field_functions(self):
        """ Set up all possible field functions

            Updates:
                self.field_functions:
                self.field_functions_id:

        :return: None
        """
        get_url = 'v1/fieldFunctions'
        self.field_functions = {f['mdmId']: f for f in self.carol.call_api(get_url, params=dict(pageSize=-1))['hits']}
        self.field_functions_id = {f['mdmName']: f['mdmId'] for f in self.field_functions.values()}

    def get_field_function(self, function_name):
        """ Get a function by its name

        :param function_name: Name of the field function

        :return: Dict of Field Function Id : Field function following MDM Model
        """
        if self.field_functions is None:
            self._get_all_field_functions()
        return self.field_functions[self.field_functions_id[function_name]]

    def filter_rejection_rule_functions(self):
        """ Get only possible rejection rules functions from field functions

        :return: Dict of Field Function Id : Field function following MDM Model
        """
        self.get_all_field_functions()
        # TODO: Get rejection rules from API
        rejection_rules = ['CONTAINS', 'CONTAINS_ARRAY', 'STARTS_WITH', 'ENDS_WITH', 'EQUALS',
                           'MATCHES', 'IS_EMPTY', 'IS_EMAIL', 'LENGTH_COMPARE', 'LENGTH_RANGE',
                           'IS_NOT_NUMBER_ONLY', 'IS_INVALID_BRAZIL_STATE_TAX_ID',
                           'IS_INVALID_BRAZIL_TAX_ID', 'VALUE_COMPARE', 'LOOKUP', 'LOOKUP_MULTIPLE',
                           'LOOKUP_FOUND']
        return {f['mdmId']: f for f in self.field_functions if f['mdmName'] in self.field_functions.values()}

    def get_dm_rule_ids(self, dm_name):
        """ Get data model's validation rules

        :param dm_name: Data model name
        :return:
        """
        dm = self.get_dm(dm_name)
        return dm['mdmEntityValidationRuleIds']

    def get_dm_rule(self, ruleId, templateId):
        """ Get specific rule from datamodel

        :param ruleId: Id of the validation rule
        :param templateId: Id of the template
        :return: Validation Rule following MDM Model
        """
        get_url = f'v1/entities/templates/{templateId}/entityValidationRules/{ruleId}'
        return self.carol.call_api(get_url)

    def create_rule(self, dm_name, field_name, rule_name, params):
        """ Create a rule at Carol
            :param dm_name: data model name
            :param field_name:
            :param rule_name:
            :param params: list with parameters for rule, without the fieldId (will be generated automatically)
        """
        templateId = self.get_dm(dm_name)['mdmId']
        post_url = f'v1/entities/templates/{templateId}/entityValidationRules'
        body = self._generate_rule_body(templateId, dm_name, field_name, rule_name, params)
        rule = self.carol.call_api(post_url, data=body, method='POST')

        post_url = f'v1/entities/templates/{templateId}'
        update_id = {"mdmEntityValidationRuleIds": [[rule['mdmId']]]}
        return self.carol.call_api(post_url, data=update_id, method='PUT')

    def create_rule_from_uniform_type(self, dm_name, field_name, uniform_type):
        return self.create_rule(dm_name, field_name, 'MATCHES', [uniform_type.create_regex()])

    def _generate_rule_body(self, templateId, dm_name, field_name, rule_name, params, state='CREATED'):
        field_func = self.get_field_function(rule_name)
        field_id = self.select_field(dm_name, field_name)['mdmId']

        body = dict(
            mdmEntityTemplateId=templateId,
            mdmFieldFunctionId=field_func['mdmId'],
            mdmFieldId=field_id,
            mdmParameterValues=[f"@@{field_id}"] + params
        )
        return body

    def delete_rule(self, dm_name, rule_id):
        # TODO
        pass

    def update_rule(self, dm_name, rule_id, field_name, params):
        # TODO
        pass

    def add_skip_rule(self, dm_name, field_name, rule):
        # TODO
        pass

    def delete_skip_rule(self, dm_name, field_name, rule):
        # TODO
        pass

    def update_skip_rule(self, dm_name, rule_id, update):
        # TODO
        pass