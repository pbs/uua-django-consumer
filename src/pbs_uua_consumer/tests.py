from django.test import TestCase
from django.test.client import Client
from django.http import Http404
from pbs_uua_consumer import models
from django.contrib.auth.models import User, Group
from openid.consumer.consumer import SUCCESS
from django.conf import settings

class GenericTestCase(TestCase):
    fixtures = ['test_taxonomy.json',
                'test_stations.json',
                'test_programs.json',
                'test_users.json',
                'test_users_openid.json',]
    
    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        
        from merlin import settings
        reload(settings)
        from merlin.config import base
        reload(base)
        from merlin.config import testing
        reload(testing)
        from merlin.apps.core import models
        reload(models)
        from pbs_uua_consumer import models
        reload(models)
        
        from pbs_uua_consumer.auth import OpenIDBackend
        self.backend = OpenIDBackend()
        
    
    def test_get_user(self):
        user = self.backend.get_user(-1)
        self.failUnlessEqual(user, None)
        
        user = self.backend.get_user(2)
        self.failUnlessEqual(user.username, "admin")
    
    def test_authenticate_fail(self, openid_response = None):
        try:
            user = self.backend.authenticate()
            self.failUnlessEqual(user, None)
        except:
            pass
        
        
    #Test for OK authentication without:
        #- creating from sreg
        #- updating from sreg
    #Those two will be tested individually
    def make_mock():
        class Mock(object): pass
        x = Mock()
        x.status = SUCCESS
        x.identity_url = "http://192.168.1.121:8081/u/BdwAEHKnlO_W3zOWh0TMcQ"
        return x

    def test_authenticate_ok(self, openid_response = make_mock()):
        user = self.backend.authenticate()
        

    
    
    
    
