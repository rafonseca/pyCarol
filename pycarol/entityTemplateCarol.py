import requests
import json
from .entityTemplateTypesCarol import *
from .verticalsCarol import *
from .fieldsCarol import *


class entIntType(object):
    ent_type = 'long'


class entDoubleType(object):
    ent_type = 'double'


class entStringType(object):
    ent_type = "string"


class entNullType(object):
    ent_type = "string"


class entBooleanType(object):
    ent_type = "boolean"


class entArrayType(object):
    ent_type = "nested"


class entObjectType(object):
    ent_type = "object"


class entType(object):
    @classmethod
    def get_ent_type_for(cls, t):
        """docstring for get_schema_type_for"""
        SCHEMA_TYPES = {
            type(None): entNullType,
            str: entStringType,
            int: entIntType,
            float: entDoubleType,
            bool: entBooleanType,
            list: entArrayType,
            dict: entObjectType,
        }

        schema_type = SCHEMA_TYPES.get(t)

        if not schema_type:
            raise JsonEntTypeNotFound("There is no schema type for  %s.\n Try:\n %s" % (
            str(t), ",\n".join(["\t%s" % str(k) for k in SCHEMA_TYPES.keys()])))
        return schema_type


class JsonEntTypeNotFound(Exception):
    pass


class entityTemplate(object):
    def __init__(self, token_object):
        self.token_object = token_object
        if self.token_object.access_token is None:
            self.token_object.newToken()

        self.headers = {'Authorization': self.token_object.access_token, 'Content-Type': 'application/json'}

    def _get(self,id, by = 'id'):
        not_found = False
        while True:
            if by == 'name':
                url = "https://{}.carol.ai/api/v1/entities/templates/name/{}".format(self.token_object.domain,id)
            elif by == 'id':
                url = "https://{}.carol.ai/api/v1/entities/templates/{}/working".format(self.token_object.domain,id)
            else:
                raise print('Type incorrect')
            self.lastResponse = requests.request("GET", url, headers=self.headers)
            if not self.lastResponse.ok:
                # error handler for token
                if self.lastResponse.reason == 'Unauthorized':
                    self.token_object.refreshToken()
                    self.headers = {'Authorization': self.token_object.access_token,
                                    'Content-Type': 'application/json'}
                    continue
                elif self.lastResponse.reason == 'Not Found':
                    not_found = True
                    print('Template not found')
                    self.entityTemplate_ = {}
                    break
                raise Exception(self.lastResponse.reason)
            break
        if not_found:
            self.entityTemplate_ = {}
        else:
            self.lastResponse.encoding = 'utf8'
            resp = json.loads(self.lastResponse.text)
            self.entityTemplate_ = {resp['mdmName'] : resp}

    def getByName(self,entityTemplateName):
        self._get(entityTemplateName, by = 'name')

    def getById(self,entityTemplateId):
        self._get(entityTemplateId, by='id')


class createTemplate(object):
    def __init__(self, token_object):
        self.token_object = token_object
        if self.token_object.access_token is None:
            self.token_object.newToken()

        self.headers = {'Authorization': self.token_object.access_token, 'Content-Type': 'application/json'}
        self.template_dict = {}

        self.fields = fieldsCarol(self.token_object)
        self.fields.possibleTypes()
        self.all_possible_types = self.fields._possibleTypes
        self.all_possible_fields = self.fields.fields_dict

    def _checkVerticals(self):
        self.verticalsNameIdsDict = verticals(self.token_object).getAll()

        if self.mdmVerticalIds is not None:
            for key, value in self.verticalsNameIdsDict.items():
                if value == self.mdmVerticalIds:
                    self.mdmVerticalIds = value
                    self.mdmVerticalNames = key
                    return
        else:
            for key, value in self.verticalsNameIdsDict.items():
                if key == self.mdmVerticalNames:
                    self.mdmVerticalIds = value
                    self.mdmVerticalNames = key
                    return

        raise Exception('{}/{} are not valid values for mdmVerticalNames/mdmVerticalIds./n'
                        ' Possible values are: {}'.format(self.mdmVerticalNames, self.mdmVerticalIds,
                                                          self.verticalsNameIdsDict))

    def _checkEntityTemplateTypes(self):
        self.entityTemplateTypesDict = entityTemplateTypeIds(self.token_object).getAll()

        if self.mdmEntityTemplateTypeIds is not None:
            for key, value in self.entityTemplateTypesDict.items():
                if value == self.mdmEntityTemplateTypeIds:
                    self.mdmEntityTemplateTypeIds = value
                    self.mdmEntityTemplateTypeNames = key
                    return
        else:
            for key, value in self.entityTemplateTypesDict.items():
                if key == self.mdmEntityTemplateTypeNames:
                    self.mdmEntityTemplateTypeIds = value
                    self.mdmEntityTemplateTypeNames = key
                    return

        raise Exception('{}/{} are not valid values for mdmEntityTemplateTypeNames/mdmEntityTemplateTypeIds./n'
                        ' Possible values are: {}'.format(self.mdmVerticalNames, self.mdmVerticalIds,
                                                          self.entityTemplateTypesDict))

    def _checkEntityTemplateName(self):

        est_ = entityTemplate(self.token_object)
        est_.getByName(self.mdmName)
        if not est_.entityTemplate_ == {}:
            raise Exception('mdm name {} already exist'.format(self.mdmName))

    def create(self, mdmName, mdmVerticalIds=None, mdmVerticalNames=None, mdmEntityTemplateTypeIds=None,
               mdmEntityTemplateTypeNames=None, mdmLabel=None, mdmGroupName='Others',
               mdmTransactionDataModel=False):

        self.mdmName = mdmName
        self.mdmGroupName = mdmGroupName

        if not mdmLabel:
            self.mdmLabel = self.mdmName
        else:
            self.mdmLabel = mdmLabel


        self.mdmTransactionDataModel = mdmTransactionDataModel

        assert ((mdmVerticalNames is not None) or (mdmVerticalIds is not None))
        assert ((mdmEntityTemplateTypeIds is not None) or (mdmEntityTemplateTypeNames is not None))

        self.mdmVerticalNames = mdmVerticalNames
        self.mdmVerticalIds = mdmVerticalIds
        self.mdmEntityTemplateTypeIds = mdmEntityTemplateTypeIds
        self.mdmEntityTemplateTypeNames = mdmEntityTemplateTypeNames

        self._checkVerticals()
        self._checkEntityTemplateTypes()
        self._checkEntityTemplateName()

        payload = {"mdmName": self.mdmName, "mdmGroupName": self.mdmGroupName, "mdmLabel": {"en-US": self.mdmLabel},
                   "mdmVerticalIds": [self.mdmVerticalIds],
                   "mdmEntityTemplateTypeIds": [self.mdmEntityTemplateTypeIds],
                   "mdmTransactionDataModel": self.mdmTransactionDataModel, "mdmProfileTitleFields": []}

        while True:
            url_filter = "https://{}.carol.ai/api/v1/entities/templates".format(self.token_object.domain)
            self.lastResponse = requests.get(url=url_filter, headers=self.headers, json = payload)
            if not self.lastResponse.ok:
                # error handler for token
                if self.lastResponse.reason == 'Unauthorized':
                    self.token_object.refreshToken()
                    self.headers = {'Authorization': self.token_object.access_token,
                                    'Content-Type': 'application/json'}
                    continue
                raise Exception(self.lastResponse.text)
            break

        self.lastResponse.encoding = 'utf8'
        response = [json.loads(self.lastResponse.text)]
        self.template_dict.update({response['mdmName']: response})


    def addField(self,fieldName, entityTemplateId = None,parentFieldId = ""):

        if entityTemplateId is None:
            assert self.entityTemplateId
        else:
            est_ = entityTemplate(self.token_object)
            est_.getById(entityTemplateId)
            if est_.entityTemplate_ == {}:
                print('Template does not exisit')
                return
            self.entityTemplateId = entityTemplateId
            _ , template_ = est_.entityTemplate_.popitem()
            self.current_fields = [i for i in template_['mdmFieldsFull'].keys()]
            if fieldName.lower() in self.current_fields:
                print("'{}' already in the template".format(fieldName))
                return

        field_to_send = self.all_possible_fields.get(fieldName,[])
        if field_to_send == []:
            print('Field does not exist')
            return
        querystring = {"parentFieldId": parentFieldId}
        while True:
            url = "https://{}.carol.ai/api/v1/entities/templates/{}/onboardField/{}".format(self.token_object.domain,
                                                                                            self.entityTemplateId, field_to_send['mdmId'])
            response = requests.request("POST", url, headers=self.headers, params=querystring)
            if not response.ok:
                # error handler for token
                if response.reason == 'Unauthorized':
                    self.token_object.refreshToken()
                    self.headers = {'Authorization': self.token_object.access_token,
                                    'Content-Type': 'application/json'}
                    continue
                raise Exception(response.text)
            break

    def _labelsAndDesc(self,prop):

        if self.mdmLabelMap is None:
            label = prop
        else:
            label = self.mdmLabelMap.get(prop,[])
            if label == []:
                label = prop
            else:
                label = {"en-US": label}

        if self.mdmDescriptionMap is None:
            description = prop
        else:
            description = self.mdmDescriptionMap.get(prop,[])
            if description == []:
                description = prop
            else:
                description = {"en-US": description}

        return label,  description



    def from_json(self,json_sample, entityTemplateId = None, mdmLabelMap = None, mdmDescriptionMap = None ):

        self.mdmLabelMap = mdmLabelMap
        self.mdmDescriptionMap = mdmDescriptionMap

        if entityTemplateId is None:
            assert self.template_dict != {}
            templateName , templateJson = self.template_dict.copy().popitem()
            self.entityTemplateId = templateJson['mdmId']

        else:
            self.entityTemplateId = entityTemplateId

        self.json_sample = json_sample

        for prop, value in self.json_sample.items():
            prop = prop.lower()
            entity_type = entType.get_ent_type_for(type(value))
            if prop in self.all_possible_fields.keys():
                if not entity_type.ent_type == 'nested':
                    ent_ = self.all_possible_fields.get(prop, []).copy()
                    ent_.pop('mdmCreated')
                    ent_.pop('mdmLastUpdated')
                    ent_.pop('mdmTenantId')
                    if (ent_['mdmMappingDataType'].lower() == entity_type.ent_type):
                        self.addField(prop, parentFieldId="")
                    else:
                        print('problem, {} not created, field name matches with an already'
                              'created field but different type'.format(prop))
                else:
                    print('Nested fields are not supported')
            else:
                if not entity_type.ent_type == 'nested':

                    currentLabel, currentDescription = self._labelsAndDesc(prop)
                    self.fields.create(mdmName = prop, mdmMappingDataType = entity_type.ent_type, mdmFieldType= 'PRIMITIVE',
                                       mdmLabel = currentLabel, mdmDescription = currentDescription)
                    self.all_possible_fields = self.fields.fields_dict
                    self.addField(prop, parentFieldId="")
                else:
                    print('Nested fields are not supported')

                #to_create = create_field(prop, value)
                #print(to_create)

    def _nested(self,mdmName, value, parentId=''):
        payload = {"mdmName": mdmName, "mdmMappingDataType": entity_type.ent_type,
                   "mdmLabel": {"en-US": mdmName}, "mdmDescription": {"en-US": mdmName}}
        entity_type = entType.get_ent_type_for(type(value))

        if entity_type == entObjectType and len(value) > 0:
            for key, val in value.items():
                payload['mdmFieldType'] = 'NESTED'
                print('criando NESTED')
                parentId = 1234
                create_field(key, val, parentId=parentId)

        elif entity_type == entArrayType and len(value) > 0:
            pass

        if entity_type.ent_type == 'nested':

            payload['mdmFieldType'] = 'NESTED'
            print('criando NESTED')
            parentId = 1234
            _, parentId = create_field()
        else:
            payload['mdmFieldType'] = 'PRIMITIVE'
            print('criando PRIMITIVE')

        return payload, parentId





"""
##############
############################
############################
############################
##############

#To add fields, firts need to cread the field.  (OBS. there are a lot of pre created fields to be used.)

url = "https://mario.carol.ai/api/v1/fields"

payload = {"mdmName":"nome","mdmMappingDataType":"string","mdmFieldType":"PRIMITIVE","mdmLabel":{"en-US":"Nome"},"mdmDescription":{"en-US":"Nome"}}
headers = {
    'authorization': "2561c210b11611e78cce0242ac110003",
    'content-type': "application/json;charset=UTF-8",
    'accept': "application/json, text/plain, */*",
    }

response = requests.request("POST", url, json=payload, headers=headers)


#response:
''' 
{"mdmName":"nome","mdmLabel":{"en-US":"Nome"},"mdmDescription":{"en-US":"Nome"},"mdmIndex":"ANALYZED","mdmAnalyzer":"STANDARD",
 "mdmMappingDataType":"STRING","mdmFields":[],"mdmForeignKeyField":false,"mdmFieldsFull":{},"mdmFieldType":"PRIMITIVE","mdmTags":[],
 "mdmId":"73792f30b11911e78cce0242ac110003","mdmEntityType":"mdmField","mdmCreated":"2017-10-14T19:54:12Z",
 "mdmLastUpdated":"2017-10-14T19:54:12Z","mdmTenantId":"8d45c660a85b11e7a2900242ac110003"}
'''


#a nested field

import requests

url = "https://mario.carol.ai/api/v1/fields"

payload = {"mdmName":"nestedtest","mdmMappingDataType":"nested","mdmFieldType":"NESTED",
           "mdmLabel":{"en-US":"nested test"},"mdmDescription":{"en-US":"nested"}}
headers = {
    'authorization': "2561c210b11611e78cce0242ac110003",
    'content-type': "application/json;charset=UTF-8"
    }

response = requests.request("POST", url, data=payload, headers=headers)


#response:
''' 
{"mdmName":"nestedtest","mdmLabel":{"en-US":"nested test"},"mdmDescription":{"en-US":"nested"},
 "mdmIndex":"ANALYZED","mdmAnalyzer":"STANDARD","mdmMappingDataType":"NESTED","mdmFields":[],
 "mdmForeignKeyField":false,"mdmFieldsFull":{},"mdmFieldType":"NESTED","mdmTags":[],"mdmId":"5abfc4c0b11b11e78cce0242ac110003",
 "mdmEntityType":"mdmField","mdmCreated":"2017-10-14T20:07:50Z","mdmLastUpdated":"2017-10-14T20:07:50Z",
 "mdmTenantId":"8d45c660a85b11e7a2900242ac110003"}
'''





#Then to add a field to a DM


url = "https://mario.carol.ai/api/v1/entities/templates/4d7e5010b11611e78cce0242ac110003/onboardField/73792f30b11911e78cce0242ac110003"

querystring = {"parentFieldId":""}

headers = {
    'authorization': "2561c210b11611e78cce0242ac110003",
    'accept': "application/json, text/plain, */*"
    }

response = requests.request("POST", url, headers=headers, params=querystring)

#Then to add nested a field to a DM

import requests

url = "https://mario.carol.ai/api/v1/entities/templates/4d7e5010b11611e78cce0242ac110003/onboardField/5abfc4c0b11b11e78cce0242ac110003"

querystring = {"parentFieldId":""}

headers = {
    'accept-language': "en-US,en;q=0.8,pt-BR;q=0.6,pt;q=0.4",
    'authorization': "2561c210b11611e78cce0242ac110003",
    }

response = requests.request("POST", url, headers=headers, params=querystring)



# to add a chield to the nest field to a DM

url = "https://mario.carol.ai/api/v1/entities/templates/4d7e5010b11611e78cce0242ac110003/onboardField/fcc94630b07911e793370242ac110003"

querystring = {"parentFieldId":"5abfc4c0b11b11e78cce0242ac110003"}

headers = {

    'accept-language': "en-US,en;q=0.8,pt-BR;q=0.6,pt;q=0.4",
    'authorization': "2561c210b11611e78cce0242ac110003"
    }

response = requests.request("POST", url, headers=headers, params=querystring)

print(response.text)


#Add profile title

import requests

url = "https://mario.carol.ai/api/v1/entities/templates/4d7e5010b11611e78cce0242ac110003/profileTitle"

payload = ["mdmtaxid"]  #list of fields
headers = {
    'accept-language': "en-US,en;q=0.8,pt-BR;q=0.6,pt;q=0.4",
    'authorization': "2561c210b11611e78cce0242ac110003"
    }

response = requests.request("POST", url, data=payload, headers=headers)

"""