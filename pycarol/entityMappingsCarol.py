import json
import requests
#from . import utils


class entityMapping:
    def __init__(self, token_object):
        self.dev = token_object.dev
        self.token_object = token_object
        self.snap = {}

        self.headers = self.token_object.headers_to_use

    def getSnapshot(self, connectorId, entityMappingsId, entitySpace, reverseMapping = False):

        self.snap = {}
        querystring = {"entitySpace": entitySpace, "reverseMapping": reverseMapping}

        while True:
            url = "https://{}.carol.ai{}/api/v1/connectors/{}/entityMappings/{}/snapshot".format(self.token_object.domain, self.dev,
                                                                                                 connectorId,
                                                                                                 entityMappingsId)

            self.response = requests.request("GET", url, headers=self.headers, params=querystring)
            if not self.response.ok:
                # error handler for token
                if self.response.reason == 'Unauthorized':
                    self.token_object.refreshToken()
                    self.headers = {'Authorization': self.token_object.access_token, 'Content-Type': 'application/json'}
                    continue
                raise Exception(self.response.text)
            break

        mdmEntityMappingName = self.response.json().get('entityMappingName')
        self.snap.update({mdmEntityMappingName : self.response.json()})


    def updateFromSnapshot(self,snap,entityMappingId,connectorId):
        url_mapping = 'https://{}.carol.ai{}/api/v1/connectors/{}/entityMappings/{}/snapshot'.format(self.token_object.domain, self.dev,
                                                                                                     connectorId,
                                                                                                     entityMappingId)

        while True:
            self.response = requests.request('PUT',url=url_mapping, headers=self.headers, json=snap)
            if not self.response.ok:
                # error handler for token
                if self.response.reason == 'Unauthorized':
                    self.token_object.refreshToken()
                    self.headers = {'Authorization': self.token_object.access_token, 'Content-Type': 'application/json'}
                    continue
                raise Exception(self.response.text)

            break

    def deleteMapping(self,entityMappingId,entitySpace,connectorId):
        url_mapping = 'https://{}.carol.ai{}/api/v1/connectors/{}/entityMappings/{}'.format(self.token_object.domain, self.dev,
                                                                                                     connectorId,
                                                                                                     entityMappingId)

        querystring = {"entitySpace": entitySpace, "reverseMapping": "false"}
        while True:
            self.response = requests.request('DELETE',url=url_mapping, headers=self.headers, params = querystring)
            if not self.response.ok:
                # error handler for token
                if self.response.reason == 'Unauthorized':
                    self.token_object.refreshToken()
                    self.headers = {'Authorization': self.token_object.access_token, 'Content-Type': 'application/json'}
                    continue
                raise Exception(self.response.text)

            break

    def createFromSnapshot(self,snap,connectorId, publish=True, overwrite = False):

        url_mapping = 'https://{}.carol.ai{}/api/v1/connectors/{}/entityMappings/snapshot'.format(self.token_object.domain, self.dev,
                                                                                                  connectorId)
        while True:
            self.response = requests.request('POST',url=url_mapping, headers=self.headers, json=snap)
            if not self.response.ok:
                # error handler for token
                if self.response.reason == 'Unauthorized':
                    self.token_object.refreshToken()
                    self.headers = {'Authorization': self.token_object.access_token, 'Content-Type': 'application/json'}
                    continue
                elif ('Record already exists' in self.response.json()['errorMessage']) and (overwrite):
                    self.getMappingInfo(snap['stagingEntityType'],connectorId)
                    self.deleteMapping(self.entityMappingId,self.entitySpace,connectorId)
                    continue
                raise Exception(self.response.text)

            break
        self.response.encoding = 'utf-8'
        self.response_mapping =  self.response.json()
        entityMappingId = self.response_mapping['mdmEntityMapping']['mdmId']

        if publish:
            self.publishMapping(entityMappingId,connectorId)

    def publishMapping(self, entityMappingId,connectorId):

        url = 'https://{}.carol.ai{}/api/v1/connectors/{}/entityMappings/{}/publish'.format(self.token_object.domain, self.dev,
                                                                                            connectorId,
                                                                                            entityMappingId)

        while True:
            self.response = requests.post(url=url, headers=self.headers)
            if not self.response.ok:
                # error handler for token
                if self.response.reason == 'Unauthorized':
                    self.token_object.refreshToken()
                    self.headers = {'Authorization': self.token_object.access_token, 'Content-Type': 'application/json'}
                    continue
                raise Exception(self.response.text)
            break


    def getMappingInfo(self, stagingType,connectorId):
        url = "https://{}.carol.ai{}/api/v1/connectors/{}/entityMappings".format(self.token_object.domain, self.dev,connectorId)

        querystring = {"reverseMapping": False, "stagingType": stagingType, "pageSize": "-1", "sortOrder": "ASC"}

        while True:
            self.response = requests.request("GET", url, headers=self.headers, params=querystring)
            if not self.response.ok:
                # error handler for token
                if self.response.reason == 'Unauthorized':
                    self.token_object.refreshToken()
                    self.headers = {'Authorization': self.token_object.access_token, 'Content-Type': 'application/json'}
                    continue
                raise Exception(self.response.text)
            break

        self.entityMappingId = self.response.json()['hits'][0]['mdmId']
        self.entitySpace = self.response.json()['hits'][0]['mdmEntitySpace']
