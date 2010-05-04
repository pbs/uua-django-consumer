from django.test import TestCase
from django.test.client import Client
from django.http import Http404
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.contrib.auth.models import User
from openid import message
from openid.consumer.consumer import SUCCESS

from pbs_uua_consumer.auth import OpenIDBackend
import models


class GenericTestCase(TestCase):
    fixtures = ['test_taxonomy.json',
                'test_stations.json',
                'test_programs.json',
                'test_users.json',
                'test_users_openid.json',]

    def make_mock(self):
        class Mock(object):
            def __init__(self):
                pass
            def getSignedNS(self):
                return "http://openid.net/extensions/sreg/1.1"

        x = Mock()
        x.message = message.Message()
        x.status = SUCCESS
        x.identity_url = "http://192.168.1.121:8081/u/BdwAEHKnlO_W3zOWh0TMcQ"
        x.sreg.fullname='First Last'
        x.sreg.nickname='User1234'
        x.sreg.email='user@testemail.org'
        return x

    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        self.backend = OpenIDBackend()
        self.mock = self.make_mock();


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

    def test_create_user_from_openid(self):
        openid_response = self.mock
        OpenIDBackend.authenticate(openid_response=openid_response)

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


