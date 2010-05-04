from django.test import TestCase
from django.test.client import Client
from django.http import Http404
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.contrib.auth.models import User
from openid import message
from openid.consumer.consumer import SUCCESS, SuccessResponse, FailureResponse
from openid.consumer.discover import OpenIDServiceEndpoint
from pbs_uua_consumer.extensions import SignatureVerification, UIExtension
from openid.extensions.sreg import SRegResponse, SRegRequest
from pbs_uua_consumer.auth import OpenIDBackend
import models
from openid.message import registerNamespaceAlias

class MockOpenIDSuccessResponse(SuccessResponse):
    def __init__(self, status, identity_url):
        self.status = status
        self.identity_url = identity_url
        self.message = message.Message()

        sig_ext = SignatureVerification(consumer_key='CKEY',
                                        secret_key='SKEY',
                                        request_token='token',
                                        hmac=None,
                                        timestamp=None)
        sig_ext.toMessage(self.message)

        sreg_ext = SRegRequest(required = ['nickname','email'],
                               optional = ['fullname'],
                               policy_url = None,
                               sreg_ns_uri = 'http://openid.net/extensions/sreg/1.1')
        sreg_ext.toMessage(self.message)
        self.signed_fields = ['openid.sreg.nickname', 'openid.sreg.email',
                              'openid.sreg.required', 'openid.sreg.optional',
                              'openid.sreg.fullname']



        self.endpoint = OpenIDServiceEndpoint()
        self.endpoint.claimed_id=identity_url

    def addSRegValid(self):
        self.message.setArg('http://openid.net/extensions/sreg/1.1', 'nickname', 'MyNickname')
        self.message.setArg('http://openid.net/extensions/sreg/1.1', 'email', 'user@domain.com')
        self.message.setArg('http://openid.net/extensions/sreg/1.1', 'fullname', 'Full Name')

    def extensionResponse(self, *args):
        return {}

class MockOpenIdFailureResponse(FailureResponse):
    pass

class GenericTestCase(TestCase):
    fixtures = ['test_taxonomy.json',
                'test_stations.json',
                'test_programs.json',
                'test_users.json',
                'test_users_openid.json',]

    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        self.backend = OpenIDBackend()

    def test_get_user(self):
        user = self.backend.get_user(-1)
        self.failUnlessEqual(user, None)

        user = self.backend.get_user(2)
        self.failUnlessEqual(user.username, "admin")

    def test_authenticate_fail(self):
        try:
            user = self.backend.authenticate(openid_response=None)
            self.failUnlessEqual(user, None)
        except:
            pass

    def test_create_user_from_openid_with_sreg(self):
        openid_response = MockOpenIDSuccessResponse(SUCCESS, 'http://192.168.1.121:8081/u/some_identity')
        openid_response.addSRegValid()
        user = self.backend.authenticate(openid_response=openid_response)
        self.failUnlessEqual(user.username, 'MyNickname')

    def test_create_user_from_openid(self):
        openid_response = MockOpenIDSuccessResponse(SUCCESS, 'http://192.168.1.121:8081/u/some_identity')
        user = self.backend.authenticate(openid_response=openid_response)
        self.failUnlessEqual(user.username, 'openiduser')

    def test_openid_request_failure_response(self):
        openid_response = MockOpenIdFailureResponse(endpoint=OpenIDServiceEndpoint())
        user = self.backend.authenticate(openid_response=openid_response)
        self.failUnlessEqual(user,None)

class ModelsTests(TestCase):
    def test_delete_user(self):
        # Create a user and an OpenID user associated
        user1 = User.objects.create(username="test1")
        user2 = User.objects.create(username="test2")
        openiduser = models.UserOpenID.objects.create(
            user=user1,
            claimed_id="http://192.168.1.121:8081/u/BdwAEHKnlO_W3zOWh0TMcQ",
            display_id="http://192.168.1.121:8081/u/BdwAEHKnlO_W3zOWh0TMcQ"
        )

        # Delete the user and check if the OpenID user is deleted
        user1.delete()
        self.assertRaises(
            models.UserOpenID.DoesNotExist,
            lambda: models.UserOpenID.objects.get(pk=openiduser.pk))

        # Delete the second user. It must be done gracefully.
        user2.delete()
